# graph_build.py
# Example LangGraph wiring for your loop:
# NL→SQL -> DB -> (ok) Viz | (error) Repair -> DB ...
#
# NOTE: This is a skeleton. Replace nl_to_sql_node, repair_node, viz_node with your real nodes.

from __future__ import annotations

import os
from langgraph.graph import StateGraph, END

from db_tool_node import (
    DBToolConfig,
    SupabaseDBToolAsync,
    GraphState,
    make_db_execute_node,
    route_after_db,
)


# ----- Dummy placeholders (replace with your real nodes) -----

async def nl_to_sql_node(state: GraphState) -> GraphState:
    # state["sql"] should be set by your NL→SQL agent output
    # (This is just a placeholder)
    state["sql"] = state.get("sql", "SELECT 1 AS ok")
    return state


async def repair_sql_node(state: GraphState) -> GraphState:
    # This node represents your SQL Repair & Reasoning Agent.
    # It reads state["db_result"]["error"] and produces a fixed SQL in state["sql"].
    #
    # IMPORTANT: increment repair_count to prevent infinite loops.
    state["repair_count"] = int(state.get("repair_count", 0)) + 1

    # Placeholder repair:
    # In real life, call your repair agent and set the returned SQL.
    state["sql"] = "SELECT 1 AS repaired_ok"
    return state


async def viz_node(state: GraphState) -> GraphState:
    # Visualization planner/code generator would consume state["db_result"]["data"]
    return state


# ----- Build the graph -----

async def build_graph():
    cfg = DBToolConfig(
        database_url=os.environ["SUPABASE_DB_URL"],  # postgresql://...
        max_rows=2000,
        statement_timeout_ms=8000,
        max_repairs=2,
    )

    db_tool = SupabaseDBToolAsync(cfg)
    await db_tool.start()

    builder = StateGraph(GraphState)

    builder.add_node("nl_to_sql", nl_to_sql_node)
    builder.add_node("db_execute", make_db_execute_node(db_tool))
    builder.add_node("repair_sql", repair_sql_node)
    builder.add_node("viz", viz_node)

    builder.set_entry_point("nl_to_sql")
    builder.add_edge("nl_to_sql", "db_execute")

    # Conditional routing after DB
    builder.add_conditional_edges(
        "db_execute",
        route_after_db,
        {
            "viz": "viz",
            "repair": "repair_sql",
            "stop": END,   # stops if repair budget exceeded
        },
    )

    # Repair goes back to DB
    builder.add_edge("repair_sql", "db_execute")

    # Viz ends (or continue to code-gen node)
    builder.add_edge("viz", END)

    graph = builder.compile()

    # Return both so your app can close the pool on shutdown
    return graph, db_tool


# Example run (in an async context):
# graph, db_tool = await build_graph()
# out = await graph.ainvoke({"sql": "SELECT * FROM missing_table"})
# await db_tool.close()
