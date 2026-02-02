# import os
# from src.database.db_tool import SupabaseDBToolAsync, DBToolConfig
# from src.app_graph.workflow import build_querymate_workflow
# from langchain_core.messages import HumanMessage

# def test_querymate():
#     # 1. Setup DB Config
#     cfg = DBToolConfig(
#         database_url="postgresql://postgres.mifszuwhtketjxkqgdji:Northwind2026%21@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require",
#         max_repairs=3 
#     )
#     db_tool = SupabaseDBToolAsync(cfg)

#     # Note: If your SupabaseDBToolAsync is still an "Async" class, 
#     # you might need to run its start/close in a small bridge, 
#     # but for the Graph itself, we use synchronous invoke.
    
#     try:
#         # 2. Build the Compiled Graph (Synchronous version)
#         app = build_querymate_workflow(db_tool)

#         # 3. Define the Initial State
#         initial_state = {
#             "messages": [HumanMessage(content="Show me a bar chart of total donations per month.")],
#             "repair_count": 0,
#             "next_step": "",
#             "max_repairs": 3
#         }

#         # 4. Run the Workflow (Synchronous .invoke)
#         # We add recursion_limit here to catch loops early without crashing the PC
#         config = {
#             "configurable": {"thread_id": "test_session_001"},
#             "recursion_limit": 40 
#         }
        
#         print("--- Starting QueryMate Workflow (Sync Mode) ---")
#         # Use .invoke() instead of await .ainvoke()
#         result = app.invoke(initial_state, config=config)

#         # 5. Inspect Final Results
#         print("\n--- Final Results ---")
#         print(f"SQL Generated: {result.get('sql_query')}")
#         print(f"Repair Attempts: {result.get('repair_count')}")
#         print(f"Viz Plan: {result.get('viz_plan')}")
        
#         if result.get('viz_code'):
#             print("--- Generated Plotly Code ---")
#             print(result.get('viz_code'))

#     except Exception as e:
#         print(f"An error occurred during execution: {e}")

# if __name__ == "__main__":
#     test_querymate()



import os
import asyncio  # Only used for the DB start/stop bridge
from src.database.db_tool import SupabaseDBToolAsync, DBToolConfig
from src.app_graph.workflow import build_querymate_workflow
from langchain_core.messages import HumanMessage

def run_chat_session():
    # 1. Setup DB Config
    cfg = DBToolConfig(
        database_url="postgresql://postgres.mifszuwhtketjxkqgdji:Northwind2026%21@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require",
        max_repairs=3 
    )
    db_tool = SupabaseDBToolAsync(cfg)
    
    # Bridge: Start the async DB pool before entering the sync loop
    asyncio.run(db_tool.start())
    
    try:
        # 2. Build the Compiled Graph (Sync version)
        app = build_querymate_workflow(db_tool)

        # 3. Chat Configuration
        # 'thread_id' allows the AI to remember your previous messages
        config = {
            "configurable": {"thread_id": "session_test_001"},
            "recursion_limit": 40 
        }

        print("--- QueryMate Live Chat Started ---")
        print("Commands: 'exit' to quit, 'clear' to reset memory\n")

        while True:
            # 4. Get User Input
            user_input = input("You: ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Closing QueryMate session...")
                break
            
            if user_input.lower() == "clear":
                config["configurable"]["thread_id"] += "_new"
                print("Memory cleared!")
                continue

            # 5. Define Initial State for this turn
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "repair_count": 0,
                "max_repairs": 3,
                "next_step": ""
            }

            # 6. Run the Workflow
            try:
                # Synchronous call
                result = app.invoke(initial_state, config=config)

                # 7. Show Output
                final_ai_msg = result["messages"][-1].content
                print(f"\nQueryMate: {final_ai_msg}")

                # Optional logs to see if agents triggered
                if result.get('sql_query'):
                    print(f"   [Log] SQL generated: {result.get('sql_query')}")
                if result.get('viz_code'):
                    print(f"   [Log] Visualization created.")
                
                print("-" * 30)

            except Exception as e:
                print(f"\n[System Error]: {e}")

    finally:
        # Bridge: Always close the DB pool on exit
        asyncio.run(db_tool.close())

if __name__ == "__main__":
    run_chat_session()