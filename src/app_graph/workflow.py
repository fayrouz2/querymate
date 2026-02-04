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

def route_after_db(state: AgentState):
    """
    Decides the next path based on DB Tool execution results.
    """
    db_res = state.get("db_result") or {}
    
    if db_res.get("ok"):
        return "viz"
    
    current_count = state.get("repair_count", 0)
    max_limit = state.get("max_repairs") if state.get("max_repairs") is not None else 3
    
    if current_count >= max_limit:
        return "stop" 
        
    return "repair"

def route_after_repair(state: AgentState):
    """
    Determines if the repair was successful or if clarification is needed.
    """
    return state.get("next_step", "orchestrator")


def build_querymate_workflow(db_tool_instance, checkpointer=True):
    workflow = StateGraph(AgentState)

    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("sql_generator", sql_generator_node)
    workflow.add_node("db_execute", make_db_execute_node(db_tool_instance))
    workflow.add_node("sql_repair", sql_repair_node)
    workflow.add_node("viz_planner", visualization_planner_node)
    workflow.add_node("viz_generator", visualization_code_generator_node)

    workflow.set_entry_point("orchestrator")
    
    workflow.add_edge("sql_generator", "db_execute")

    workflow.add_conditional_edges(
        "db_execute",
        route_after_db,
        {
            "viz": "viz_planner",
            "repair": "sql_repair",
            "stop": "orchestrator"
        }
    )

    workflow.add_conditional_edges(
        "sql_repair",
        route_after_repair,
        {
            "db_execute": "db_execute",
            "orchestrator": "orchestrator"
        }
    )

    workflow.add_edge("viz_planner", "viz_generator")
    workflow.add_edge("viz_generator", "orchestrator") 

    workflow.add_conditional_edges(
        "orchestrator",
        lambda state: state.get("next_step", "end"), 
        {
            "sql_generator": "sql_generator",
            "end": END
        }
    )

    return workflow.compile(checkpointer=MemorySaver() if checkpointer else None)