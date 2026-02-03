from typing import Annotated, List, TypedDict , Optional, Dict, Any
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
    db_result: Dict[str, Any] # NEW: DB tool envelope
    #columns: List[str]       # column names from result (optional)
    #sample_rows: List[dict]  # small sample of rows (optional)

    # Output of this agent
    viz_plan: str

    viz_code: str          #from code generator agent



class AgentState(TypedDict):
    # Core conversation history
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Technical SQL data
    sql_query: Optional[str]
    db_result: Optional[Dict[str, Any]] # Stores the Error Envelope from DB Tool
    
    # Repair loop control
    repair_attempt: int # Counter for the 3-round limit
    
    # Orchestrator control flags
    needs_clarification: bool # Triggered if intent is ambiguous
    is_unsupported: bool      # Triggered if request is impossible/dangerous
    feedback_reason: Optional[str] # Explanation for the user/orchestrator
    
    # Routing
    next_step: str # Determines the next node in the graph

class GraphState(TypedDict, total=False):
    # Inputs / outputs shared in the graph
    sql: str # is overwritten by NL→SQL or Repair Agent
    db_result: Dict[str, Any] # is written ONLY by DB Tool

    # Repair loop control
    repair_count: int # prevents infinite loops
    max_repairs: int

    # You can keep these if you want:
    last_error: Dict[str, Any]   # copy of db_result["error"] when ok=False