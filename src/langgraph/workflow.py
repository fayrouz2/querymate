from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import VizPlannerState
from .nodes import visualization_planner_node


def build_visualization_planner_graph():
    graph = StateGraph(VizPlannerState)

    graph.add_node("viz_planner", visualization_planner_node)
    graph.add_edge(START, "viz_planner")
    graph.add_edge("viz_planner", END)

    # MemorySaver is good for dev/testing and chaining
    return graph.compile(checkpointer=MemorySaver())


# Export a ready-to-use compiled graph object
viz_planner_graph = build_visualization_planner_graph()
