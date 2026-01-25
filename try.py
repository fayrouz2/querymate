from src.langgraph.workflow import viz_planner_graph

result = viz_planner_graph.invoke(
    {
        "question": "Show me total sales per month",
        "sql_query": "SELECT ...",
        "columns": ["month", "total_sales"],
        "sample_rows": [{"month": "2025-01-01", "total_sales": 12000}],
    },
    config={"configurable": {"thread_id": "viz-test-1"}}
)

print(result["viz_plan"])

