import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from src.database.db_tool import SupabaseDBToolAsync, DBToolConfig
from src.app_graph.workflow import build_querymate_workflow
from langchain_core.messages import HumanMessage

load_dotenv()

app = FastAPI()

# ---------- Request Model ----------
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


# ---------- Startup / Shutdown ----------
@app.on_event("startup")
async def startup_event():
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        raise ValueError("SUPABASE_DB_URL not set in environment")

    cfg = DBToolConfig(database_url=db_url, max_repairs=3)
    db_tool = SupabaseDBToolAsync(cfg)

    await db_tool.start()

    app.state.db_tool = db_tool
    app.state.graph = build_querymate_workflow(db_tool)


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.db_tool.close()


# ---------- Chat Endpoint ----------
@app.post("/chat")
async def chat(req: ChatRequest):
    graph = app.state.graph

    initial_state = {
        "messages": [HumanMessage(content=req.message)],
        "repair_count": 0,
        "max_repairs": 3,
        "next_step": "",
        "db_result": None,
        "viz_code": None,
        "viz_plan": None,
        "columns": [],
        "sample_rows": [],
        "needs_clarification": False,
        "is_unsupported": False,
        "feedback_reason": None,
        "last_error": None,
    }

    config = {
        "configurable": {"thread_id": req.thread_id},
        "recursion_limit": 40
    }

    #result = graph.invoke(initial_state, config=config)
    result = await graph.ainvoke(initial_state, config=config)


    # Extract assistant message
    final_msg = result["messages"][-1].content

    return {
        "reply": final_msg,
        "sql_query": result.get("sql_query"),
        "viz_code": result.get("viz_code"),
        "columns": result.get("columns"),
        "sample_rows": result.get("sample_rows"),
        "error": result.get("last_error"),
    }
