import os
import sqlite3
import hashlib
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma


# 初始化（建表）

class DBClient:
    """数据库客户端封装"""

    
    def __init__(self, db_path: str = 'my.db', vector_store_path: str = './chroma_db', str_max_len: int|None = 200, **kwargs):

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        self.vector_store=Chroma(persist_directory=vector_store_path,embedding_function=DashScopeEmbeddings(),collection_name="my_collection")
        if str_max_len is not None:
            self.str_max_len = str_max_len
        self.init()

    def init(self):
        os.environ["DASHSCOPE_API_KEY"] = "sk-ee359256b7da45d18462e9f854b756e0"

        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS md5_table (
                md5_str TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def get_reference(self,ques:str,amount:int=3)->list[str]:
        results=self.vector_store.similarity_search(ques, k=amount)
        return [result.page_content for result in results]
    def upload_str(self, content: str) -> bool:
        if content is None:
            return False
        if content == "":
            return True
        # 无论长短，都使用 _upload_str_splited，但短字符串直接作为一个块
        if len(content) <= self.str_max_len:
            return self._upload_str_splited(content)
        else:
            parts = [content[i:i+self.str_max_len] for i in range(0, len(content), self.str_max_len)]
            success = any(self._upload_str_splited(part) for part in parts)
            print(f"分成 {len(parts)} 部分，成功上传 {sum(1 for p in parts if self._upload_str_splited(p))} 部")
            return success


    def _upload_str_splited(self,content:str)->bool:
        md5_str=self.getmd5(content)
        if(self.checkmd5(md5_str)):
            print("已存在")
            return False
        else:
            self.savemd5(md5_str)
            self.vector_store.add_texts([content],ids=[md5_str])
            return True
        

    def getmd5(self,input_str: str, encoding: str = "utf-8") -> str:
        """计算字符串 MD5"""
        str_bytes = input_str.encode(encoding)
        md5_hash = hashlib.md5()
        md5_hash.update(str_bytes)
        return md5_hash.hexdigest()

    def checkmd5(self, md5_str: str) -> bool:
        """检查 MD5 是否已存在"""
        self.cursor.execute("SELECT 1 FROM md5_table WHERE md5_str = ?", (md5_str,))
        return self.cursor.fetchone() is not None

    def delete_md5(self, md5_str: str) -> bool:
        """删除指定 MD5"""
        self.cursor.execute("DELETE FROM md5_table WHERE md5_str = ?", (md5_str,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def savemd5(self, md5_str: str) -> bool:
        """保存 MD5，返回是否插入成功"""
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO md5_table (md5_str) VALUES (?)", 
                (md5_str,)
            )
            self.conn.commit()
            return self.cursor.rowcount > 0  # 1=插入成功, 0=已存在
        except sqlite3.Error as e:
            print(f"Error: {e}")
            return False
