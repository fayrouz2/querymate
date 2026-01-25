from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

from .state import VizPlannerState
from .nodes import visualization_planner_node



def build_visualization_planner_graph():
    graph = StateGraph(VizPlannerState)

    graph.add_node("viz_planner", visualization_planner_node)

    # Use string endpoints for older langgraph versions
    graph.set_entry_point("viz_planner")
    graph.set_finish_point("viz_planner")

    return graph.compile(checkpointer=MemorySaver())


viz_planner_graph = build_visualization_planner_graph()

