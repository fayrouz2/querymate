"""
LLM-as-a-Judge Evaluator
Uses LLM to evaluate SQL query quality and result correctness
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import from querymate config, fallback to env
try:
    sys.path.insert(0, '/Users/shahad/Downloads/bootcamp/querymate')
    from src.config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your environment or .env file")


class LLMJudgeEvaluator:
    """Uses LLM to judge SQL queries and results"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize LLM judge

        Args:
            model: OpenAI model to use (gpt-4o, gpt-4o-mini, etc.)
        """
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model

    def evaluate_sql_query(
        self,
        question: str,
        gold_sql: str,
        agent_sql: str,
        schema_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate if agent's SQL is semantically equivalent to gold SQL

        Returns:
            {
                "equivalent": bool,
                "score": float (0-1),
                "explanation": str,
                "issues": List[str]
            }
        """
        prompt = f"""You are an expert SQL evaluator. Compare these two SQL queries for the question below.

Question: {question}

Gold Standard SQL (Correct):
```sql
{gold_sql}
```

Agent Generated SQL:
```sql
{agent_sql}
```

Evaluate if the agent's SQL is semantically equivalent to the gold standard SQL. Consider:
1. Do they retrieve the same data?
2. Are the columns selected appropriate?
3. Are the filters/conditions equivalent?
4. Are joins/aggregations correct?
5. Minor differences in aliases, formatting, or optimization are acceptable if results would be identical

Respond in JSON format:
{{
    "equivalent": true/false,
    "score": 0.0-1.0,
    "explanation": "detailed explanation of comparison",
    "issues": ["list", "of", "specific", "issues"] or []
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SQL evaluator. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            return {
                "equivalent": False,
                "score": 0.0,
                "explanation": f"LLM evaluation failed: {str(e)}",
                "issues": [str(e)]
            }

    def evaluate_results(
        self,
        question: str,
        expected_result: Any,
        agent_result: Any,
        gold_sql: Optional[str] = None,
        agent_sql: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate if agent's results match expected results

        Returns:
            {
                "correct": bool,
                "score": float (0-1),
                "explanation": str,
                "differences": List[str]
            }
        """
        # Format results for display
        expected_str = self._format_result(expected_result)
        agent_str = self._format_result(agent_result)

        prompt = f"""You are an expert database result evaluator. Compare these query results.

Question: {question}

Expected Result:
{expected_str}

Agent Result:
{agent_str}
"""

        if gold_sql and agent_sql:
            prompt += f"""
Gold SQL:
```sql
{gold_sql}
```

Agent SQL:
```sql
{agent_sql}
```
"""

        prompt += """
Evaluate if the agent's result is correct. Consider:
1. Are all expected rows present?
2. Are the values correct?
3. Are column names/structure appropriate?
4. Minor formatting differences are acceptable if data is correct
5. Order may differ unless explicitly required

Respond in JSON format:
{
    "correct": true/false,
    "score": 0.0-1.0,
    "explanation": "detailed explanation of comparison",
    "differences": ["list", "of", "differences"] or []
}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert database result evaluator. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            return {
                "correct": False,
                "score": 0.0,
                "explanation": f"LLM evaluation failed: {str(e)}",
                "differences": [str(e)]
            }

    def evaluate_complete(
        self,
        question: str,
        gold_sql: str,
        agent_sql: str,
        expected_result: Any,
        agent_result: Any
    ) -> Dict[str, Any]:
        """
        Complete evaluation: SQL + Results

        Returns:
            {
                "sql_evaluation": {...},
                "result_evaluation": {...},
                "overall_score": float,
                "overall_correct": bool
            }
        """
        sql_eval = self.evaluate_sql_query(question, gold_sql, agent_sql)
        result_eval = self.evaluate_results(
            question,
            expected_result,
            agent_result,
            gold_sql,
            agent_sql
        )

        # Overall score is weighted average (SQL: 40%, Results: 60%)
        overall_score = (sql_eval["score"] * 0.4) + (result_eval["score"] * 0.6)
        overall_correct = sql_eval["equivalent"] and result_eval["correct"]

        return {
            "sql_evaluation": sql_eval,
            "result_evaluation": result_eval,
            "overall_score": overall_score,
            "overall_correct": overall_correct
        }

    def _format_result(self, result: Any) -> str:
        """Format result for LLM consumption"""
        if result is None:
            return "NULL/Empty"

        if isinstance(result, str):
            try:
                result = json.loads(result)
            except:
                pass

        if isinstance(result, list):
            if len(result) == 0:
                return "Empty result set (0 rows)"

            # Format as a readable table
            if len(result) <= 10:
                return json.dumps(result, indent=2, default=str)
            else:
                # Show first 5 and last 5 for large results
                sample = result[:5] + ["... {} more rows ...".format(len(result) - 10)] + result[-5:]
                return json.dumps(sample, indent=2, default=str)

        return str(result)


# Quick test
if __name__ == "__main__":
    evaluator = LLMJudgeEvaluator()

    # Test SQL evaluation
    print("Testing SQL Evaluation:")
    sql_result = evaluator.evaluate_sql_query(
        question="How many products are in our catalog?",
        gold_sql='SELECT COUNT(*) AS ProductCount FROM Products',
        agent_sql='SELECT COUNT(*) AS product_count FROM "products"'
    )
    print(json.dumps(sql_result, indent=2))

    # Test result evaluation
    print("\nTesting Result Evaluation:")
    result_eval = evaluator.evaluate_results(
        question="How many products are in our catalog?",
        expected_result=[{"ProductCount": 77}],
        agent_result=[{"product_count": 77}]
    )
    print(json.dumps(result_eval, indent=2))
