from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState

from .nodes import (
    orchestrator_node, 
    sql_generator_node, 
    make_db_execute_node, 
    sql_repair_node, 
    visualization_planner_node, 
    visualization_code_generator_node
)

# --- Routing Helpers ---

def route_after_db(state: AgentState):
    db_res = state.get("db_result")
    
    # Safety check: if db_res is None, something went wrong in the transition
    if not db_res:
        return "stop" 

    if db_res.get("ok"):
        return "viz"
    
    current_count = state.get("repair_count", 0)
    max_limit = state.get("max_repairs") if state.get("max_repairs") is not None else 3
    
    if current_count >= max_limit:
        return "stop" 
        
    return "repair"

def route_after_repair(state: AgentState):
    # Ensure we only go back to db_execute if a new query was actually generated
    return state.get("next_step", "orchestrator")

# --- Workflow Builder ---

# --- 1. Remove the conditional logic from orchestrator for now to simplify
# --- 2. Fix the SQL Generator -> DB Execute bridge

# Inside src/app_graph/workflow.py

def build_querymate_workflow(db_tool_instance, checkpointer=True):
    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("sql_generator", sql_generator_node)
    workflow.add_node("db_execute", make_db_execute_node(db_tool_instance))
    workflow.add_node("sql_repair", sql_repair_node)
    workflow.add_node("viz_planner", visualization_planner_node)
    workflow.add_node("viz_generator", visualization_code_generator_node)

    # 2. Set Entry
    workflow.set_entry_point("orchestrator")

    # 3. Orchestrator Logic
    workflow.add_conditional_edges(
        "orchestrator",
        lambda state: state.get("next_step", "end"),
        {"sql_generator": "sql_generator", "end": END}
    )

    # 4. THE FIX: Force SQL Generator to always go to DB Execute
    # Remove any conditional edges you have for "sql_generator"
    workflow.add_edge("sql_generator", "db_execute")

    # 5. DB Execute Logic
    workflow.add_conditional_edges(
        "db_execute",
        route_after_db, # This function checks if result is 'ok'
        {
            "viz": "viz_planner",
            "repair": "sql_repair",
            "stop": "orchestrator"
        }
    )

    # 6. Repair Logic (Loop back to EXECUTE, not back to Generator)
    workflow.add_edge("sql_repair", "db_execute") 

    # 7. Viz Logic
    workflow.add_edge("viz_planner", "viz_generator")
    workflow.add_edge("viz_generator", "orchestrator")

    return workflow.compile(checkpointer=MemorySaver() if checkpointer else None)