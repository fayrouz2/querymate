from langchain_core.messages import HumanMessage, AIMessage
from src.agent.controller import run_master_agent

# def run_terminal_chat():
#     print("--- QueryMate Controller Agent Test ---")
#     print("Type 'exit' or 'quit' to stop.")

#     messages = []  # conversation history

#     while True:
#         user_input = input("\nUser: ")
#         if user_input.lower() in ["exit", "quit"]:
#             break

#         # Add user message
#         messages.append(HumanMessage(content=user_input))

#         # Call your controller agent directly
#         response = run_master_agent(messages)

#         # Save assistant response
#         messages.append(response)

#         # Print response (clean token if needed)
#         content = response.content
#         clean = (
#             content.replace("[TRIGGER_SQL]", "")
#                    .replace("[NO_SQL]", "")
#                    .strip()
#         )

#         print(f"\nQueryMate: {clean}")

# if _name_ == "_main_":
#     run_terminal_chat()

import sys
import os
import json
from langchain_core.messages import HumanMessage

# Ensure access to the project root directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.langgraph.nodes import sql_repair_node, orchestrator_node

def run_test_scenario(description, state):
    """Helper function to run and print test results"""
    print(f"\n>>> SCENARIO: {description}")
    print(f"Current Attempt: {state.get('repair_attempt', 0)}")
    
    # Run the Repair Node
    output = sql_repair_node(state)
    
    print(f"Decision Reason: {output.get('feedback_reason')}")
    print(f"Action Taken: {'REPAIR' if output.get('sql_query') else 'ROUTING'}")
    print(f"Next Agent: {output.get('next_step')}")
    
    # If it goes to the Orchestrator, show the final message to user
    if output.get('next_step') == "orchestrator":
        # Simulate Orchestrator receiving this state
        orch_output = orchestrator_node({**state, **output})
        print(f"Orchestrator to User: {orch_output['messages'][-1].content}")
    
    return output

def test_repair_agent_capabilities():
    print("=== Testing SQL Repair & Reasoning Agent Capabilities ===")

    # CASE 1: REPAIR (Synonym Resolution)
    # User uses 'client' (synonym) instead of 'contact_name'
    repair_case = {
        "messages": [HumanMessage(content="Show me client names from London")],
        "sql_query": "SELECT client_name FROM customers WHERE city = 'London'",
        "db_result": {
            "ok": False,
            "error": {"message": "column 'client_name' does not exist", "hint": "Check synonyms"},
            "query": {"sql": "SELECT client_name FROM customers WHERE city = 'London'"}
        },
        "repair_attempt": 0
    }
    run_test_scenario("REPAIR (Synonym: client -> contact_name)", repair_case)

    # CASE 2: CLARIFICATION (Ambiguity)
    # User intent 'sales' is ambiguous in the Data Dictionary
    clarify_case = {
        "messages": [HumanMessage(content="Show me sales for beverages")],
        "sql_query": "SELECT unit_price FROM products WHERE category_id = 1",
        "db_result": {
            "ok": False,
            "error": {"message": "Semantic mismatch: 'sales' is ambiguous", "hint": "Multiple matches found"},
            "query": {"sql": "SELECT unit_price FROM products WHERE category_id = 1"}
        },
        "repair_attempt": 0
    }
    run_test_scenario("CLARIFICATION (Ambiguity: 'sales' could be price or quantity)", clarify_case)

    # CASE 3: UNSUPPORTED (Security/Scope)
    # User tries to delete data (Unsupported operation)
    unsupported_case = {
        "messages": [HumanMessage(content="Delete all customers from France")],
        "sql_query": "DELETE FROM customers WHERE country = 'France'",
        "db_result": {
            "ok": False,
            "error": {"message": "Permission denied: DELETE not allowed", "hint": "Only SELECT is supported"},
            "query": {"sql": "DELETE FROM customers WHERE country = 'France'"}
        },
        "repair_attempt": 0
    }
    run_test_scenario("UNSUPPORTED (Safety: Blocking DELETE request)", unsupported_case)

    # CASE 4: MAX ATTEMPTS REACHED
    # Verifying the 3-round limit
    limit_case = repair_case.copy()
    limit_case["repair_attempt"] = 3
    run_test_scenario("MAX ATTEMPTS (Enforcing the 3-round limit circuit breaker)", limit_case)

if __name__ == "__main__":
    test_repair_agent_capabilities()