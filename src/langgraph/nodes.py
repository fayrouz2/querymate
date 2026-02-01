import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.agent.controller import run_master_agent
from src.agent.sql_generator_agent import generate_sql_from_nlq

from src.agent.prompts import VISUALIZATION_PLANNER_PROMPT,  VISUALIZATION_CODE_PROMPT
from src.config import OPENAI_API_KEY
from .state import VizPlannerState

from langchain_core.messages import AIMessage
from .state import AgentState
import json
from src.metadata.data_dictionary import DATA_DICTIONARY
from src.agent.prompts import REPAIR_SYSTEM_PROMPT
from src.agent.sql_validator_agent import repair_reasoning_engine
from src.database.db_tool import SupabaseDBToolAsync
from src.langgraph.state import GraphState

from typing import Dict, Any

from src.database.extract_db_result_preview import _extract_columns_and_sample_rows

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

    # if state.get("is_unsupported"):
    #     return {
    #         "messages": [AIMessage(content="I'm sorry, I can't perform that specific analysis on this database.")],
    #         "next_step": "end",
    #         "is_unsupported": False
    #     }
    if state.get("is_unsupported"):
    
        reason = state.get("feedback_reason", "")
        
      
        if "DELETE" in reason.upper() or "DROP" in reason.upper():
            user_msg = "I'm sorry, but for security reasons, I can only analyze data, not delete or modify it."
        elif "Max repair attempts" in reason:
            user_msg = "I apologize, I've run into a technical issue while processing this request and couldn't resolve it after several attempts."
        else:
          
            user_msg = "I'm sorry, I can't perform that specific analysis on this database with the information currently available."

        return {
            "messages": [AIMessage(content=user_msg)],
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
        "next_step": "db_tool"
    }

def visualization_planner_node(state: "VizPlannerState") -> dict:
    """
    Generates a visualization plan using VISUALIZATION_PLANNER_PROMPT.
    Reads query results from DB Tool output: state["db_result"].
    """

    # 0) Pull core fields
    question = state.get("question", "") or ""
    sql_query = state.get("sql_query", "") or ""

    db_result = state.get("db_result")

    # If DB tool didn't run or failed, do NOT crash.
    # Usually the graph should route here only when ok=True,
    # but we guard anyway (defensive programming).

    '''
    the return below 
    This is returned to the LangGraph runtime, not to a human, not directly to another agent.

    LangGraph will:

    1. Merge this into the shared state
    2. Then decide what node runs next based on your graph routing

    '''
    if not db_result:
        return {
            "viz_plan": "NO_VIZ\nreason: db_result missing (DB tool did not run).",
        } 

    if not db_result.get("ok"):
        # You can choose: either return a "no viz" plan or include error summary
        err = db_result.get("error") or {}
        return {
            "viz_plan": (
                "NO_VIZ\n"
                f"reason: db_error\n"
                f"error_type: {err.get('type')}\n"
                f"message: {err.get('message')}"
            )
        }

    # 1) Extract columns + sample rows from db_result
    columns, sample_rows = _extract_columns_and_sample_rows(db_result, max_sample=10)

    # 2) Build LLM
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0, openai_api_key=OPENAI_API_KEY)

    # 3) System prompt
    system = SystemMessage(content=VISUALIZATION_PLANNER_PROMPT)

    # 4) User payload (now grounded in db_result)
    # Optional: include row_count to help decide if aggregation is needed.
    row_count = (db_result.get("data") or {}).get("row_count")

    user_payload = (
        f"User question:\n{question}\n\n"
        f"SQL query:\n{sql_query}\n\n"
        f"Result columns:\n{columns}\n\n"
        f"Row count:\n{row_count}\n\n"
        f"Sample rows (up to 10):\n{sample_rows}\n\n"
        "Return ONLY the visualization plan as the final answer."
    )

    human = HumanMessage(content=user_payload)

    # 5) Keep prior messages if present (system always first)
    prior_messages = state.get("messages") or []
    messages = [system] + prior_messages + [human]

    # 6) Call model
    response = llm.invoke(messages)

    # 7) Update state
    return {
        "messages": [response],
        "viz_plan": response.content,
    }

# def visualization_planner_node(state: VizPlannerState) -> dict:
#     """
#     Node that generates a visualization plan using your VISUALIZATION_PLANNER_PROMPT.
#     Returns:
#       - messages: the AI response message (so it can be chained)
#       - viz_plan: extracted content for easy downstream use
#     """

#     # 1) Build the LLM (GPT)
#     model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
#     llm = ChatOpenAI(model=model_name, temperature=0, openai_api_key=OPENAI_API_KEY)

#     # 2) System prompt (your prompt)
#     system = SystemMessage(content=VISUALIZATION_PLANNER_PROMPT)

#     # 3) Build a clear user payload from available state fields
#     question = state.get("question", "")
#     sql_query = state.get("sql_query", "")
#     columns = state.get("columns", [])
#     sample_rows = state.get("sample_rows", [])

#     user_payload = (
#         f"User question:\n{question}\n\n"
#         f"SQL query (if available):\n{sql_query}\n\n"
#         f"Columns (if available):\n{columns}\n\n"
#         f"Sample rows (if available):\n{sample_rows}\n\n"
#         "Return ONLY the visualization plan as the final answer."
#     )

#     human = HumanMessage(content=user_payload)

#     # 4) If there are already messages in the state, keep them
#     #    but always include system prompt first.
#     prior_messages = state.get("messages") or []
#     messages = [system] + prior_messages + [human]

#     # 5) Call the model
#     response = llm.invoke(messages)

#     # 6) Return updates to the graph state
#     return {
#         "messages": [response],
#         "viz_plan": response.content,
#     }


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



def sql_repair_node(state: AgentState):
    """
    SQL Repair Node: Analyzes DB errors and decides the next step based on the Dictionary.
    """
    db_result = state.get("db_result")
    attempt = state.get("repair_attempt", 0)
    
    if attempt >= 3:
        return {
            "is_unsupported": True,
            "feedback_reason": "Max repair attempts reached.",
            "next_step": "orchestrator"
        }

    # Extract info from state
    error_data = db_result.get("error", {})
    failed_sql = db_result.get("query", {}).get("sql")
    user_intent = state["messages"][-1].content 

    decision = repair_reasoning_engine(
        intent=user_intent, 
        sql=failed_sql, 
        error_info=error_data, 
        dictionary=DATA_DICTIONARY # Pass as dict, not formatted string
    )
    
    action = decision.get("action")
    updates = {
        "needs_clarification": False,
        "is_unsupported": False,
        "feedback_reason": decision.get("reason")
    }

    # Routing Logic based on your architecture
    if action == "REPAIR":
        updates.update({
            "sql_query": decision.get("repaired_sql"),
            "repair_attempt": attempt + 1,
            "next_step": "db_tool"
        })
    elif action == "CLARIFY":
        updates.update({"needs_clarification": True, "next_step": "orchestrator"})
    else: # FAIL case
        updates.update({"is_unsupported": True, "next_step": "orchestrator"})

    return updates


def make_db_execute_node(db_tool: SupabaseDBToolAsync):
    """
    Factory so you can inject the running db_tool instance into the node.
    Use as a node in LangGraph: add_node("db_execute", make_db_execute_node(db_tool))
    """

    async def db_execute_node(state: GraphState) -> GraphState:
        sql = state.get("sql_query", "")

        # Ensure counters exist
        if "repair_count" not in state:
            state["repair_count"] = 0
        if "max_repairs" not in state:
            state["max_repairs"] = getattr(db_tool.cfg, "max_repairs", 2)

        result = await db_tool.run_sql(sql)
        state["db_result"] = result

        if not result.get("ok"):
            state["last_error"] = result.get("error") or {}
        else:
            state.pop("last_error", None)

        return state

    return db_execute_node