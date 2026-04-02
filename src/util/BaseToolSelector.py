from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig

from src.util.entity.ToolMeta import ToolMeta


class BaseToolSelector(Runnable, ABC):
    """
    核心流程骨架：
    query -> rule -> llm -> parse -> retry -> fallback
    """

    def __init__(
        self,
        max_retries: int = 2,
        retry_sleep: float = 0.3,
        default_tool_ids: Optional[list[int]] = None,
    ):
        self.max_retries = max_retries
        self.retry_sleep = retry_sleep
        self.default_tool_ids = default_tool_ids or []
    # ========================
    # 对外统一入口
    # ========================
    def query(self,input) -> list[int]:
        question = input.get("question", "")
        question = str(question).strip()
        if not question:
            return self.default_tool_ids

        # 1️⃣ 规则路由（你要求现在先返回 None）
        rule_result = self.rule_route(input)
        if rule_result is not None:
            return rule_result

        # 2️⃣ LLM 路由（带重试）
        return self._llm_route_with_retry(input)

    def invoke(
        self,
        input: Any,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> list[int]:

        if isinstance(input, dict):
            return self.query(
                input=input,

            )

        raise ValueError(f"Unsupported input type: {type(input)}")

    # ========================
    # 主流程（固定，不允许子类改）
    # ========================
    def _llm_route_with_retry(self, input:dict) -> list[int]:

        for attempt in range(self.max_retries + 1):

            prompt = (
                self.build_prompt(input)
                if attempt == 0
                else self.build_retry_prompt(input)
            )

            content = self.call_model(prompt)

            result = self.parse_response(content)
            if result:
                return result

            if attempt < self.max_retries:
                time.sleep(self.retry_sleep)

        return self.default_tool_ids

    # ========================
    # 子类必须实现的方法
    # ========================

    @abstractmethod
    def rule_route(self, input:dict) -> Optional[list[int]]:
        """规则路由（可以返回 None）"""
        pass

    @abstractmethod
    def build_prompt(self, input:dict) -> str:
        """构造 prompt"""
        pass

    @abstractmethod
    def build_retry_prompt(self, input:dict) -> str:
        """构造 retry prompt"""
        pass

    @abstractmethod
    def call_model(self, prompt: str) -> str:
        """调用模型"""
        pass

    @abstractmethod
    def parse_response(self, content: str) -> list[int]:
        """解析模型输出"""
        pass