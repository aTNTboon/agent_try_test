from typing import List
from langchain.chat_models import BaseChatModel
from langchain_community.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
import ollama
from src.util.BaseVectorModel import BaseVectorModel
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
# 调用 Ollama embed

class OllamaModel(BaseVectorModel):
    def __init__(self, model_name: str,vector_store:VectorStore,threshold:float=0.98,api_key_env: str|None=None, ):
   
        super().__init__(model_name,vector_store)
        self.model = ollama.Client(model=model_name)
        
    def embed_query(self, text: str) -> List[float]:
        """
        返回单条文本向量
        """
        # 调用 Ollama embed API
        result: ollama.EmbedResponse = ollama.embed(
            model=self.model_name,
            input=text
        )
        # Ollama 返回 embeddings 列表，每条文本是一个向量
        vector = result['embeddings'][0]  # 获取单条文本向量
        return vector


    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        batch = ollama.embed(
        model='qwen2.5-fixed',
        input=texts
        )
        return batch['embeddings']



    
