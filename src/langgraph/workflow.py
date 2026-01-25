from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

from .state import VizPlannerState
from .nodes import visualization_planner_node, visualization_code_generator_node


def build_visualization_planner_graph(checkpointer=True): #TODO: change graph name after adding other nodes
    graph = StateGraph(VizPlannerState)

    graph.add_node("viz_planner", visualization_planner_node)
    graph.add_node("viz_code_generator", visualization_code_generator_node)

    graph.set_entry_point("viz_planner")
    graph.add_edge("viz_planner", "viz_code_generator")
    graph.set_finish_point("viz_code_generator")

    if checkpointer:
        return graph.compile(checkpointer=MemorySaver())
    else:
        return graph.compile(checkpointer=None)


viz_graph = build_visualization_planner_graph()
