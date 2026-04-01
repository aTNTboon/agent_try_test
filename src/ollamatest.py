from typing import Any, Sequence
import json
import os
from typing import Sequence
from langchain_community.vectorstores import Chroma
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict

from ollama import chat, ChatResponse
from langchain.messages import HumanMessage,SystemMessage,AIMessage
from src.util.XunfeiModel import XunfeiModel
from testRunnable import test2
import json
import requests
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
# 更简单的写法，不用定义类
# 推荐的新导入方式（langchain-core）
from langchain_core.chat_history import InMemoryChatMessageHistory,BaseChatMessageHistory
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.embeddings import DashScopeEmbeddings
#
from langchain_core.output_parsers import StrOutputParser  # ✅ 用这个
from langchain_core.documents import Document
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    get_buffer_string,
)
# response: ChatResponse = chat(model='qwen2.5-fixed', messages=[
#   {
#     'role': 'user',
#     'content': '你是谁da？',
#   },
# ])
# # 打印响应内容
# print(response['message']['content'])

# 或者直接访问响应对象的字段
#print(response.message.content)
model = XunfeiModel(
    api_key="ZXSdpSgEJXFhygMYiiaA",
    api_secret="jDalRRbmMsQBXJeiCUAa",
    model="x1",
    temperature=0.7
)

class parser(Runnable) :
        def __init__(self):
            super().__init__()
        
        def run(self):
            pass

        def invoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
          if(isinstance(input,AIMessage)):
              return input.content







class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._messages = []
        
        # 文件存在则加载，不存在则创建空文件
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._messages = messages_from_dict(data)
        else:
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            self._save()

    def _save(self) -> None:
        """保存到 JSON 文件"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(messages_to_dict(self._messages), f, ensure_ascii=False, indent=2)

    @property
    def messages(self) -> list[BaseMessage]:
        return self._messages

    def add_message(self, message: BaseMessage) -> None:
        self._messages.append(message)
        self._save()

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        self._messages.extend(messages)
        self._save()

    def clear(self) -> None:
        self._messages = []
        self._save()



store={}
def get_history(session_id:str):
    if session_id not in store:
        store[session_id]=FileChatMessageHistory(f"./{session_id}_history.json")
    return store[session_id]

if __name__ == "__main__":
    os.environ["DASHSCOPE_API_KEY"] = "sk-ee359256b7da45d18462e9f854b756e0"
    vector_store=Chroma(persist_directory='./chroma_db',embedding_function=DashScopeEmbeddings(),collection_name="my_collection")
    content_list:list[str]=["hello world","hi","hello","world"]
    vector_store.add_texts(content_list,ids=["id"+str(i) for i in range(len(content_list))])
    similarty_docs:list[Document]=vector_store.similarity_search("hello",k=2)


    # chain1= RunnableWithMessageHistory(chain,get_session_history=get_history,input_messages_key="input_word",history_messages_key="history") | StrOutputParser()
    # result=chain1.invoke(input={'input_word': 'shit'},
    #                     config={'configurable': {'session_id': 'foo'}})
    # history = get_history('foo')

    prompt_template = PromptTemplate.from_template("给你的文章{content}")
    few_shot_prompt = FewShotPromptTemplate(
        example_prompt=prompt_template,
        examples=[{"content": doc.page_content} for doc in similarty_docs],
        prefix="根据文档回答问题",
        suffix="基于前面的文章，回答我下面的问题 {input_word}",
        input_variables=['input_word'],
    )
#     example_prompt=prompt_template,
#     examples=example_data,
#     prefix="告知单词反义词，以下是例子",
#     suffix="基于前面的例子，告诉我接下来词语的反义词 {input_word}",
#     input_variables=['input_word'],
# )

    def printPrompt(prompt):
        print(prompt)
        return prompt


    chain=few_shot_prompt|printPrompt
    chain.invoke({'input_word': '怎么翻译你好'})


