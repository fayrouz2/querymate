# test_db_tool.py
import asyncio
import os
from dotenv import load_dotenv
from src.langgraph.db_tool_node import SupabaseDBToolAsync, DBToolConfig

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    raise ValueError("SUPABASE_DB_URL not found in environment")

# ----------------------------
# Async test function
# ----------------------------
async def test_db_tool():
    # 1) Create config & DB tool instance
    cfg = DBToolConfig(database_url=DB_URL)
    db_tool = SupabaseDBToolAsync(cfg)

    # 2) Start the async connection pool
    await db_tool.start()

    # 3) Run a simple test query
    sql = "SELECT 1 AS test_val"
    result = await db_tool.run_sql(sql)

    print("Result Envelope:")
    print(result)

    # 4) Close the pool
    await db_tool.close()


# ----------------------------
# Run test
# ----------------------------
if __name__ == "__main__":
    asyncio.run(test_db_tool())

