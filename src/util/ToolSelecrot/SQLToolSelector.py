import json
import re
import ollama
from typing import Any, Optional

from pydantic import BaseModel

from src.util.BaseToolSelector import BaseToolSelector

# 继承刚才那个 BaseToolSelector


class ToolMeta(BaseModel):
    id: int
    code: str
    name: str
    description: str
    enabled: bool = True


class DefaultToolSelector(BaseToolSelector):
    def __init__(self):
        super().__init__(
            max_retries=2,
            retry_sleep=0.3,
            default_tool_ids=[2],
        )

        self.model_name = "qwen2.5-fixed"

        self.tools: list[ToolMeta] = [
                ToolMeta(**{
                    "id": 1,
                    "code": "weather",
                    "name": "天气查询",
                    "description": "查询天气、气温、降雨",
                }),
                ToolMeta(**{
                    "id": 2,
                    "code": "search",
                    "name": "互联网搜索",
                    "description": "搜索网页、新闻、百科",
                }),
                ToolMeta(**{
                    "id": 3,
                    "code": "calc",
                    "name": "数学计算",
                    "description": "数学计算、表达式求值",
                }),
            ]
    # ========================
    # 规则（你要求先禁用）
    # ========================
    def rule_route(self, question: str) -> Optional[list[int]]:
        return None

    # ========================
    # Prompt
    # ========================
    def build_prompt(self, question: str) -> str:
        tool_text = "\n".join(
            f"{t.id}: {t.name}，作用：{t.description}"
            for t in self.tools if t.enabled
        )

        return f"""你是工具选择助手。
只返回 JSON 数组（工具 id）。

工具：
{tool_text}

问题：{question}
输出：
"""

    def build_retry_prompt(self, question: str) -> str:
        tool_text = "\n".join(
            f"{t.id}: {t.name}"
            for t in self.tools if t.enabled
        )

        return f"""格式错误，请只输出 JSON 数组，例如 [1] 或 [1,2]
工具：
{tool_text}

问题：{question}
输出：
"""

    # ========================
    # 模型
    # ========================
    def call_model(self, prompt: str) -> str:
        result = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return result["message"]["content"].strip()

    # ========================
    # 解析（重点）
    # ========================
    def parse_response(self, content: str) -> list[int]:
        if not content:
            return []

        valid_ids = {t.id for t in self.tools if t.enabled}

        # 多策略解析
        for parser in [
            self._parse_json,
            self._parse_codeblock,
            self._parse_brackets,
            self._parse_numbers,
        ]:
            try:
                data = parser(content)
                result = self._normalize(data, valid_ids)
                if result:
                    return result
            except:
                continue

        return []

    # ========================
    # 内部解析工具
    # ========================
    def _normalize(self, data: Any, valid_ids: set[int]) -> list[int]:
        result = []

        if isinstance(data, list):
            for x in data:
                x = self._to_int(x)
                if x and x in valid_ids and x not in result:
                    result.append(x)

        elif isinstance(data, (int, str)):
            x = self._to_int(data)
            if x and x in valid_ids:
                result = [x]

        return result

    def _to_int(self, x):
        if isinstance(x, int):
            return x
        if isinstance(x, str) and re.fullmatch(r"\d+", x.strip()):
            return int(x)
        return None

    def _parse_json(self, text: str):
        return json.loads(text)

    def _parse_codeblock(self, text: str):
        import re
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
        if not match:
            raise ValueError
        return json.loads(match.group(1))

    def _parse_brackets(self, text: str):
        import re
        match = re.search(r"\[[^\]]*\]", text)
        if not match:
            raise ValueError
        try:
            return json.loads(match.group(0))
        except:
            return [int(x) for x in re.findall(r"\d+", match.group(0))]

    def _parse_numbers(self, text: str):
        import re
        nums = re.findall(r"\d+", text)
        if not nums:
            raise ValueError
        return [int(x) for x in nums]