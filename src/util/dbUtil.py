# db_manager.py
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from src.config.dbConfig import MYSQL_CONFIG, POSTGRESQL_CONFIG

class DatabaseManager:
    def __init__(self):
        # MySQL 引擎
        self.mysql_engine = self._create_mysql_engine()
        # PostgreSQL 引擎
        self.pg_engine = self._create_postgresql_engine()

    def _create_mysql_engine(self):
        url = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@" \
              f"{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
        return create_engine(
            url,
            poolclass=QueuePool,
            pool_size=10,          # 连接池大小
            max_overflow=20,       # 最大溢出连接数
            pool_pre_ping=True,    # 自动检测连接是否存活
            echo=False             # 是否打印SQL日志
        )

    def _create_postgresql_engine(self):
        url = f"postgresql+psycopg2://{POSTGRESQL_CONFIG['user']}:{POSTGRESQL_CONFIG['password']}@" \
              f"{POSTGRESQL_CONFIG['host']}:{POSTGRESQL_CONFIG['port']}/{POSTGRESQL_CONFIG['database']}"
        return create_engine(
            url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )

    def get_mysql_connection(self):
        """获取 MySQL 原始连接（可用于原生SQL）"""
        return self.mysql_engine.connect()

    def get_postgresql_connection(self):
        """获取 PostgreSQL 原始连接"""
        return self.pg_engine.connect()

    def close(self):
        """关闭所有连接池"""
        self.mysql_engine.dispose()
        self.pg_engine.dispose()

# 全局单例
db_manager = DatabaseManager()