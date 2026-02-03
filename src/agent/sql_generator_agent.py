from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.agent.prompts import NLQ_TO_SQL_PROMPT
from src.config import OPENAI_API_KEY

llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=1000, openai_api_key=OPENAI_API_KEY)


def _clean_sql_output(sql: str) -> str:
    """
    Remove markdown formatting from SQL output.
    
    Args:
        sql: Raw SQL string that might contain markdown
    
    Returns:
        str: Cleaned SQL query
    """
    sql = sql.strip()
    
    # Remove markdown code blocks
    if sql.startswith("```sql"):
        sql = sql[6:]
    elif sql.startswith("```"):
        sql = sql[3:]
    
    if sql.endswith("```"):
        sql = sql[:-3]
    
    return sql.strip()


def generate_sql_from_nl(user_question: str) -> str:
    """
    Generates SQL query from natural language question.
    
    Args:
        user_question: Natural language question from user
    
    Returns:
        str: Cleaned SQL query
    """
    # Format the full prompt with user question
    formatted_prompt = NLQ_TO_SQL_PROMPT.replace("{user_question}", user_question)
    
    # Use the entire formatted prompt as system message
    system_instruction = SystemMessage(content=formatted_prompt)
    
    try:
        # Invoke LLM with just the system instruction
        response = llm.invoke([system_instruction])
        
        # Clean SQL output (remove markdown if present)
        sql = _clean_sql_output(response.content)
        
        return sql
        
    except Exception as e:
        return f"Error: {str(e)}"





# from langchain_openai import ChatOpenAI  # Updated for deprecation
# from langchain_core.messages import SystemMessage
# from src.agent.prompts import NLQ_TO_SQL_PROMPT
# from src.config import OPENAI_API_KEY

# # Initialize the LLM
# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)

# def _clean_sql_output(sql: str) -> str:
#     """Remove markdown formatting from SQL output."""
#     sql = sql.strip()
#     if sql.startswith("```sql"):
#         sql = sql[6:]
#     elif sql.startswith("```"):
#         sql = sql[3:]
#     if sql.endswith("```"):
#         sql = sql[:-3]
#     return sql.strip()

# # Change 1: Added 'async' keyword
# async def generate_sql_from_nl(user_question: str) -> str:
#     """Generates SQL query from natural language question asynchronously."""
#     formatted_prompt = NLQ_TO_SQL_PROMPT.replace("{user_question}", user_question)
#     system_instruction = SystemMessage(content=formatted_prompt)
    
#     try:
#         # Change 2: Use 'await' and '.ainvoke()'
#         response = await llm.ainvoke([system_instruction])
        
#         sql = _clean_sql_output(response.content)
#         return sql
        
#     except Exception as e:
#         return f"Error: {str(e)}"