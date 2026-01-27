# src/langgraph/state.py
from typing import Annotated, List, TypedDict , Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator



class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    next_step: str        # Which node to execute next
    sql_query: Optional[str]
    is_valid: Optional[bool]
    
    needs_clarification: bool
    is_unsupported: bool
    # To pass the reason from Repair to Orchestrator
    feedback_reason: Optional[str] 
    
    # --- Data for UI ---
    columns: Optional[List[str]]
    sample_rows: Optional[List[dict]]
    viz_code: Optional[str]


class SQLGeneratorState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    sql_query: str | None


class SQLValidatorState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    sql_query: str | None
    is_valid: bool | None
    validation_message: str | None
    retry_count: int | None


class VizPlannerState(TypedDict, total=False):
    """
    Shared state passed between LangGraph nodes.
    total=False means keys are optional (flexible for your teammate to connect later).
    """

    # Conversation messages (LangGraph will merge lists using operator.add)
    messages: Annotated[List[BaseMessage], operator.add]

    # Inputs that your teammate might pass in later
    question: str            # user's question in NL
    sql_query: str           # SQL used (optional)
    columns: List[str]       # column names from result (optional)
    sample_rows: List[dict]  # small sample of rows (optional)

    # Output of this agent
    viz_plan: str

    viz_code: str          #from code generator agent