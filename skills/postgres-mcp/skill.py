"""
postgres-mcp - PostgreSQL database access for AI agents

A SkillGuard official skill for querying and managing PostgreSQL databases
with parameterized queries to prevent SQL injection.
Upstream: https://github.com/modelcontextprotocol/servers/tree/main/src/postgres
"""

import os
from pathlib import Path

from skillguard.sdk import Skill, SkillContext, SkillManifest, SkillResult


class PostgresMCPSkill(Skill):
    """PostgreSQL database access skill."""

    def execute(self, action: str, context: SkillContext) -> SkillResult:
        actions = {
            "query": self._query,
            "execute": self._execute,
            "list_tables": self._list_tables,
            "describe_table": self._describe_table,
            "explain": self._explain,
        }

        handler = actions.get(action)
        if handler is None:
            return SkillResult.error(f"Unknown action: {action}")

        return handler(context)

    def _get_dsn(self, context: SkillContext):
        dsn = (os.environ.get("DATABASE_URL") or
               context.secrets.get("DATABASE_URL"))
        if not dsn:
            return None, SkillResult.error("DATABASE_URL not set")
        return dsn, None

    def _query(self, context: SkillContext) -> SkillResult:
        sql = context.parameters.get("sql")
        if not sql:
            return SkillResult.error("Missing required parameter: sql")

        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return SkillResult.denied("query action only allows SELECT/WITH statements; use execute for mutations")

        params = context.parameters.get("params", [])
        limit = min(context.parameters.get("limit", 100), 1000)

        dsn, err = self._get_dsn(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_query=sql[:100])

        try:
            import psycopg2
            import psycopg2.extras
            with psycopg2.connect(dsn) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql + f" LIMIT {limit}", params or None)
                    rows = [dict(row) for row in cur.fetchall()]
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    return SkillResult.success({"columns": columns, "rows": rows, "count": len(rows)})
        except ImportError:
            return SkillResult.error("psycopg2-binary not installed: pip install psycopg2-binary")
        except Exception as e:
            return SkillResult.error(f"PostgreSQL error: {e}")

    def _execute(self, context: SkillContext) -> SkillResult:
        sql = context.parameters.get("sql")
        if not sql:
            return SkillResult.error("Missing required parameter: sql")

        sql_upper = sql.strip().upper()
        blocked = ("DROP TABLE", "DROP DATABASE", "TRUNCATE", "DROP SCHEMA")
        for keyword in blocked:
            if keyword in sql_upper:
                return SkillResult.denied(f"Dangerous operation blocked: {keyword}")

        params = context.parameters.get("params", [])

        dsn, err = self._get_dsn(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True, would_execute=sql[:100])

        try:
            import psycopg2
            with psycopg2.connect(dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params or None)
                    conn.commit()
                    return SkillResult.success({"rows_affected": cur.rowcount})
        except ImportError:
            return SkillResult.error("psycopg2-binary not installed")
        except Exception as e:
            return SkillResult.error(f"PostgreSQL error: {e}")

    def _list_tables(self, context: SkillContext) -> SkillResult:
        schema = context.parameters.get("schema", "public")

        dsn, err = self._get_dsn(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success([], dry_run=True)

        try:
            import psycopg2
            with psycopg2.connect(dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT table_name,
                               (SELECT reltuples::bigint FROM pg_class
                                WHERE relname = table_name) as est_rows
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """, (schema,))
                    tables = [{"name": row[0], "estimated_rows": row[1]}
                              for row in cur.fetchall()]
                    return SkillResult.success(tables, count=len(tables))
        except ImportError:
            return SkillResult.error("psycopg2-binary not installed")
        except Exception as e:
            return SkillResult.error(f"PostgreSQL error: {e}")

    def _describe_table(self, context: SkillContext) -> SkillResult:
        table = context.parameters.get("table")
        if not table:
            return SkillResult.error("Missing required parameter: table")

        schema = context.parameters.get("schema", "public")

        dsn, err = self._get_dsn(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            import psycopg2
            with psycopg2.connect(dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable,
                               column_default, character_maximum_length
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                    """, (schema, table))
                    columns = [{"name": r[0], "type": r[1], "nullable": r[2] == "YES",
                                "default": r[3], "max_length": r[4]}
                               for r in cur.fetchall()]

                    cur.execute("""
                        SELECT indexname, indexdef
                        FROM pg_indexes
                        WHERE schemaname = %s AND tablename = %s
                    """, (schema, table))
                    indexes = [{"name": r[0], "definition": r[1]} for r in cur.fetchall()]

                    return SkillResult.success({
                        "table": f"{schema}.{table}",
                        "columns": columns,
                        "indexes": indexes,
                    })
        except ImportError:
            return SkillResult.error("psycopg2-binary not installed")
        except Exception as e:
            return SkillResult.error(f"PostgreSQL error: {e}")

    def _explain(self, context: SkillContext) -> SkillResult:
        sql = context.parameters.get("sql")
        if not sql:
            return SkillResult.error("Missing required parameter: sql")

        analyze = context.parameters.get("analyze", False)

        dsn, err = self._get_dsn(context)
        if err:
            return err

        if context.dry_run:
            return SkillResult.success({}, dry_run=True)

        try:
            import psycopg2
            with psycopg2.connect(dsn) as conn:
                with conn.cursor() as cur:
                    explain_sql = f"EXPLAIN {'ANALYZE ' if analyze else ''}FORMAT JSON {sql}"
                    cur.execute(explain_sql)
                    plan = cur.fetchone()[0]
                    return SkillResult.success({"plan": plan})
        except ImportError:
            return SkillResult.error("psycopg2-binary not installed")
        except Exception as e:
            return SkillResult.error(f"PostgreSQL error: {e}")


def create_skill() -> PostgresMCPSkill:
    manifest = SkillManifest.from_yaml(Path(__file__).parent / "skillguard.yaml")
    return PostgresMCPSkill(manifest)
