from __future__ import annotations

from dataclasses import dataclass
import sys
import types
import unittest

# 为了在无 langchain 依赖环境下运行链路单测，注入最小桩对象。
langchain_core = types.ModuleType("langchain_core")
runnables = types.ModuleType("langchain_core.runnables")
config = types.ModuleType("langchain_core.runnables.config")


class Runnable:  # pragma: no cover
    pass


class RunnableConfig:  # pragma: no cover
    pass


runnables.Runnable = Runnable
config.RunnableConfig = RunnableConfig
sys.modules["langchain_core"] = langchain_core
sys.modules["langchain_core.runnables"] = runnables
sys.modules["langchain_core.runnables.config"] = config

from src.util.ToolSelecrot.CatagorySelector import CategorySelector
from src.util.ToolSelecrot.MeetingToolSelector import DefaultToolSelector


@dataclass
class FakeTool:
    id: int
    code: str
    name: str
    description: str
    category: str
    handler: str
    enabled: bool = True


class FakeRepository:
    def __init__(self):
        self.category_calls: list[list[str]] = []
        self.categories = ["meeting", "search", "calendar"]

    def list_categories(self):
        return self.categories

    def get_tools_by_categories(self, categories):
        self.category_calls.append(list(categories))
        tools = [
            FakeTool(1, "meeting_summary", "会议总结", "总结会议内容", "meeting", "h1"),
            FakeTool(2, "global_search", "全局搜索", "执行搜索", "search", "h2"),
            FakeTool(3, "calendar_query", "日程查询", "查询日程", "calendar", "h3"),
        ]
        return [tool for tool in tools if tool.category in categories]


class ToolSelectionFlowTests(unittest.TestCase):
    def setUp(self):
        self.repo = FakeRepository()
        self.category_selector = CategorySelector(self.repo)

    def test_category_selector_matches_multiple_categories(self):
        categories = self.category_selector.select_categories("meeting search 我昨天没参会吗")
        self.assertEqual(categories, ["meeting", "search"])

    def test_build_prompt_falls_back_to_all_categories(self):
        selector = DefaultToolSelector(
            repository=self.repo,
            category_selector=self.category_selector,
            model_caller=lambda _: "[1]",
        )

        prompt = selector.build_prompt({"question": "帮我处理一下"})

        self.assertIn("会议总结", prompt)
        self.assertIn("全局搜索", prompt)
        self.assertIn("日程查询", prompt)
        self.assertEqual(self.repo.category_calls[-1], ["meeting", "search", "calendar"])

    def test_query_io_chain(self):
        selector = DefaultToolSelector(
            repository=self.repo,
            category_selector=self.category_selector,
            model_caller=lambda _: "```json\n[2, 1]\n```",
        )

        result = selector.query({"question": "meeting search: 今天需要哪些工具?"})

        self.assertEqual(result, [2, 1])


if __name__ == "__main__":
    unittest.main()
