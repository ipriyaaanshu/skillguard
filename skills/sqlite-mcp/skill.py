"""
sqlite-mcp - Lightweight local SQLite database operations

A SkillGuard official skill for interacting with local SQLite databases.
Uses parameterized queries to prevent SQL injection. Sandbox-safe (no network).
Upstream: https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite
"""

import sqlite3
from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class SQLiteMCPSkill(Skill):
    """SQLite local database skill."""

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "query": self._query,
            "execute": self._execute,
            "list_tables": self._list_tables,
            "describe_table": self._describe_table,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _resolve_db(self, context: SkillContext) -> tuple:
        db_path_str = context.parameters.get("db_path")
        if not db_path_str:
            return None, SkillResult.error("Missing required parameter: db_path")

        db_path = (context.workspace / db_path_str).resolve()

        try:
            db_path.relative_to(context.workspace.resolve())
        except ValueError:
            return None, SkillResult.denied("db_path is outside workspace")

        return db_path, None

    def _query(self, context: SkillContext) -> SkillResult:
        db_path, err = self._resolve_db(context)
        if err:
            return err

        sql = context.parameters.get("sql")
        if not sql:
            return SkillResult.error("Missing required parameter: sql")

        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return SkillResult.denied("query action only allows SELECT/WITH; use execute for mutations")

        params = context.parameters.get("params", [])

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            rows = [dict(row) for row in cursor.fetchall()]
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            conn.close()
            return SkillResult.success({"columns": columns, "rows": rows, "count": len(rows)})
        except sqlite3.Error as e:
            return SkillResult.error(f"SQLite error: {e}")

    def _execute(self, context: SkillContext) -> SkillResult:
        db_path, err = self._resolve_db(context)
        if err:
            return err

        sql = context.parameters.get("sql")
        if not sql:
            return SkillResult.error("Missing required parameter: sql")

        sql_upper = sql.strip().upper()
        if "DROP DATABASE" in sql_upper:
            return SkillResult.denied("DROP DATABASE is not allowed")

        params = context.parameters.get("params", [])

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(sql, params)
            conn.commit()
            last_row_id = cursor.lastrowid
            rows_affected = cursor.rowcount
            conn.close()
            return SkillResult.success({
                "rows_affected": rows_affected,
                "last_row_id": last_row_id,
            })
        except sqlite3.Error as e:
            return SkillResult.error(f"SQLite error: {e}")

    def _list_tables(self, context: SkillContext) -> SkillResult:
        db_path, err = self._resolve_db(context)
        if err:
            return err

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return SkillResult.success(tables, count=len(tables))
        except sqlite3.Error as e:
            return SkillResult.error(f"SQLite error: {e}")

    def _describe_table(self, context: SkillContext) -> SkillResult:
        db_path, err = self._resolve_db(context)
        if err:
            return err

        table = context.parameters.get("table")
        if not table:
            return SkillResult.error("Missing required parameter: table")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = [{"cid": row[0], "name": row[1], "type": row[2],
                        "not_null": bool(row[3]), "default": row[4], "pk": bool(row[5])}
                       for row in cursor.fetchall()]
            conn.close()
            if not columns:
                return SkillResult.error(f"Table not found: {table}")
            return SkillResult.success(columns, count=len(columns))
        except sqlite3.Error as e:
            return SkillResult.error(f"SQLite error: {e}")


def create_skill() -> SQLiteMCPSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return SQLiteMCPSkill(manifest)
