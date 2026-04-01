# base_model.py
import os
from typing import List
from abc import ABC, abstractmethod
from langchain_community.vectorstores import VectorStore

class BaseVectorModel(ABC):
    """
    通用向量模型接口，兼容 LangChain Embeddings。
    """
    def __init__(self, model_name: str, vector_store: VectorStore, threshold: float = 0.98,
                 api_key_env: str | None = None,str_max_len: int = 512):
        # API Key 可选
        if api_key_env is not None:
            self._api_key = os.getenv(api_key_env)
        else:
            self._api_key = None
        self.str_max_len=str_max_len
        self.model_name = model_name
        self._vector_dim = None  # 缓存维度
        self.threshold = threshold

        if vector_store:
            self.vector_store = vector_store

    # ---------------- 抽象方法 ----------------
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """返回单条文本向量"""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """返回多条文本向量"""
        pass
    # ---------------- 公共方法 ----------------
    def get_vector_dimension(self) -> int:
        """获取向量维度"""
        if self._vector_dim is None:
            vec = self.embed_query("sample text for dimension")
            self._vector_dim = len(vec)
        return self._vector_dim

    def search_vector(self, vector: List[float], top_k: int = 5):
        """向量搜索"""
        if self.vector_store is None:
            raise ValueError("vector_store 未初始化")
        return self.vector_store.similarity_search_by_vector(vector, k=top_k)

    def insert_vector_with_content(self, content: str) -> bool:
            if(len(content)>self.str_max_len):
                str_list = split_text_overlap(content, self.str_max_len, overlap=50)
                self.insert_vector_with_contents(str_list)
                return True
            else:
                vec=self.embed_query(content)
                if(self._insert_vector(vec, content)):
                    return True
                else:
                    return False
                
                
    def insert_vector_with_contents(self, contents: list[str]):
        sum=len(contents)
        success=0
        for content in contents:
            if(self.insert_vector_with_content(content)):
                success+=1
        print(f"成功插入 {success} / {sum} 个向量")


    def search_content_by_vector(self, vector: List[float], top_k: int = 5) -> List[str]:
        """根据向量返回相似文本内容"""
        if self.vector_store is None:
            raise ValueError("vector_store 未初始化")
        results = self.vector_store.similarity_search_by_vector(vector, k=top_k)
        return [doc.page_content for doc in results]

    # ---------------- 新增方法 ----------------
    def search_content_by_text(self, text: str, top_k: int = 5) -> List[str]:
        """
        根据文本获取最相似的文本列表
        1. 先生成文本向量
        2. 再调用向量搜索
        """
        vector = self.embed_query(text)
        return self.search_content_by_vector(vector, top_k=top_k)


    def _can_insert(self, content: str) -> bool:
        results = self.vector_store.similarity_search_with_score(content, k=1)

        if not results:
            return True

        _, score = results[0]
        return score < self.threshold
    def _insert_vector(self,vector:List[float], content: str)->bool:
        if(self._can_insert(content)):
            self.vector_store.add_texts([content],embedding=vector)
            return True
        else:
            return False
def split_text_overlap(text: str, max_len: int, overlap: int = 50) -> list[str]:
    """
    将文本切分为固定长度的 chunk，并带 overlap
    - text: 要切分的文本
    - max_len: 每个 chunk 最大长度
    - overlap: 相邻 chunk 重叠长度
    """
    if overlap >= max_len:
        overlap = max_len // 2  # 防止负步长

    res = []
    step = max_len - overlap
    for i in range(0, len(text), step):
        res.append(text[i:i + max_len])
    return res