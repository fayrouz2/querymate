# from langchain_openai import ChatOpenAI
# from langchain_core.messages import SystemMessage
# from src.agent.prompts import PROMPTS


# src/langgraph/nodes.py
from src.agent.controller import run_master_agent

def orchestrator_node(state):
    """
    The Master Node: Calls the master agent function and routes the flow.
    """
    # 1. Call the Master Agent logic defined above
    response = run_master_agent(state["messages"])
    
    # 2. Extract content to check for triggers 
    
    content = response.content.strip()

    if content.startswith("[TRIGGER_SQL]"):
        next_step = "sql_generator"
    else:
        next_step = "end"

    return {
        "messages": [response],
        "next_step": next_step
           }

   