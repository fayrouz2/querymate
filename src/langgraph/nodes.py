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

   
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .state import VizPlannerState
from src.agent.prompts import PROMPTS


def visualization_planner_node(state: VizPlannerState) -> dict:
    """
    Node that generates a visualization plan using your VISUALIZATION_PLANNER_PROMPT.
    Returns:
      - messages: the AI response message (so it can be chained)
      - viz_plan: extracted content for easy downstream use
    """

    # 1) Build the LLM (GPT)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0)

    # 2) System prompt (your prompt)
    system = SystemMessage(content=PROMPTS["VISUALIZATION_PLANNER_PROMPT"])

    # 3) Build a clear user payload from available state fields
    question = state.get("question", "")
    sql_query = state.get("sql_query", "")
    columns = state.get("columns", [])
    sample_rows = state.get("sample_rows", [])

    user_payload = (
        "You are a visualization planner.\n\n"
        f"User question:\n{question}\n\n"
        f"SQL query (if available):\n{sql_query}\n\n"
        f"Columns (if available):\n{columns}\n\n"
        f"Sample rows (if available):\n{sample_rows}\n\n"
        "Return ONLY the visualization plan as the final answer."
    )

    human = HumanMessage(content=user_payload)

    # 4) If there are already messages in the state, keep them
    #    but always include system prompt first.
    prior_messages = state.get("messages", [])
    messages = [system] + prior_messages + [human]

    # 5) Call the model
    response = llm.invoke(messages)

    # 6) Return updates to the graph state
    return {
        "messages": [response],
        "viz_plan": response.content,
    }
