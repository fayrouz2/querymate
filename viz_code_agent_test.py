import pandas as pd
import plotly.express as px

from src.agent.viz_code_agent import generate_visualization_code_from_plan


#fake dataframe (like SQL output)
df = pd.DataFrame({
    "Product": ["A", "B", "C", "D"],
    "total_sales": [100, 150, 80, 120]
})

#fake Viz Planner output
viz_plan = {
    "visualize": True,
    "chart_type": "bar",
    "x_axis": {"column": "total_sales", "label": "Total Sales"},
    "y_axis": {"column": "Product", "label": "Product"},
    "group_by": None,
    "title": "Sales by Product"
}

fig, code = generate_visualization_code_from_plan(df, viz_plan)

print("Generated Code:\n", code)

if fig:
    print("Figure generated successfully!")
    fig.show()
else:
    print("Figure generation failed")
    print(code)
