import psycopg2
import json
from typing import Dict
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")


def get_db_schema_json(conn) -> Dict:
    """
    Fetch database schema from PostgreSQL (Supabase)
    Returns schema as a Python dict
    """
    query = """
    SELECT
        table_name,
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """

    schema = {}

    with conn.cursor() as cursor:
        cursor.execute(query)
        for table, column, dtype in cursor.fetchall():
            schema.setdefault(table, []).append({
                "column": column,
                "type": dtype
            })

    return schema


def load_schema_once() -> Dict:
    """
    Open DB connection → load schema ONCE → close connection
    """
    conn = None
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        schema = get_db_schema_json(conn)
        return schema

    finally:
        if conn is not None:
            conn.close()
            print("✅ Supabase DB connection closed")


# Manual test
if __name__ == "__main__":
    schema = load_schema_once()
    print(json.dumps(schema, indent=2))


