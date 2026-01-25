import streamlit as st
import pandas as pd
from datetime import datetime
import time




st.set_page_config(page_title="QueryMate", layout="wide")

st.title("QueryMate")
st.caption("Ask questions and get answers directly from the database")


if "history" not in st.session_state:
    st.session_state.history = []  

if "last_result" not in st.session_state:
    st.session_state.last_result = None



with st.sidebar:
    st.header("QueryMate Assistant")


    
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


    user_input = st.chat_input("Ask about the data...")


if user_input:

    st.session_state.history.append({
        "role": "user",
        "content": user_input
    })


    with st.spinner("Thinking..."):
        time.sleep(1)

        #chat agent placeholder
        conv_result = {
            "status": "success",
            "action": "query_db",
            "target_question": user_input,
            "chart": "bar"
        }

        #text to sql agent placeholder
        sql_result = {
            "status": "success",
            "sql": "SELECT ProductName, SUM(SalesAmount) AS TotalSales FROM SalesTable "
                   "GROUP BY ProductName ORDER BY TotalSales DESC LIMIT 5;",
            "columns": ["Product", "total_sales"],
            "rows": [
                ["K", 40],
                ["M", 35],
                ["B", 35],
                ["L", 34],
                ["A", 30]
            ],
            "error_message": None,
            "chart": conv_result["chart"]
        }

       
        df = pd.DataFrame(sql_result["rows"], columns=sql_result["columns"])

        #vis planer placeholder
        viz_plan = {
            "visualize": True,
            "chart_type": "bar",
            "x_axis": {"column": "total_sales", "label": "Total Sales"},
            "y_axis": {"column": "Product", "aggregation": "sum", "label": "Product"},
            "group_by": None,
            "title": "Top Products by Sales"
        }


        #temp viz
        import plotly.express as px
        fig = px.bar(
            df,
            x=viz_plan["x_axis"]["column"],
            y=viz_plan["y_axis"]["column"],
            orientation="h",
            title=viz_plan["title"]
        )

        st.session_state.last_result = {
            "question": user_input,
            "df": df,
            "sql": sql_result["sql"],
            "fig": fig,
            "answer": "Here are the results for your query:"
        }

        assistant_reply = "here are the results" #replace with chat agent reply

        st.session_state.history.append({
            "role": "assistant",
            "content": assistant_reply 
        })

        st.rerun()
        



if st.session_state.last_result is not None:
    result = st.session_state.last_result

    st.subheader("Query Results")
    st.write(result["answer"])

    with st.expander("Show SQL Query"):
        st.code(result["sql"], language="sql")

    tab1, tab2 = st.tabs(["Dataframe", "Chart"])

    with tab1:
        if result["df"] is not None:
            st.dataframe(result["df"], hide_index=True, height=300, use_container_width=True)
        else:
            st.info("No data available.")

    with tab2:
        if result["fig"] is not None:
            st.plotly_chart(result["fig"], use_container_width=True)
        else:
            st.info("No charts available for this query.")

else:
    st.info("Ask a question in the chat sidebar to see results here.")
