from collections.abc import Iterator
import json
from langchain_core.messages import AIMessageChunk 
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from pydantic import Field
from typing import Any, Optional, List
import requests


class XunfeiModel(BaseChatModel):
    api_key: str = Field(default="")
    api_secret: str = Field(default="")  # 小写，Python 规范
    model: str = Field(default="x1")
    base_url: str = Field(default="https://spark-api-open.xf-yun.com/v2/chat/completions")
    temperature: float = Field(default=0.7)
    
    def model_post_init(self, __context):
        """初始化后设置 headers"""
        super().model_post_init(__context)
        self._headers = {
            "Authorization": f"Bearer {self.api_key}:{self.api_secret}",
            "Content-Type": "application/json",
        }
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[dict]:
        """LangChain 消息格式转 API 格式"""
        converted = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                converted.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                converted.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                converted.append({"role": "assistant", "content": msg.content})
            else:
                # 默认当 user 处理
                converted.append({"role": "user", "content": str(msg.content)})
        return converted
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """必须实现：同步生成"""
        
        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": self.temperature,
            "stream": False,
        }
        
        # 如果有 stop 词，加入请求
        if stop:
            payload["stop"] = stop
        
        response = requests.post(
            self.base_url,
            headers=self._headers,
            json=payload,
            timeout=40
        )
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # 必须返回 ChatResult
        return ChatResult(
            generations=[ChatGeneration(
                message=AIMessage(content=content)
            )]
        )
    def _stream(self, messages: List[BaseMessage], stop: List[str] | None = None, run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any) -> Iterator[ChatGenerationChunk]:
        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": self.temperature,
            "stream": True,
        }
        response = requests.post(
            self.base_url,
            headers=self._headers,
            json=payload,
            timeout=30,
            stream=True
        )
        response.raise_for_status()
        for chunks in response.iter_lines():
            if not chunks:
                continue
            line_str = chunks.decode('utf-8')
            if not line_str.startswith("data: "):
                continue
            line = line_str[6:]  # 去掉 "data: "
            if line == "[DONE]":  # ✅ 需要检查结束标记
                 break
            try:
                data = json.loads(line)
                delta = data["choices"][0]["delta"]
                
                # ✅ 正确提取 content
                content = delta.get("content", "") if isinstance(delta, dict) else ""
                
                if content:
                    yield ChatGenerationChunk(
                        message=AIMessageChunk(content=content)
                    )
                    
                    # 回调通知
                    if run_manager:
                        run_manager.on_llm_new_token(content)
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
    @property
    def _llm_type(self) -> str:
        return "xunfei-x1"
    
    @property
    def _identifying_params(self) -> dict[str, Any]:
        """标识参数"""
        return {
            "model": self.model,
            "temperature": self.temperature,
        }


# ========== 使用示例 ==========

