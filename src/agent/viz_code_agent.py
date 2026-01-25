import os
from openai import OpenAI
import traceback
from langchain.agents import initialize_agent, Tool
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import AgentType
from langchain.prompts import PromptTemplate
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.agent.prompts import format_viz_code_prompt
from src.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_visualization_code_from_plan(df, viz_plan: dict):
    """
    Generates a Plotly figure from a DataFrame and a Viz Planner output.
    """
    prompt = format_viz_code_prompt(viz_plan, df)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate Python data visualization code from a plan."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    code = response.choices[0].message.content.strip()

    #remove accidental markdown formatting
    if code.startswith("```"):
        code = code.split("```")[1]

    local_vars = {
    "df": df,
    "px": px,
    "go": go,
    "pd": pd
    }

    try:
        exec(code, {}, local_vars)
        fig = local_vars.get("fig", None)
        return fig, code

    except Exception as e:
        error_trace = traceback.format_exc()
        return None, f"Code Execution Error:\n{e}\n\nTraceback:\n{error_trace}\n\nGenerated Code:\n{code}"


