import asyncio
import os
from dotenv import load_dotenv

from src.langgraph.db_tool_node import DBToolConfig, SupabaseDBToolAsync

load_dotenv()

async def main():
    cfg = DBToolConfig(
        database_url=os.environ["SUPABASE_DB_URL"],
        max_rows=10,                # keep small so you SEE the limit working
        statement_timeout_ms=10_000,
        enforce_limit=True,
    )

    db_tool = SupabaseDBToolAsync(cfg)
    await db_tool.start()

    try:
        print("\n--- Test 1: valid query ---")
        result = await db_tool.run_sql("SELECT 1 AS ok")
        print(result)

        print("\n--- Test 2: invalid column (should fail EXPLAIN) ---")
        # customers exists in your schema; NotAColumn should fail with "undefined column" (42703)
        result = await db_tool.run_sql("SELECT NotAColumn FROM customers")
        print(result)

        print("\n--- Test 3: forbidden operation (should be blocked) ---")
        result = await db_tool.run_sql("DELETE FROM customers")
        print(result)

        print("\n--- Test 4: big table with enforced LIMIT ---")
        # order_details exists and is usually large
        result = await db_tool.run_sql("SELECT * FROM order_details")

        if result["ok"]:
            print("Rows returned:", result["data"]["row_count"])
            print("Columns:", result["data"]["columns"])
            # print first row sample
            print("First row:", result["data"]["rows"][0] if result["data"]["rows"] else None)
        else:
            print("Test 4 failed:")
            print("Type:", result["error"]["type"])
            print("Code:", result["error"]["code"])
            print("Message:", result["error"]["message"])

    finally:
        await db_tool.close()


if __name__ == "__main__":
    asyncio.run(main())

