from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.agent.prompts import NLQ_TO_SQL_PROMPT 
from src.config import OPENAI_API_KEY

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)

def generate_sql_from_nlq(user_question: str) -> str:
    """
    Generates SQL query from natural language question.
    
    Args:
        user_question: Natural language question from user
    
    Returns:
        str: Cleaned SQL query
    """
    # Format the full prompt with user question
    formatted_prompt = NLQ_TO_SQL_PROMPT.format(user_question=user_question)
    
    # Use the entire formatted prompt as system message
    system_instruction = SystemMessage(content=formatted_prompt)
    
    try:
        # Invoke LLM with just the system instruction
        response = llm.invoke([system_instruction])
        
        print(response.content)

        # Extract and clean SQL
        # sql = _clean_sql_output(response.content)
        return response.content.strip()
        
    except Exception as e:
        return f"Error: {str(e)}"