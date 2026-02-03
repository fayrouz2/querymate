from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import asyncpg


# =========================
# Config
# =========================

@dataclass(frozen=True)
class DBToolConfig: # Keeps all DB rules in one place
    database_url: str # Supabase Postgres connection string (postgresql://...)
    statement_timeout_ms: int = 8_000
    lock_timeout_ms: int = 2_000
    idle_in_tx_timeout_ms: int = 8_000
    max_rows: int = 5_000 # prevents huge accidental queries
    enforce_limit: bool = True
    allow_multi_statement: bool = False
    max_repairs: int = 2 # to prevent infinite loops


# =========================
# Fixed output envelope
# =========================
# Graph routing depends on ok: true/false

def ok_envelope( # Success response
    sql: str,
    columns: List[str],
    rows: List[Dict[str, Any]],
    row_count: int,
    execution_ms: int,
    explain_json: Any,
) -> Dict[str, Any]:
    return {
        "ok": True,
        "query": {"sql": sql, "params": {}},
        "data": {"columns": columns, "rows": rows, "row_count": row_count},
        "meta": {"execution_ms": execution_ms, "explain_json": explain_json},
        "error": None,
    }


def err_envelope( # Error response
    sql: str,
    error_type: str,
    message: str,
    code: Optional[str] = None,
    hint: Optional[str] = None,
    details: Optional[str] = None,
    explain_json: Any = None,
    execution_ms: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "ok": False,
        "query": {"sql": sql, "params": {}},
        "data": None,
        "meta": {"execution_ms": execution_ms, "explain_json": explain_json},
        "error": {
            "type": error_type,
            "code": code,
            "message": message,
            "hint": hint,
            "details": details,
        },
    }


# =========================
# Deterministic safety checks
# =========================

_FORBIDDEN = re.compile( # Forbidden operations
    r"\b("
    r"insert|update|delete|drop|alter|truncate|create|grant|revoke|comment|"
    r"vacuum|analyze|cluster|copy|do|call|execute|listen|notify|"
    r"security\s+definer|pg_sleep"
    r")\b",
    flags=re.IGNORECASE,
)
_SELECT_LIKE = re.compile(r"^\s*(with\b.*?\bselect\b|select\b)", flags=re.IGNORECASE | re.DOTALL) # SELECT-only check
_SEMICOLON = re.compile(r";") # Multi-statement block

def validate_sql_policy(sql: str, allow_multi_statement: bool) -> Tuple[bool, Optional[str]]:
    '''
    Policy validation function
    This runs before any DB call.

    If it fails → returns a POLICY_VIOLATION error
    The database is never touched.
    '''
    if not isinstance(sql, str) or not sql.strip():
        return False, "Empty SQL."
    if not _SELECT_LIKE.search(sql):
        return False, "Only SELECT queries are allowed (SELECT / WITH ... SELECT)."
    if _FORBIDDEN.search(sql):
        return False, "Forbidden operation detected (read-only queries only)."
    if not allow_multi_statement:
        # block multi-statements by disallowing semicolons (simple + effective for MVP)
        if _SEMICOLON.search(sql.strip().rstrip(";")):
            return False, "Multiple statements are not allowed."
    return True, None


def enforce_limit_wrapper(sql: str, max_rows: int) -> str:
    # Robust MVP approach: wrap as subquery and apply LIMIT outside.
    return f"SELECT * FROM ({sql}) AS _q LIMIT {int(max_rows)}"


# =========================
# Async DB Tool (pool)
# =========================

import asyncio
import asyncpg
import time
from typing import Any, Dict, List, Optional

class SupabaseDBToolAsync:
    def __init__(self, cfg: DBToolConfig):
        self.cfg = cfg
        self._pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()  # Prevent multiple simultaneous pool reconnects

    async def start(self) -> None:
        """Initialize the pool."""
        await self._create_pool()

    async def _create_pool(self):
        """Internal pool creation, with automatic SSL."""
        self._pool = await asyncpg.create_pool(
            dsn=self.cfg.database_url,
            min_size=1,
            max_size=5,
            ssl="require",
        )

    async def close(self) -> None:
        """Close pool if exists."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def _ensure_pool(self):
        """Check if pool exists, reconnect if necessary."""
        async with self._lock:
            if self._pool is None:
                await self._create_pool()

    async def run_sql(self, sql: str) -> Dict[str, Any]:
        t0 = time.time()

        ok, reason = validate_sql_policy(sql, self.cfg.allow_multi_statement)
        if not ok:
            return err_envelope(
                sql=sql,
                error_type="POLICY_VIOLATION",
                message=reason or "Policy violation",
                execution_ms=int((time.time() - t0) * 1000),
            )

        final_sql = enforce_limit_wrapper(sql, self.cfg.max_rows) if self.cfg.enforce_limit else sql

        for attempt in range(2):  # Retry once on connection issues
            await self._ensure_pool()  # Make sure pool exists
            try:
                async with self._pool.acquire() as conn:
                    async with conn.transaction():
                        await conn.execute(f"SET LOCAL statement_timeout = {int(self.cfg.statement_timeout_ms)}")
                        await conn.execute(f"SET LOCAL lock_timeout = {int(self.cfg.lock_timeout_ms)}")
                        await conn.execute(f"SET LOCAL idle_in_transaction_session_timeout = {int(self.cfg.idle_in_tx_timeout_ms)}")

                        explain_rows = await conn.fetch(f"EXPLAIN (FORMAT JSON) {final_sql}")
                        explain_json = explain_rows[0]["QUERY PLAN"] if explain_rows else None

                        data_rows = await conn.fetch(final_sql)

                        rows = [dict(r) for r in data_rows]
                        columns = list(rows[0].keys()) if rows else []
                        row_count = len(rows)

                        ms = int((time.time() - t0) * 1000)
                        return ok_envelope(
                            sql=final_sql,
                            columns=columns,
                            rows=rows,
                            row_count=row_count,
                            execution_ms=ms,
                            explain_json=explain_json,
                        )

            except asyncpg.exceptions.ConnectionDoesNotExistError as e:
                # Pool / connection was closed, retry once
                if attempt == 0:
                    await self.close()
                    await asyncio.sleep(0.1)
                    continue
                ms = int((time.time() - t0) * 1000)
                return err_envelope(
                    sql=final_sql,
                    error_type="INTERNAL_ERROR",
                    message=f"Connection lost: {e}",
                    execution_ms=ms,
                )
            except asyncpg.PostgresError as e:
                ms = int((time.time() - t0) * 1000)
                return err_envelope(
                    sql=final_sql,
                    error_type="SQL_ERROR",
                    code=getattr(e, "sqlstate", None),
                    message=str(e).strip(),
                    hint=getattr(e, "hint", None),
                    details=getattr(e, "detail", None),
                    execution_ms=ms,
                )
            except Exception as e:
                ms = int((time.time() - t0) * 1000)
                return err_envelope(
                    sql=final_sql,
                    error_type="INTERNAL_ERROR",
                    message=str(e),
                    execution_ms=ms,
                )




