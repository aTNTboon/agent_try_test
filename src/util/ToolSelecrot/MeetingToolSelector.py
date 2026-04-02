from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any, Callable, List, Optional


from src.util.BaseToolSelector import BaseToolSelector
from src.util.ToolSelecrot.CatagorySelector import CategorySelector
from src.util.entity.ToolMeta import ToolMeta
if TYPE_CHECKING:
    from src.util.respository.ToolRespository import ToolRepository


class DefaultToolSelector(BaseToolSelector):
    def __init__(
        self,
        repository: "ToolRepository | None" = None,
        category_selector: CategorySelector | None = None,
        model_caller: Callable[[str], str] | None = None,
    ):
        super().__init__(
            max_retries=2,
            retry_sleep=0.3,
            default_tool_ids=[2],
        )
        self.model_name = "qwen2.5-fixed"
        if repository is None:
            from src.util.respository.ToolRespository import get_tool_repository

            repository = get_tool_repository()
        self.repository = repository
        self.category_selector = category_selector or CategorySelector(self.repository)
        self.model_caller = model_caller

    def rule_route(self, input: dict) -> Optional[List[int]]:
        return None

    def _normalize_input_categories(self, input_value: Any) -> list[str]:
        if isinstance(input_value, list):
            return [str(x).strip() for x in input_value if str(x).strip()]
        if isinstance(input_value, str) and input_value.strip():
            return [input_value.strip()]
        return []

    def _resolve_categories(self, input: dict) -> list[str]:
        manual_categories = self._normalize_input_categories(input.get("category", []))
        question = str(input.get("question", "")).strip()
        auto_categories = self.category_selector.select_categories(question)
        return self.category_selector.merge_categories(manual_categories, auto_categories)

    def build_prompt(self, input: dict) -> str:
        question = str(input.get("question", "")).strip()
        categories = self._resolve_categories(input)

        if categories:
            tools: List[ToolMeta] = self.repository.get_tools_by_categories(categories)
        else:
            # 没有命中类别时，聚合所有可用类别工具，避免漏召回。
            all_categories = self.repository.list_categories()
            tools = self.repository.get_tools_by_categories(all_categories)

        tool_text = "\n".join(
            f"{t.id}: {t.name}，作用：{t.description}"
            for t in tools
            if t.enabled
        )

        return f"""你是工具选择助手。
只返回 JSON 数组（工具 id）。请选择你认为回答这个问题需要选取的工具。

工具：
{tool_text}

问题：{question}
输出：
"""

    def build_retry_prompt(self, input: dict) -> str:
        base_prompt = self.build_prompt(input)
        retry_hint = (
            "注意：请严格按照 JSON 数组格式返回工具 id，例如 [1] 或 [1,2]，"
            "不要返回文字描述或其他内容。\n"
        )
        return retry_hint + base_prompt

    def call_model(self, prompt: str) -> str:
        if self.model_caller is not None:
            return self.model_caller(prompt)

        import ollama

        result = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return result["message"]["content"].strip()

    def parse_response(self, content: str) -> List[int]:
        if not content:
            return []
        return self._parse_tool_ids(content)

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
