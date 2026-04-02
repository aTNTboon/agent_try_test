from __future__ import annotations

import re
from typing import Iterable

from typing import Any


class CategorySelector:
    """根据用户输入从 tools 表中可用 category 自动挑选类别。"""

    _SPLIT_PATTERN = re.compile(r"[\s,，;；|/]+")

    def __init__(self, repository: Any = None):
        if repository is None:
            from src.util.respository.ToolRespository import get_tool_repository

            repository = get_tool_repository()
        self.repository = repository

    def select_categories(self, user_input: str) -> list[str]:
        categories = self.repository.list_categories()
        if not categories:
            return []

        normalized_input = (user_input or "").strip().lower()
        if not normalized_input:
            return []

        raw_tokens = [
            token.strip().lower()
            for token in self._SPLIT_PATTERN.split(normalized_input)
            if token.strip()
        ]

        selected: list[str] = []
        for category in categories:
            cat = category.lower()
            if cat in raw_tokens or cat in normalized_input:
                selected.append(category)

        return selected

    @staticmethod
    def merge_categories(*category_groups: Iterable[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for categories in category_groups:
            for category in categories:
                key = category.strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                merged.append(category)
        return merged
