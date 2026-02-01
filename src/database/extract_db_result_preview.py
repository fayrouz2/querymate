from typing import Any, Dict, List, Optional
import os

def _extract_columns_and_sample_rows(db_result: Dict[str, Any], max_sample: int = 10):
    """
    Extract columns + a small sample from the DB tool envelope.
    Expected shape (example):
      db_result = {
        "ok": True,
        "query": {"sql": "..."},
        "data": {"columns": [...], "rows": [...], "row_count": n, "meta": {...}},
        "error": None
      }
    """
    data = (db_result or {}).get("data") or {}
    columns = data.get("columns") or []
    rows = data.get("rows") or []
    sample_rows = rows[:max_sample]
    return columns, sample_rows