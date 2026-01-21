import streamlit as st
import pandas as pd
from datetime import datetime

# from src.agent.sql_agent import run_sql_agent
from src.visualization.charts import generate_chart
# from src.visualization.viz import prepare_dataframe


st.set_page_config( page_title="QueryMate", layout="wide")

st.title("QueryMate")
st.caption("Ask questions and get answers directly from the database ")

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None


with st.sidebar:
    st.header("How to use")
    st.markdown(
        """
        **Examples:**
        - Top 5 products by sales
        - Monthly revenue in 1998
        - Customers with the most orders
        
        **Notes:**
        - Read-only queries only
        - SQL is shown for transparency
        """
    )

question = st.text_input("Ask a question about the database:", placeholder="e.g., Show me top 5 products by total sales")

run_button = st.button("Submit", type="primary")


if run_button:
    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    with st.spinner("Thinking..."):
        # response = run_sql_agent(question)
        response = { #Placeholder
                    "status": "success", # | "error"
                    "sql": "SELECT ProductName, SUM(SalesAmount) AS TotalSales FROM SalesTable GROUP BY ProductName ORDER BY TotalSales DESC LIMIT 5; ",
                    "columns": ["Product", "total_sales"],
                    "rows": [
                        ["K", 40],
                        ["M", 35],
                        ["B", 35],
                        ["L", 34],
                        ["A", 30],

                    ],
                    "error_message": None,
                    'chart': "bar" # | "line"
                    }


    if response["status"] == "error":
        st.error("Failed to execute the query.")
        st.code(response.get("error_message", "Unknown error"))
        st.stop()


    df = pd.DataFrame(
        response["rows"],
        columns=response["columns"]
    )

 
    chart_type = response.get("chart", "bar")

    # df = prepare_dataframe(df)
    chart = generate_chart(df, chart_type=chart_type)


    st.session_state.last_result = {
    "question": question,
    "df": df,
    "sql": response["sql"],
    "fig": chart,
    "answer": response.get("answer", "Here are the results for your query:")}

    
    st.session_state.history.append({
        "question": question,
        "timestamp": datetime.now()
    })

if st.session_state.last_result is not None:
    result = st.session_state.last_result

    st.subheader("Query Results")
    st.write(result["answer"])

    with st.expander("Show SQL Query"):
        st.code(result["sql"], language="sql")

    tab1, tab2 = st.tabs(["Dataframe", "Chart"])

    with tab1:
        st.dataframe(result["df"],hide_index=True, height=250, use_container_width=True)

    with tab2:
        if result["fig"] is not None:
            st.plotly_chart(result["fig"], height=250, use_container_width=True)
        else:
            st.info("No charts available for this query.")

    
    


    














