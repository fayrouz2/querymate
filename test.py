from langchain_core.messages import HumanMessage, AIMessage
from src.agent.controller import run_master_agent

def run_terminal_chat():
    print("--- QueryMate Controller Agent Test ---")
    print("Type 'exit' or 'quit' to stop.")

    messages = []  # conversation history

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # Add user message
        messages.append(HumanMessage(content=user_input))

        # Call your controller agent directly
        response = run_master_agent(messages)

        # Save assistant response
        messages.append(response)

        # Print response (clean token if needed)
        content = response.content
        clean = (
            content.replace("[TRIGGER_SQL]", "")
                   .replace("[NO_SQL]", "")
                   .strip()
        )

        print(f"\nQueryMate: {clean}")

if _name_ == "_main_":
    run_terminal_chat()
