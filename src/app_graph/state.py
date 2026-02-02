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

######## 

# from typing import Annotated, List, TypedDict, Optional, Dict, Any
# from langchain_core.messages import BaseMessage
# from langgraph.graph.message import add_messages
# import operator

# class AgentState(TypedDict):
#     """
#     The unified state for the QueryMate project. 
#     This shared dictionary is the 'single source of truth' for all agents.
#     """
#     # --- 1. Core Conversation History ---
#     messages: Annotated[List[BaseMessage], add_messages]
#     next_step: str  # Controls the graph routing logic
    
#     # --- 2. SQL & Database Data ---
#     sql_query: Optional[str]  # The SQL generated or repaired
#     db_result: Optional[Dict[str, Any]]  # Stores your ok_envelope or err_envelope
    
#     # --- 3. Repair Loop Control (Matches your DB Tool) ---
#     repair_count: int  # Current attempt number
#     max_repairs: int   # Usually set to 2 or 3
    
#     # --- 4. Logic & Orchestrator Flags ---
#     is_valid: Optional[bool]      # Used for syntax validation
#     needs_clarification: bool     # True if AI is confused by user intent
#     is_unsupported: bool          # True if request is dangerous/out of scope
#     feedback_reason: Optional[str] # The 'Internal Memo' from Repair to Orchestrator
    
#     # --- 5. Visualization & UI Data ---
#     viz_plan: Optional[str]       # The logical plan for the chart
#     viz_code: Optional[str]       # The actual Python/Plotly code generated
#     columns: Optional[List[str]]  # Column names for the UI
#     sample_rows: Optional[List[dict]] # Data rows for the UI table

########last version

from typing import Annotated, List, TypedDict, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator

class AgentState(TypedDict):
    """
    The unified state for the QueryMate project. 
    This shared dictionary is the 'single source of truth' for all agents.
    """
    # --- 1. Core Conversation & Routing ---
    # messages: Stores history and uses add_messages to append new messages
    messages: Annotated[List[BaseMessage], add_messages]
    # next_step: The crucial routing variable used by your conditional edges
    next_step: str 
    
    # --- 2. SQL & Database Data ---
    # sql_query: The current SQL string (Generated or Repaired)
    sql_query: Optional[str]  
    # db_result: The JSON envelope (ok/error) returned by SupabaseDBToolAsync
    db_result: Optional[Dict[str, Any]] 
    # last_error: A helper field to store specific error details for the UI
    last_error: Optional[Dict[str, Any]]
    
    # --- 3. Repair Loop Control (Synced with DB Tool Config) ---
    # repair_count: Current attempt (0, 1, 2, 3)
    repair_count: int  
    # max_repairs: Total allowed attempts before the 'Circuit Breaker' stops the loop
    max_repairs: int   
    
    # --- 4. Logic & Orchestrator Flags ---
    # is_valid: General syntax check flag
    is_valid: Optional[bool]      
    # needs_clarification: True if the Agent needs to ask the user a question
    needs_clarification: bool     
    # is_unsupported: True for Policy Violations or unfixable errors
    is_unsupported: bool          
    # feedback_reason: The technical explanation passed from agents to Orchestrator
    feedback_reason: Optional[str] 
    
    # --- 5. Visualization & UI Data ---
    # viz_plan: The high-level description of the chart (Bar, Line, etc.)
    viz_plan: Optional[str]       
    # viz_code: The final Python/Plotly code to be executed in the UI
    viz_code: Optional[str]       
    # columns/sample_rows: Extracted from db_result for easy UI rendering
    columns: Optional[List[str]]  
    sample_rows: Optional[List[dict]]
