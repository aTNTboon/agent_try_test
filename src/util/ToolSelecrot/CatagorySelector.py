import json
import re
from typing import Any, List, Optional


from src.util.BaseToolSelector import BaseToolSelector


class CatagoryToolSelector(BaseToolSelector):
    """根据用户问题选择工具类别。"""

    def __init__(self):
        super().__init__(
            max_retries=2,
            retry_sleep=0.3,
            default_tool_ids=[],
        )
        self.model_name = "qwen2.5-fixed"

    def rule_route(self, input: dict) -> Optional[List[str]]:
        return None

    def get_categories(self) -> List[str]:
        # 延迟导入，避免模块导入阶段就触发数据库连接
        from src.util.respository.ToolRespository import get_tool_repository

        return get_tool_repository().list_categories()

    def build_prompt(self, input: dict) -> str:
        question = str(input.get("question", "")).strip()
        categories = self.get_categories()
        category_text = ",".join(categories)

        return f"""你是工具类别选择助手。
请根据用户的问题选择需要的工具类别。
类别有[{category_text}]。

要求：
1. 只返回 JSON 数组，数组元素必须是上面类别中的字符串。
2. 不要输出解释、代码块或其它文本。
3. 如果没有合适类别，返回 []。

问题：{question}
输出：
"""

    def build_retry_prompt(self, input: dict) -> str:
        retry_hint = (
            "注意：严格返回 JSON 字符串数组，例如 [\"meeting\"] 或 [\"meeting\",\"search\"]。\n"
        )
        return retry_hint + self.build_prompt(input)

    def call_model(self, prompt: str) -> str:
        import ollama

        result = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return result["message"]["content"].strip()

    def parse_response(self, content: str) -> List[str]:
        if not content:
            return []

        candidates = self._parse_string_list(content)
        if not candidates:
            return []

        available = set(self.get_categories())
        result: List[str] = []
        for item in candidates:
            if item in available and item not in result:
                result.append(item)
        return result

    def _parse_string_list(self, content: str) -> List[str]:
        parsers = [
            self._parse_json,
            self._parse_codeblock,
            self._parse_brackets,
        ]
        for parser in parsers:
            try:
                data = parser(content)
                normalized = self._normalize(data)
                if normalized:
                    return normalized
            except Exception:
                continue
        return []

    def _normalize(self, data: Any) -> List[str]:
        result: List[str] = []
        if isinstance(data, list):
            for x in data:
                if isinstance(x, str):
                    val = x.strip()
                    if val and val not in result:
                        result.append(val)
        elif isinstance(data, str):
            val = data.strip()
            if val:
                result = [val]
        return result

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
        return json.loads(match.group(0))
