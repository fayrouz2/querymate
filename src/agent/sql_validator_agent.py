from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.agent.prompts import SQL_VALIDATOR_PROMPT
from src.config import OPENAI_API_KEY

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)

def validate_sql_query(sql_query: str) -> tuple:
    """
    Validates SQL query for security and safety.
    
    Args:
        sql_query: SQL query to validate
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    # Format the validation prompt with SQL query
    formatted_prompt = SQL_VALIDATOR_PROMPT.format(sql_query=sql_query)
    
    # Use formatted prompt as system instruction
    system_instruction = SystemMessage(content=formatted_prompt)
    
    try:
        # Invoke LLM with system instruction
        response = llm.invoke([system_instruction])
        
        validation_result = response.content.strip()
        
        # Check validation result
        if "VALID" in validation_result.upper():
            return True, "Query is safe and valid"
        else:
            return False, validation_result
            
    except Exception as e:
        return False, f"Validation Error: {str(e)}"