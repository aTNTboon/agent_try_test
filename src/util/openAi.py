import datetime
import functools
import os
import time
from langchain.messages import HumanMessage,SystemMessage,AIMessage
from langchain_community.embeddings import DashScopeEmbeddings
from openai import OpenAI
import langchain
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

api_key = os.getenv("API_KEY", "sk-4RA02El8XSHwNCQJ2471085cBd97445eB56075DaD82a567d")
base_url = os.getenv("BASE_URL", "https://dpapi.cn/v1/chat/completions")

messages =[
        SystemMessage(content="你是一个有趣的助手，可以回答任何问题。"),
        HumanMessage(content="你好，请问你是谁？"),
]
llm = ChatOpenAI(
    api_key=SecretStr(api_key) if isinstance(api_key, str) else api_key,
    base_url=base_url,
    model="deepseek-r1",
    temperature=0.7,
    streaming=True,  # 启用流式输出
)



def request():
    content = ""
    
    for chunk in llm.stream(messages):
        chunk_content = chunk.content
        
        # 处理不同类型的 content
        if isinstance(chunk_content, str):
            print(chunk_content, end="", flush=True)
            content += chunk_content
        elif isinstance(chunk_content, list):
            # 列表类型：提取字符串元素
            for item in chunk_content:
                if isinstance(item, str):
                    print(item, end="", flush=True)
                    content += item
                elif isinstance(item, dict) and "text" in item:
                    text = item["text"]
                    print(text, end="", flush=True)
                    content += text
    messages.append(AIMessage(content=content))

if __name__ == "__main__":
    while(True):
        text= input()
        if(text=="e"):
            break
        else:
            messages.append(HumanMessage(content=text))
            result= request()
            
