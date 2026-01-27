# from typing import Annotated, List, TypedDict
# from langchain_core.messages import BaseMessage
# import operator

# src/langgraph/state.py
from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    next_step: str           # routing
    sql_query: str | None
    is_valid: bool | None


    
from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage
import operator


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
<<<<<<< Updated upstream
=======

    viz_code: str          #from code generator agent





    # src/langgraph/state.py
from typing import Annotated, List, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator


class GraphState(TypedDict, total=False):
    # ---- Conversation ----
    messages: Annotated[List[BaseMessage], add_messages]

    # ---- Routing ----
    next_step: str

    # ---- SQL generation ----
    sql_query: Optional[str]

    # ---- SQL validation ----
    is_valid: Optional[bool]
    validation_message: Optional[str]
    retry_count: Optional[int]

    # ---- DB execution (future) ----
    columns: Optional[List[str]]
    sample_rows: Optional[List[dict]]

    # ---- Visualization ----
    viz_plan: Optional[str]
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    viz_code: Optional[str]
>>>>>>> Stashed changes
=======
    viz_code: Optional[str]
>>>>>>> Stashed changes
=======
    viz_code: Optional[str]
>>>>>>> Stashed changes
