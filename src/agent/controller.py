# src/agent/controller.py
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.agent.prompts import DAILOG_PROMPTS
from src.config import OPENAI_API_KEY

# Initialize GPT-4
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0 ,openai_api_key=OPENAI_API_KEY)

def run_master_agent(messages):
    """
    This is the Master Agent Logic. It takes chat history and 
    returns the LLM's decision.
    """
    system_instruction = SystemMessage(content=DAILOG_PROMPTS["controller_system"])
    
    # GPT-4 decides how to respond based on the conversation history
    response = llm.invoke([system_instruction] + messages)
    return response