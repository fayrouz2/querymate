import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.agent.controller import run_master_agent
from src.agent.sql_generator_agent import generate_sql_from_nl

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
from src.app_graph.state import GraphState

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





####updated orecstrotr node async22


# async def orchestrator_node(state: AgentState):
#     """
#     The Orchestrator: Controls the flow based on technical feedback 
#     and presents final results to the user.
#     """
#     # 1. Handle Clarification Requests (From Repair Agent)
#     if state.get("needs_clarification"):
#         feedback = state.get("feedback_reason", "Could you provide more details?")
#         return {
#             "messages": [AIMessage(content=f"I need a bit more info: {feedback}")],
#             "next_step": "end",
#             "needs_clarification": False
#         }

#     # 2. Handle Errors or Security Blocks (From DB Tool/Repair Agent)
#     if state.get("is_unsupported"):
#         reason = state.get("feedback_reason", "")
        
#         # Specific check for your DB Tool's Policy Violation
#         if "POLICY_VIOLATION" in reason.upper() or "Security" in reason:
#             user_msg = "For security reasons, I can only analyze data. I am not allowed to perform modifications or use forbidden commands."
#         elif "Max repair attempts" in reason:
#             user_msg = "I've tried to resolve the technical issues with this query several times but was unsuccessful. Could you try rephrasing your question?"
#         else:
#             user_msg = "I'm sorry, I can't perform that specific analysis on this database with the information currently available."

#         return {
#             "messages": [AIMessage(content=user_msg)],
#             "next_step": "end",
#             "is_unsupported": False 
#         }
    

#     # 3. Handle Success: Presentation Phase
#     # Check if we have a successful result from the DB or Viz agents
#     # FIX: Explicitly check that db_res is not None before calling .get()
#     db_res = state.get("db_result")
    
#     if db_res is not None and isinstance(db_res, dict) and db_res.get("ok"):
#         # Access data safely
#         row_count = db_res.get("data", {}).get("row_count", 0)
#         success_msg = f"I've analyzed the data ({row_count} records found) and prepared the results for you below."
        
#         return {
#             "messages": [AIMessage(content=success_msg)],
#             "next_step": "end" # End the technical flow and show the result
#         }

#     # 4. Standard Flow: Initial Request Handling
#     # Use await if run_master_agent is an LLM call
#     response = await run_master_agent(state["messages"])
#     content = response.content.strip()

#     if "[TRIGGER_SQL]" in content:
#         next_step = "sql_generator"
#     else:
#         next_step = "end"

#     return {
#         "messages": [response],
#         "next_step": next_step
#     }



# async def orchestrator_node(state: AgentState):
#     """
#     The Orchestrator: Controls the flow based on technical feedback 
#     and presents final results to the user.
#     """
#     # 1. Handle Clarification Requests (From Repair Agent)
#     if state.get("needs_clarification"):
#         feedback = state.get("feedback_reason", "Could you provide more details?")
#         return {
#             "messages": [AIMessage(content=f"I need a bit more info: {feedback}")],
#             "next_step": "end",
#             "needs_clarification": False
#         }

#     # 2. Handle Errors or Security Blocks (From DB Tool/Repair Agent)
#     if state.get("is_unsupported"):
#         reason = state.get("feedback_reason", "")
        
#         # Specific check for your DB Tool's Policy Violation
#         if "POLICY_VIOLATION" in reason.upper() or "Security" in reason:
#             user_msg = "For security reasons, I can only analyze data. I am not allowed to perform modifications or use forbidden commands."
#         elif "Max repair attempts" in reason:
#             user_msg = "I've tried to resolve the technical issues with this query several times but was unsuccessful. Could you try rephrasing your question?"
#         else:
#             user_msg = "I'm sorry, I can't perform that specific analysis on this database with the information currently available."

#         return {
#             "messages": [AIMessage(content=user_msg)],
#             "next_step": "end",
#             "is_unsupported": False 
#         }
    

#     # 3. Handle Success: Presentation Phase
#     # Check if we have a successful result from the DB or Viz agents
#     # FIX: Explicitly check that db_res is not None before calling .get()
#     db_res = state.get("db_result")
    
#     if db_res is not None and isinstance(db_res, dict) and db_res.get("ok"):
#         # Access data safely
#         row_count = db_res.get("data", {}).get("row_count", 0)
#         success_msg = f"I've analyzed the data ({row_count} records found) and prepared the results for you below."
        
#         return {
#             "messages": [AIMessage(content=success_msg)],
#             "next_step": "end" # End the technical flow and show the result
#         }




def sql_generator_node(state):
    """
    SQL Generator Node:
    Takes the latest user question and generates SQL.
    """
    # Get last user message
    user_message = state["messages"][-1].content

    # Generate SQL from NL
    sql_query = generate_sql_from_nl(user_message)

    return {
        "sql_query": sql_query,
        "next_step": "db_execute"
    }

# async def sql_generator_node(state: AgentState):
#     """ SQL Generator Node:
#       Takes the latest user question and generates SQL.
#       """
#     user_message = state["messages"][-1].content
    
#     # Ensure generate_sql_from_nl is async or wrapped
#     sql_query = await generate_sql_from_nl(user_message) 

#     return {
#         "sql_query": sql_query,
#         "next_step": "db_execute"
#     }

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

#
# async def visualization_planner_node(state: AgentState) -> dict:
#     db_result = state.get("db_result")
    
#     if not db_result or not db_result.get("ok"):
#         return {"viz_plan": "NO_VIZ - DB result missing or failed."}

#     columns, sample_rows = _extract_columns_and_sample_rows(db_result, max_sample=10)
    
#     model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
#     llm = ChatOpenAI(model=model_name, temperature=0, openai_api_key=OPENAI_API_KEY)

#     system = SystemMessage(content=VISUALIZATION_PLANNER_PROMPT)
#     user_payload = f"User question: {state.get('messages')[0].content}\nColumns: {columns}\nSample: {sample_rows}"
    
#     # Use .ainvoke() for async execution
#     response = await llm.ainvoke([system] + state["messages"] + [HumanMessage(content=user_payload)])

#     return {
#         "messages": [response],
#         "viz_plan": response.content,
#         "columns": columns,
#         "sample_rows": sample_rows
#     }





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



## async generation of visualization code node

# async def visualization_code_generator_node(state: AgentState):
#     model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
#     llm = ChatOpenAI(model=model_name, temperature=0, openai_api_key=OPENAI_API_KEY)

#     prompt = VISUALIZATION_CODE_PROMPT.format(
#         viz_plan=state.get("viz_plan", ""),
#         df_preview=state.get("sample_rows", [])[:5]
#     )

#     # Use .ainvoke() here as well
#     response = await llm.ainvoke([SystemMessage(content="Generate Plotly code."), HumanMessage(content=prompt)])

#     return {
#         "messages": [response],
#         "viz_code": response.content.strip(),
#         "next_step": "orchestrator" # Route back to present the result
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

#updated Repaire for DB tools

# async def sql_repair_node(state: AgentState):
#     """
#     Analyzes DB errors and decides whether to repair, clarify, or fail.
#     Integrated with SupabaseDBToolAsync envelope structure.
#     """
#     # 1. Get the envelope from your DB Tool
#     db_res = state.get("db_result", {})
#     error_data = db_res.get("error") or {}
#     failed_sql = db_res.get("query", {}).get("sql", "")

#     # 2. IMMEDIATE GATE: Handle Policy Violations
#     # If the DB Tool blocked the query (DELETE, UPDATE, etc.), don't try to repair it.
#     if error_data.get("type") == "POLICY_VIOLATION":
#         return {
#             "next_step": "orchestrator",
#             "is_unsupported": True,
#             "feedback_reason": f"Security Policy Violation: {error_data.get('message')}"
#         }

#     # 3. Call Reasoning Engine for technical errors (SQL_ERROR, etc.)
#     # We pass the full error_data so the LLM can see 'hint' and 'details'
#     decision = await repair_reasoning_engine(
#         intent=state["messages"][-1].content,
#         sql=failed_sql,
#         error_info=error_data,
#         dictionary=DATA_DICTIONARY
#     )

#     # 4. Process Decision & Prepare Updates
#     action = decision.get("action")  # Expected: "REPAIR", "CLARIFY", "FAIL"
    
#     # We increment the count here to ensure the DB Tool's circuit breaker works
#     current_count = state.get("repair_count", 0)
    
#     updates = {
#         "feedback_reason": decision.get("reason"),
#         "repair_count": current_count + 1 
#     }

#     if action == "REPAIR":
#         updates["sql_query"] = decision.get("repaired_sql")
#         updates["next_step"] = "db_execute"  # Matches your node name
    
#     elif action == "CLARIFY":
#         updates["next_step"] = "orchestrator"
#         updates["needs_clarification"] = True
        
#     else:  # FAIL or unrecognized action
#         updates["next_step"] = "orchestrator"
#         updates["is_unsupported"] = True

#     return updates

 


# def make_db_execute_node(db_tool: SupabaseDBToolAsync):
#     """
#     Factory so you can inject the running db_tool instance into the node.
#     Use as a node in LangGraph: add_node("db_execute", make_db_execute_node(db_tool))
#     """

#     def db_execute_node(state: GraphState) -> GraphState:
#         sql = state.get("sql_query", "")

#         # Ensure counters exist
#         if "repair_count" not in state:
#             state["repair_count"] = 0
#         if "max_repairs" not in state:
#             state["max_repairs"] = getattr(db_tool.cfg, "max_repairs", 2)

#         result = db_tool.run_sql(sql)
#         state["db_result"] = result

#         if not result.get("ok"):
#             state["last_error"] = result.get("error") or {}
#         else:
#             state.pop("last_error", None)

#         return state

#     return db_execute_node


import asyncio

def make_db_execute_node(db_tool: SupabaseDBToolAsync):
    """
    Factory to inject the async db_tool into a synchronous LangGraph node.
    """

    def db_execute_node(state: AgentState) -> AgentState:
        sql = state.get("sql_query", "")

        # Ensure counters exist
        if "repair_count" not in state:
            state["repair_count"] = 0
        if "max_repairs" not in state:
            state["max_repairs"] = getattr(db_tool.cfg, "max_repairs", 2)

        # --- SYNC BRIDGE ---
        # Because db_tool.run_sql is async and this node is sync, 
        # we must force it to run and wait for the result.
        try:
            # Try to get the existing loop (common in some environments)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If a loop is already running, we use a future to wait
                result = asyncio.run_coroutine_threadsafe(db_tool.run_sql(sql), loop).result()
            else:
                result = loop.run_until_complete(db_tool.run_sql(sql))
        except RuntimeError:
            # If no loop exists at all (standard for simple sync main.py), we create a new one
            result = asyncio.run(db_tool.run_sql(sql))
        # --------------------

        state["db_result"] = result

        # Now 'result' is a real dictionary, so .get() will work!
        if not result.get("ok"):
            state["last_error"] = result.get("error") or {}
        else:
            state.pop("last_error", None)

        return state

    return db_execute_node