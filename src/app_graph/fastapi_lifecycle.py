# fastapi_lifecycle.py
# How to fit it in FastAPI async lifecycle (startup/shutdown)

from __future__ import annotations

import os
from fastapi import FastAPI

from db_tool_node import DBToolConfig, SupabaseDBToolAsync
from graph_build import build_graph

app = FastAPI()

app.state.graph = None
app.state.db_tool = None

@app.on_event("startup")
async def startup():
    graph, db_tool = await build_graph()
    app.state.graph = graph
    app.state.db_tool = db_tool

@app.on_event("shutdown")
async def shutdown():
    if app.state.db_tool:
        await app.state.db_tool.close()

@app.post("/query")
async def query(payload: dict):
    # payload could include user question; your conversation agent would set state["sql"].
    # Here we just demonstrate a direct SQL pass-through for testing.
    sql = payload.get("sql", "SELECT 1")
    out = await app.state.graph.ainvoke({"sql": sql, "repair_count": 0})
    return out.get("db_result") or out
