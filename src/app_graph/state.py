from typing import Annotated, List, TypedDict , Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The unified state for the QueryMate project. 
    This shared dictionary is the 'single source of truth' for all agents.
    """
    messages: Annotated[List[BaseMessage], add_messages]

    next_step: str 
    
    sql_query: Optional[str]  
    db_result: Optional[Dict[str, Any]] 
    last_error: Optional[Dict[str, Any]]
    
    repair_count: int  
    max_repairs: int   
    
    is_valid: Optional[bool]      
    needs_clarification: bool     
    is_unsupported: bool          
    feedback_reason: Optional[str] 
    
    viz_plan: Optional[str]       
    viz_code: Optional[str]       
    columns: Optional[List[str]]  
    sample_rows: Optional[List[dict]]