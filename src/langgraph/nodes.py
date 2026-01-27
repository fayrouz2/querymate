# from src.agent.prompts import PROMPTS

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.agent.controller import run_master_agent
from src.agent.sql_generator_agent import generate_sql_from_nlq
from src.agent.sql_validator_agent import validate_sql_query
from src.agent.prompts import VISUALIZATION_PLANNER_PROMPT,  VISUALIZATION_CODE_PROMPT
from src.config import OPENAI_API_KEY
from .state import VizPlannerState

from langchain_core.messages import AIMessage
from .state import AgentState

def orchestrator_node(state: AgentState):
    """
    The Orchestrator: Controls the flow based on Repair Agent feedback.
    """
    if state.get("needs_clarification"):
        feedback = state.get("feedback_reason", "Could you provide more details?")
        return {
            "messages": [AIMessage(content=f"I need a bit more info: {feedback}")],
            "next_step": "end", # Stops the graph to wait for user
            "needs_clarification": False # Reset for next turn
        }

    if state.get("is_unsupported"):
        return {
            "messages": [AIMessage(content="I'm sorry, I can't perform that specific analysis on this database.")],
            "next_step": "end",
            "is_unsupported": False
        }

    response = run_master_agent(state["messages"])
    content = response.content.strip()

   
    if "[TRIGGER_SQL]" in content:
        next_step = "sql_generator"
    else:
        next_step = "end"

    return {
        "messages": [response],
        "next_step": next_step
    }

def sql_generator_node(state):
    """
    SQL Generator Node:
    Takes the latest user question and generates SQL.
    """
    # Get last user message
    user_message = state["messages"][-1].content

    # Generate SQL from NLQ
    sql_query = generate_sql_from_nlq(user_message)

    return {
        "sql_query": sql_query,
        "next_step": "sql_validator"
    }


def sql_validator_node(state):
    """
    SQL Validator Node:
    Validates the generated SQL query for safety.
    """
    sql_query = state.get("sql_query")

    if not sql_query:
        return {
            "is_valid": False,
            "validation_message": "No SQL query provided for validation",
            "next_step": "sql_generator"
        }

    is_valid, message = validate_sql_query(sql_query)

    if is_valid:
        return {
            "is_valid": True,
            "validation_message": message,
            "next_step": "execute_sql"
        }
    else:
        return {
            "is_valid": False,
            "validation_message": message,
            "next_step": "sql_generator"
        }
    

def visualization_planner_node(state: VizPlannerState) -> dict:
    """
    Node that generates a visualization plan using your VISUALIZATION_PLANNER_PROMPT.
    Returns:
      - messages: the AI response message (so it can be chained)
      - viz_plan: extracted content for easy downstream use
    """

    # 1) Build the LLM (GPT)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0, openai_api_key=OPENAI_API_KEY)

    # 2) System prompt (your prompt)
    system = SystemMessage(content=VISUALIZATION_PLANNER_PROMPT)

    # 3) Build a clear user payload from available state fields
    question = state.get("question", "")
    sql_query = state.get("sql_query", "")
    columns = state.get("columns", [])
    sample_rows = state.get("sample_rows", [])

    user_payload = (
        f"User question:\n{question}\n\n"
        f"SQL query (if available):\n{sql_query}\n\n"
        f"Columns (if available):\n{columns}\n\n"
        f"Sample rows (if available):\n{sample_rows}\n\n"
        "Return ONLY the visualization plan as the final answer."
    )

    human = HumanMessage(content=user_payload)

    # 4) If there are already messages in the state, keep them
    #    but always include system prompt first.
    prior_messages = state.get("messages") or []
    messages = [system] + prior_messages + [human]

    # 5) Call the model
    response = llm.invoke(messages)

    # 6) Return updates to the graph state
    return {
        "messages": [response],
        "viz_plan": response.content,
    }


def visualization_code_generator_node(state):
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0, openai_api_key=OPENAI_API_KEY)

    viz_plan = state.get("viz_plan", "")
    sample_rows = state.get("sample_rows", [])
    df_preview = sample_rows[:5] if sample_rows else []

    prompt = VISUALIZATION_CODE_PROMPT.format(
        viz_plan=viz_plan,
        df_preview=df_preview
    )

    system = SystemMessage(content="You generate Python Plotly visualization code only.")
    human = HumanMessage(content=prompt)

    prior_messages = state.get("messages") or []
    messages = [system] + prior_messages + [human]

    response = llm.invoke(messages)

    return {
        "messages": [response],
        "viz_code": response.content.strip()
    }