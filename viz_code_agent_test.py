import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 

from src.langgraph.workflow import build_visualization_planner_graph

viz_graph = build_visualization_planner_graph(checkpointer=False)


#fake dataframe (like SQL output)
df = pd.DataFrame({
    "order_date": ["2024-01", "2024-02", "2024-03", "2024-04"],
    "total_sales": [1200, 1500, 1100, 1800],
})

user_question = "Show the sales trend over time"

result = viz_graph.invoke({
    "question": user_question,
    "sql_query": "SELECT order_date, SUM(total) as total_sales FROM orders GROUP BY order_date",
    "columns": df.columns.tolist(),
    "sample_rows": df.head().to_dict(orient="records"),

} )

viz_plan = result["viz_plan"]
viz_code = result["viz_code"]

print("\n--- Visualization Plan ---\n")
print(viz_plan)

print("\n--- Generated Python Code ---\n")
print(viz_code)


local_vars = {
    "df": df,
    "px": px,
    "go": go
}

try:
    exec(viz_code, {}, local_vars)
    fig = local_vars.get("fig")

    if fig is None:
        raise ValueError("o figure named 'fig' was created by the agent.")

    fig.show()

except Exception as e:
    print("\nError while executing generated visualization code:")
    print(e)