import json
import re
import ollama
from typing import Any, Optional
from src.util.respository.dbUtil import db_manager as db
from src.util.BaseToolSelector import BaseToolSelector
from src.util.entity.ToolMeta import ToolMeta
from src.util.respository.ToolRespository import get_tool_repository
from typing import Any, Optional, List



class DefaultToolSelector(BaseToolSelector):
    def __init__(self):
        super().__init__(
            max_retries=2,
            retry_sleep=0.3,
            default_tool_ids=[2],
        )
        self.model_name = "qwen2.5-fixed"

    # ========================
    # 规则（当前禁用）
    # ========================
    def rule_route(self, input: dict) -> Optional[List[int]]:
        return None

    # ========================
    # Prompt
    # ========================
    def build_prompt(self, input: dict) -> str:
        question = str(input.get("question", "")).strip()
        tools: List[ToolMeta] = get_tool_repository().get_tools_by_categories(input.get("category", []))
        


        tool_text = "\n".join(
            f"{t.id}: {t.name}，作用：{t.description}"
            for t in tools if t.enabled
        )

        return f"""你是工具选择助手。
只返回 JSON 数组（工具 id）。请选择你认为回答这个问题需要选取的工具。

工具：
{tool_text}

问题：{question}
输出：
"""

    def build_retry_prompt(self, input: dict) -> str:
        """
        retry prompt 可以直接复用 build_prompt，只是加上提示要求严格返回 JSON。
        """
        base_prompt = self.build_prompt(input)

        retry_hint = (
            "注意：请严格按照 JSON 数组格式返回工具 id，例如 [1] 或 [1,2]，"
            "不要返回文字描述或其他内容。\n"
        )

        return retry_hint + base_prompt

    # ========================
    # 模型调用
    # ========================
    def call_model(self, prompt: str) -> str:
        result = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return result["message"]["content"].strip()

    # ========================
    # 解析
    # ========================
    def parse_response(self, content: str) -> List[int]:
        if not content:
            return []

        return self._parse_tool_ids(content)

    # ========================
    # 内部解析工具
    # ========================
    def _parse_tool_ids(self, content: str) -> List[int]:
        parsers = [
            self._parse_json,
            self._parse_codeblock,
            self._parse_brackets,
            self._parse_numbers,
        ]
        for parser in parsers:
            try:
                data = parser(content)
                result = self._normalize(data)
                if result:
                    return result
            except Exception:
                continue
        return []

    def _normalize(self, data: Any) -> List[int]:
        result: List[int] = []

        if isinstance(data, list):
            for x in data:
                val = self._to_int(x)
                if val is not None and val not in result:
                    result.append(val)
        elif isinstance(data, (int, str)):
            val = self._to_int(data)
            if val is not None:
                result = [val]

        return result

    def _to_int(self, x: Any) -> Optional[int]:
        if isinstance(x, int):
            return x
        if isinstance(x, str) and re.fullmatch(r"\d+", x.strip()):
            return int(x)
        return None

    def _parse_json(self, text: str):
        return json.loads(text)

    def _parse_codeblock(self, text: str):
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
        if not match:
            raise ValueError("no code block found")
        return json.loads(match.group(1))

    def _parse_brackets(self, text: str):
        match = re.search(r"\[[^\]]*\]", text)
        if not match:
            raise ValueError("no brackets found")
        try:
            return json.loads(match.group(0))
        except Exception:
            return [int(x) for x in re.findall(r"\d+", match.group(0))]

    def _parse_numbers(self, text: str):
        nums = re.findall(r"\d+", text)
        if not nums:
            raise ValueError("no numbers found")
        return [int(x) for x in nums]