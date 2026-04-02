import sys
import types
import unittest

# 轻量 mock langchain_core 依赖，保证单测只验证输入输出链路
langchain_core_module = types.ModuleType("langchain_core")
runnables_module = types.ModuleType("langchain_core.runnables")
config_module = types.ModuleType("langchain_core.runnables.config")


class Runnable:
    pass


class RunnableConfig:
    pass


runnables_module.Runnable = Runnable
config_module.RunnableConfig = RunnableConfig

sys.modules.setdefault("langchain_core", langchain_core_module)
sys.modules.setdefault("langchain_core.runnables", runnables_module)
sys.modules.setdefault("langchain_core.runnables.config", config_module)


openai_module = types.ModuleType("openai")


class BaseModel:
    pass


openai_module.BaseModel = BaseModel
sys.modules.setdefault("openai", openai_module)

from src.util.ToolSelecrot.CatagorySelector import CatagoryToolSelector


class StubCatagoryToolSelector(CatagoryToolSelector):
    def __init__(self, model_output: str, categories=None):
        super().__init__()
        self._model_output = model_output
        self._categories = categories or ["meeting", "search"]
        self.last_prompt = ""

    def get_categories(self):
        return self._categories

    def call_model(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._model_output


class CatagoryToolSelectorTests(unittest.TestCase):
    def test_query_chain_returns_expected_categories(self):
        selector = StubCatagoryToolSelector('["meeting","search"]')

        result = selector.query({"question": "帮我查会议并搜索资料"})

        self.assertEqual(result, ["meeting", "search"])

    def test_prompt_includes_dynamic_categories(self):
        selector = StubCatagoryToolSelector('["meeting"]', categories=["meeting", "search", "calendar"])

        selector.query({"question": "帮我看会议"})

        self.assertIn("类别有[meeting,search,calendar]", selector.last_prompt)

    def test_parse_filters_unknown_category(self):
        selector = StubCatagoryToolSelector('["meeting","unknown"]', categories=["meeting", "search"])

        result = selector.query({"question": "测试"})

        self.assertEqual(result, ["meeting"])


if __name__ == "__main__":
    unittest.main()
