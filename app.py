import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="QueryMate", layout="wide")

st.title("QueryMate")
st.caption("Ask questions and get answers directly from the database")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

# =========================
# Sidebar Chat
# =========================
with st.sidebar:
    st.header("QueryMate Assistant")

    # Display chat history
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input box
    user_input = st.chat_input("Ask about the data...")

# =========================
# Handle user input
# =========================
if user_input:
    # Save user message
    st.session_state.history.append({"role": "user", "content": user_input})

    with st.sidebar:
        assistant_placeholder = st.empty()

    with assistant_placeholder.container():
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Call FastAPI backend
                try:
                    response = requests.post(
                                "http://127.0.0.1:8000/chat",
                                json={"message": user_input, "thread_id": "session_001"}, 
                                timeout=60
                            )

                    response.raise_for_status()
                    result = response.json()
                except requests.exceptions.RequestException as e:
                    st.error(f"API Error: {e}")
                    st.stop()

                # Extract results
                answer = result.get("reply", "Here are your results.")
                sql_query = result.get("sql_query")
                columns = result.get("columns")
                rows = result.get("sample_rows")  # matches FastAPI
                viz_code = result.get("viz_code")


                df = pd.DataFrame(rows, columns=columns) if columns and rows else None
                fig = None

                # Execute visualization code safely
                if viz_code and df is not None:
                    st.code(viz_code, language="python")  # optional debug
                    try:
                        local_vars = {"df": df, "px": px}
                        exec(viz_code, {"__builtins__": {}}, local_vars)
                        fig = local_vars.get("fig")
                        if fig is None:
                            st.warning("Visualization code did not produce a figure.")
                    except Exception as e:
                        st.warning(f"Visualization failed: {e}")

                # Save last result
                st.session_state.last_result = {
                    "question": user_input,
                    "df": df,
                    "sql": sql_query,
                    "fig": fig,
                    "answer": answer
                }

                # Append AI reply
                st.session_state.history.append({"role": "assistant", "content": answer})
                st.rerun()

# =========================
# Main panel: Results
# =========================
if st.session_state.last_result:
    result = st.session_state.last_result

    st.subheader("Query Results")
    st.write(result["answer"])

    with st.expander("Show SQL Query"):
        if result["sql"]:
            st.code(result["sql"], language="sql")
        else:
            st.info("No SQL query available.")

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
