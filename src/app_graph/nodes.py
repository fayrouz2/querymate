import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.agent.controller import run_master_agent
from src.agent.sql_generator_agent import generate_sql_from_nl

from src.agent.prompts import VISUALIZATION_PLANNER_PROMPT,  VISUALIZATION_CODE_PROMPT
from src.config import OPENAI_API_KEY

from langchain_core.messages import AIMessage
from .state import AgentState
from src.metadata.data_dictionary import DATA_DICTIONARY
from src.agent.sql_validator_agent import repair_reasoning_engine
from src.database.db_tool import SupabaseDBToolAsync
from src.database.extract_db_result_preview import _extract_columns_and_sample_rows


def orchestrator_node(state: AgentState) -> dict:
    """
    The Orchestrator: Controls the flow based on Repair Agent feedback.
    """

    if (state.get("db_result") or {}).get("ok") and state.get("viz_code"):
        return {
            "next_step": "end"
        }

    if state.get("needs_clarification"):
        feedback = state.get("feedback_reason", "Could you provide more details?")
        return {
            "messages": [AIMessage(content=f"I need a bit more info: {feedback}")],
            "next_step": "end",
            "needs_clarification": False 
        }

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

  
    clean_content = content.replace("[NO_SQL]", "").replace("[TRIGGER_SQL]", "").strip()
    response.content = clean_content 
   

    if "[TRIGGER_SQL]" in content: 
        next_step = "sql_generator"
    else:
        next_step = "end"

    return {
        "messages": [response],
        "next_step": next_step
    }



def sql_generator_node(state: AgentState) -> dict:
    """
    SQL Generator Node:
    Takes the latest user question and generates SQL.
    """
    user_message = state["messages"][-1].content

    sql_query = generate_sql_from_nl(user_message)
    sql_query = (sql_query or "").strip().rstrip(";")

    return {
        "sql_query": sql_query,
        "next_step": "db_execute"
    }


def visualization_planner_node(state: AgentState) -> dict:
    """
    Generates a visualization plan using VISUALIZATION_PLANNER_PROMPT.
    Reads query results from DB Tool output: state["db_result"].
    """

    question = state.get("question", "") or ""
    sql_query = state.get("sql_query", "") or ""

    db_result = state.get("db_result")

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
        err = db_result.get("error") or {}
        return {
            "viz_plan": (
                "NO_VIZ\n"
                f"reason: db_error\n"
                f"error_type: {err.get('type')}\n"
                f"message: {err.get('message')}"
            )
        }

    columns, sample_rows = _extract_columns_and_sample_rows(db_result, max_sample=10)

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0, openai_api_key=OPENAI_API_KEY)

    system = SystemMessage(content=VISUALIZATION_PLANNER_PROMPT)

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

    prior_messages = state.get("messages") or []
    messages = [system] + prior_messages + [human]

    response = llm.invoke(messages)

    return {
        "messages": [response],
        "viz_plan": response.content,
        "columns": columns,
        "sample_rows": sample_rows,
    }


def visualization_code_generator_node(state: AgentState) -> dict:
    """
    Generates Python Plotly code based on the visualization plan.
    Reads from state["viz_plan"] and state["sample_rows"].
    """
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0, openai_api_key=OPENAI_API_KEY)

    viz_plan = state.get("viz_plan", "")
    sample_rows = state.get("sample_rows", [])
    
    print("ROWS:", len(sample_rows))
    print("COLUMNS:", state.get("columns")) 

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
        "messages": ["I've generated a chart based on your data!"],
        "viz_code": response.content.strip()
    }


def sql_repair_node(state: AgentState) -> dict:
    """
    SQL Repair Node: Analyzes DB errors and decides the next step based on the Dictionary.
    """
    db_result = state.get("db_result")
    attempt = state.get("repair_count", 0)
    
    if attempt >= 3:
        return {
            "is_unsupported": True,
            "feedback_reason": "Max repair attempts reached.",
            "next_step": "orchestrator"
        }

    error_data = db_result.get("error", {})
    failed_sql = db_result.get("query", {}).get("sql")
    user_intent = state["messages"][-1].content 

    decision = repair_reasoning_engine(
        intent=user_intent, 
        sql=failed_sql, 
        error_info=error_data, 
        dictionary=DATA_DICTIONARY 
    )
    
    action = decision.get("action")
    updates = {
        "needs_clarification": False,
        "is_unsupported": False,
        "feedback_reason": decision.get("reason")
    }

    if action == "REPAIR":
        updates.update({
            "sql_query": decision.get("repaired_sql"),
            "repair_count": attempt + 1,
            "next_step": "db_execute"
        })
    elif action == "CLARIFY":
        updates.update({"needs_clarification": True, "next_step": "orchestrator"})
    else:
        updates.update({"is_unsupported": True, "next_step": "orchestrator"})

    return updates


import asyncio

def make_db_execute_node(db_tool: SupabaseDBToolAsync):

    async def db_execute_node(state: AgentState) -> AgentState:
        sql = state.get("sql_query", "") or ""

        if "repair_count" not in state:
            state["repair_count"] = 0
        if "max_repairs" not in state:
            state["max_repairs"] = getattr(db_tool.cfg, "max_repairs", 2)

        result = await db_tool.run_sql(sql)

        state["db_result"] = result

        print("DB_OK:", result.get("ok"))
        print("DB_ERROR:", result.get("error"))

        if result.get("ok"):
            data = result.get("data") or {}
            state["columns"] = data.get("columns", [])
            state["sample_rows"] = (data.get("rows") or [])[:20]

        if not result.get("ok"):
            state["last_error"] = result.get("error") or {}
        else:
            state.pop("last_error", None)

        return state

    return db_execute_node
