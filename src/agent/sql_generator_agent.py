from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.agent.prompts import NLQ_TO_SQL_PROMPT
from src.config import OPENAI_API_KEY

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)


def _clean_sql_output(sql: str) -> str:
    """
    Remove markdown formatting from SQL output.
    
    Args:
        sql: Raw SQL string that might contain markdown
    
    Returns:
        str: Cleaned SQL query
    """
    sql = sql.strip()
    
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
    formatted_prompt = NLQ_TO_SQL_PROMPT.replace("{user_question}", user_question)
    
    system_instruction = SystemMessage(content=formatted_prompt)
    
    try:
        response = llm.invoke([system_instruction])
        
        sql = _clean_sql_output(response.content)
        
        return sql
        
    except Exception as e:
        return f"Error: {str(e)}"
