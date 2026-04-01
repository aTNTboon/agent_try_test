from sqlalchemy import Connection, text

import src.util.dbUtil as db_manager
 

class PostgreSqlUtil:
    def __init__(self):
        try:
            self.pg_conn:Connection = db_manager.db_manager.get_postgresql_connection()
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            exit()
    def create_table(self):
        try:
            self.pg_conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            # 临时表
            self.pg_conn.execute(text("CREATE TEMP TABLE test_vector (id SERIAL PRIMARY KEY, embedding vector(3));"))
            self.pg_conn.commit()
            print("Table created successfully")
        except Exception as e:
            print(f"Error creating table: {e}")