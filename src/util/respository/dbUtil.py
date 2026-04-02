# db_manager.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.pool import QueuePool
from src.config.dbConfig import MYSQL_CONFIG, POSTGRESQL_CONFIG
from time import sleep

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self.mysql_engine = self._create_mysql_engine()
        self.pg_engine = self._create_postgresql_engine()
        

    def _create_mysql_engine(self):
        url = (
            f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
            f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
        )
        return self._create_engine(url, "m")

    def _create_postgresql_engine(self):
        url = (
            f"postgresql+psycopg2://{POSTGRESQL_CONFIG['user']}:{POSTGRESQL_CONFIG['password']}"
            f"@{POSTGRESQL_CONFIG['host']}:{POSTGRESQL_CONFIG['port']}/{POSTGRESQL_CONFIG['database']}"
        )
        return self._create_engine(url, "PostgreSQL")

    def _create_engine(self, url, db_name):
        for attempt in range(3):  # Retry up to 3 times
            try:
                engine = create_engine(
                    url,
                    poolclass=QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    echo=False
                )
                # Test connection immediately
                with engine.connect() as conn:
                    pass
                logger.info(f"{db_name} engine created successfully.")
                return engine
            except OperationalError as e:
                logger.warning(f"Failed to connect to {db_name}, attempt {attempt + 1}/3: {e}")
                sleep(2)
        raise RuntimeError(f"Cannot connect to {db_name} after 3 attempts.")

    def get_mysql_connection(self):
        """获取 MySQL 原始连接，支持 context manager"""
        try:
            return self.mysql_engine.connect()
        except SQLAlchemyError as e:
            logger.error(f"MySQL connection error: {e}")
            raise

    def get_postgresql_connection(self):
        """获取 PostgreSQL 原始连接"""
        try:
            return self.pg_engine.connect()
        except SQLAlchemyError as e:
            logger.error(f"PostgreSQL connection error: {e}")
            raise

    def close(self):
        """关闭所有连接池"""
        if self.mysql_engine:
            self.mysql_engine.dispose()
            logger.info("MySQL engine disposed.")
        if self.pg_engine:
            self.pg_engine.dispose()
            logger.info("PostgreSQL engine disposed.")

# 全局单例
db_manager = DatabaseManager()
