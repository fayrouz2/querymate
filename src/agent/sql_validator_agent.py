from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.config import OPENAI_API_KEY
from src.agent.prompts import REPAIR_SYSTEM_PROMPT
import json
from langchain.prompts import ChatPromptTemplate

from langchain_core.output_parsers import JsonOutputParser


def repair_reasoning_engine(intent: str, sql: str, error_info: dict, dictionary: dict):
    """
    Analyzes SQL errors by cross-referencing the failed query with the 
    provided Data Dictionary.
    """

    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0,
        model_kwargs={"response_format": {"type": "json_object"}} 
    )

    system_instructions = (
        "You are a technical SQL Repair Agent. You must output ONLY a valid JSON object. "
        "Do not include any conversational text, markdown blocks, or explanations outside the JSON structure.\n\n"
        "DATA DICTIONARY:\n{dictionary_json}\n\n"
        "RESPONSE FORMAT:\n"
        "{{\n"
        '  "action": "REPAIR" | "CLARIFY" | "FAIL",\n'
        '  "repaired_sql": "string or null",\n'
        '  "reason": "string"\n'
        "}}\n\n"
        "RULES:\n"
        "1. REPAIR: Fix syntax or use synonyms from the dictionary.\n"
        "2. CLARIFY: If multiple dictionary entries match the intent.\n"
        "3. FAIL: If the request is impossible or dangerous."
    )
   
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("human", "Intent: {intent}\nSQL: {sql}\nError: {error}")
    ])

    chain = prompt | llm | JsonOutputParser()

    return chain.invoke({
        "dictionary_json": json.dumps(dictionary, indent=2),
        "intent": intent,
        "sql": sql,
        "error": error_info.get("message")
    })