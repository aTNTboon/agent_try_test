from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.util.entity.ToolMeta import ToolMeta
from src.util.respository.dbUtil import db_manager as db


class ToolRepository:
    def __init__(self, conn: Any):
        self.conn = conn
        self.init_tools_table()

    def init_tools_table(self) -> None:
        sql = text("""
        CREATE TABLE IF NOT EXISTS tools (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            code VARCHAR(64) NOT NULL UNIQUE,
            name VARCHAR(64) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(32) NOT NULL,
            handler VARCHAR(64) NOT NULL,
            enabled TINYINT(1) NOT NULL DEFAULT 1
        )
        """)
        self.conn.execute(sql)
        self.conn.commit()

    def _row_to_tool_meta(self, row: dict) -> ToolMeta:
        return ToolMeta(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            description=row["description"],
            category=row["category"],
            handler=row["handler"],
            enabled=bool(row["enabled"]),
        )

    def get_tools_by_category(self, category: str) -> list[ToolMeta]:
        sql = text("""
        SELECT id, code, name, description, category, handler, enabled
        FROM tools
        WHERE category = :category
        ORDER BY id ASC
        """)
        result = self.conn.execute(sql, {"category": category})
        rows = result.mappings().all()
        return [self._row_to_tool_meta(dict(row)) for row in rows]

    def get_enabled_tools_by_category(self, category: str) -> list[ToolMeta]:
        sql = text("""
        SELECT id, code, name, description, category, handler, enabled
        FROM tools
        WHERE category = :category AND enabled = 1
        ORDER BY id ASC
        """)
        result = self.conn.execute(sql, {"category": category})
        rows = result.mappings().all()
        return [self._row_to_tool_meta(dict(row)) for row in rows]

    def get_tools_by_categories(self, categories: list[str]) -> list[ToolMeta]:
        if not categories:
            return []

        placeholders = ", ".join([f":cat_{i}" for i in range(len(categories))])
        params = {f"cat_{i}": category for i, category in enumerate(categories)}

        sql = text(f"""
        SELECT id, code, name, description, category, handler, enabled
        FROM tools
        WHERE category IN ({placeholders}) AND enabled = 1
        ORDER BY id ASC
        """)
        result = self.conn.execute(sql, params)
        rows = result.mappings().all()
        return [self._row_to_tool_meta(dict(row)) for row in rows]

    def get_tool_by_id(self, tool_id: int) -> Optional[ToolMeta]:
        sql = text("""
        SELECT id, code, name, description, category, handler, enabled
        FROM tools
        WHERE id = :tool_id
        LIMIT 1
        """)
        result = self.conn.execute(sql, {"tool_id": tool_id})
        row = result.mappings().first()

        if not row:
            return None

        return self._row_to_tool_meta(dict(row))

    def get_tool_basic_by_id(self, tool_id: int) -> Optional[dict]:
        sql = text("""
        SELECT id, code, name, description, category, enabled
        FROM tools
        WHERE id = :tool_id
        LIMIT 1
        """)
        result = self.conn.execute(sql, {"tool_id": tool_id})
        row = result.mappings().first()

        if not row:
            return None

        data = dict(row)
        data["enabled"] = bool(data["enabled"])
        return data

    def get_handler_by_id(self, tool_id: int) -> Optional[str]:
        sql = text("""
        SELECT handler
        FROM tools
        WHERE id = :tool_id AND enabled = 1
        LIMIT 1
        """)
        result = self.conn.execute(sql, {"tool_id": tool_id})
        row = result.mappings().first()

        if not row:
            return None

        return row["handler"]

    def list_categories(self) -> list[str]:
        sql = text("""
        SELECT DISTINCT category
        FROM tools
        WHERE enabled = 1
        ORDER BY category ASC
        """)
        result = self.conn.execute(sql)
        rows = result.mappings().all()
        return [row["category"] for row in rows]


def get_tool_repository() -> ToolRepository:
    conn = db.get_mysql_connection()
    return ToolRepository(conn)