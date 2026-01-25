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
