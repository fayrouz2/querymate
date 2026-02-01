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


######## 

from typing import Annotated, List, TypedDict, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator

class AgentState(TypedDict):
    """
    The unified state for the QueryMate project. 
    This shared dictionary is the 'single source of truth' for all agents.
    """
    # --- 1. Core Conversation History ---
    messages: Annotated[List[BaseMessage], add_messages]
    next_step: str  # Controls the graph routing logic
    
    # --- 2. SQL & Database Data ---
    sql_query: Optional[str]  # The SQL generated or repaired
    db_result: Optional[Dict[str, Any]]  # Stores your ok_envelope or err_envelope
    
    # --- 3. Repair Loop Control (Matches your DB Tool) ---
    repair_count: int  # Current attempt number
    max_repairs: int   # Usually set to 2 or 3
    
    # --- 4. Logic & Orchestrator Flags ---
    is_valid: Optional[bool]      # Used for syntax validation
    needs_clarification: bool     # True if AI is confused by user intent
    is_unsupported: bool          # True if request is dangerous/out of scope
    feedback_reason: Optional[str] # The 'Internal Memo' from Repair to Orchestrator
    
    # --- 5. Visualization & UI Data ---
    viz_plan: Optional[str]       # The logical plan for the chart
    viz_code: Optional[str]       # The actual Python/Plotly code generated
    columns: Optional[List[str]]  # Column names for the UI
    sample_rows: Optional[List[dict]] # Data rows for the UI table