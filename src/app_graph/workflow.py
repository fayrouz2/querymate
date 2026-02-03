

# from langgraph.graph import StateGraph
# from langgraph.checkpoint.memory import MemorySaver

# from .state import VizPlannerState
# from .nodes import visualization_planner_node, visualization_code_generator_node
# from .state import GraphState




# def build_visualization_planner_graph(checkpointer=True): #TODO: change graph name after adding other nodes
#     graph = StateGraph(VizPlannerState)

#     graph.add_node("viz_planner", visualization_planner_node)
#     graph.add_node("viz_code_generator", visualization_code_generator_node)

#     graph.set_entry_point("viz_planner")
#     graph.add_edge("viz_planner", "viz_code_generator")
#     graph.set_finish_point("viz_code_generator")

#     if checkpointer:
#         return graph.compile(checkpointer=MemorySaver())
#     else:
#         return graph.compile(checkpointer=None)


# viz_graph = build_visualization_planner_graph()

# # =========================
# # Routing helpers (LangGraph)
# # =========================
# def route_after_db(state: GraphState) -> str:
#     """
#     Conditional edge router after DB execution.
#     Returns one of: "viz" | "repair" | "stop"
#     """
#     db_result = state.get("db_result") or {}
#     if db_result.get("ok") is True:
#         return "viz"

#     # If failed, check retry budget
#     repair_count = int(state.get("repair_count", 0))
#     max_repairs = int(state.get("max_repairs", 2))
#     if repair_count >= max_repairs:
#         return "stop"

#     return "repair"







from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Importing the nodes and the unified state
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
    """
    Decides the next path based on DB Tool execution results.
    """
    db_res = state.get("db_result") or {}
    
    # SUCCESS: Go to Visualization
    if db_res.get("ok"):
        return "viz"
    
    # FAILURE: Check retry budget
    current_count = state.get("repair_count", 0)
    # Defaulting to 3 if max_repairs is None to avoid TypeError
    max_limit = state.get("max_repairs") if state.get("max_repairs") is not None else 3
    
    if current_count >= max_limit:
        return "stop" 
        
    return "repair"

def route_after_repair(state: AgentState):
    """
    Determines if the repair was successful or if clarification is needed.
    """
    return state.get("next_step", "orchestrator")

# --- Workflow Builder (Synchronous) ---

def build_querymate_workflow(db_tool_instance, checkpointer=True):
    # Removed 'async' from the function definition
    workflow = StateGraph(AgentState)

    # 1. Add all Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("sql_generator", sql_generator_node)
    workflow.add_node("db_execute", make_db_execute_node(db_tool_instance))
    workflow.add_node("sql_repair", sql_repair_node)
    workflow.add_node("viz_planner", visualization_planner_node)
    workflow.add_node("viz_generator", visualization_code_generator_node)

    # 2. Define the Entry and Primary Flow
    workflow.set_entry_point("orchestrator")
    
    # Static edge: Orchestrator always starts with the SQL Generator 
    # (The node itself will decide if it needs to skip to 'end')
    workflow.add_edge("sql_generator", "db_execute")

    # 3. Decision after DB execution
    workflow.add_conditional_edges(
        "db_execute",
        route_after_db,
        {
            "viz": "viz_planner",
            "repair": "sql_repair",
            "stop": "orchestrator"
        }
    )

    # 4. Decision after Repair Agent
    workflow.add_conditional_edges(
        "sql_repair",
        route_after_repair,
        {
            "db_execute": "db_execute",
            "orchestrator": "orchestrator"
        }
    )

    # 5. Visualization Pipeline
    workflow.add_edge("viz_planner", "viz_generator")
    workflow.add_edge("viz_generator", "orchestrator") 

    # 6. Final Exit Logic (Fixed to prevent Recursion Loop)
    workflow.add_conditional_edges(
        "orchestrator",
        lambda state: state.get("next_step", "end"), 
        {
            "sql_generator": "sql_generator",
            "end": END
        }
    )

    return workflow.compile(checkpointer=MemorySaver() if checkpointer else None)