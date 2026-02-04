from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.agent.prompts import DAILOG_PROMPTS
from src.config import OPENAI_API_KEY

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0 ,openai_api_key=OPENAI_API_KEY)

def run_master_agent(messages):
    """
    This is the Master Agent Logic. It takes chat history and 
    returns the LLM's decision.
    """
    system_instruction = SystemMessage(content=DAILOG_PROMPTS["controller_system"])
    
    response = llm.invoke([system_instruction] + messages)
    return response



