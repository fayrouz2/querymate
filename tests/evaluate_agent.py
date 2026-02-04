"""
Automated Text-to-SQL Agent Evaluation Script
Evaluates the QueryMate agent against ground truth dataset
with comprehensive metrics tracking
"""

import sys
import os
import time
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / '.env')

from src.agent.sql_generator_agent import generate_sql_from_nl
from src.database.db_tool import SupabaseDBToolAsync, DBToolConfig
from src.config import OPENAI_API_KEY

from tests.metrics_calculator import MetricsCalculator
from tests.llm_judge import LLMJudgeEvaluator


class AgentEvaluator:
    """Main evaluation orchestrator"""

    def __init__(self, ground_truth_path: Optional[str] = None, max_attempts: int = 3):
        if ground_truth_path is None:
            ground_truth_path = Path(__file__).parent / 'data' / 'ground_truth.csv'

        self.ground_truth_path = ground_truth_path
        self.max_attempts = max_attempts
        self.results = []
        self.db_tool = None

        print("Using LLM-as-a-Judge for evaluation")
        self.llm_judge = LLMJudgeEvaluator()

    async def setup_database(self):
        print("Setting up database connection...")

        db_config = DBToolConfig(
            database_url="postgresql://postgres.mifszuwhtketjxkqgdji:Northwind2026%21@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require",
            max_repairs=0
        )

        self.db_tool = SupabaseDBToolAsync(db_config)
        await self.db_tool.start()

        print("✓ Database connection established")

    async def close_database(self):
        if self.db_tool:
            await self.db_tool.close()

    def load_ground_truth(self) -> List[Dict[str, Any]]:
        questions = []
        with open(self.ground_truth_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            questions.extend(reader)
        return questions

    async def execute_sql(self, sql: str) -> Tuple[Any, str]:
        try:
            result = await self.db_tool.run_sql(sql)

            if result.get("ok"):
                return result["data"]["rows"], None
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                return None, error_msg

        except Exception as e:
            return None, str(e)

    async def evaluate_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        q_id = question['id']
        q_text = question['natural_language_question']
        correct_sql = question['correct_sql']
        correct_result = question['correct_result']

        print(f"\nEvaluating {q_id}: {q_text[:70]}...")

        evaluation = {
            "question_id": q_id,
            "question": q_text,
            "difficulty": question['difficulty_level'],
            "category": question['business_category'],
            "sql_patterns": question['sql_patterns'],
            "correct_sql": correct_sql,
            "correct_result": correct_result,
            "attempts": [],
            "sql_execution_success": False,
            "result_accurate": False,
            "semantic_score": 1,
            "total_attempts": 0,
            "self_corrected": False,
            "total_time": 0.0,
            "comparison_method": None,
            "sql_equivalent": False
        }

        for attempt_num in range(1, self.max_attempts + 1):
            print(f"  Attempt {attempt_num}/{self.max_attempts}...")

            start_time = time.time()
            try:
                agent_sql = generate_sql_from_nl(q_text)
                gen_time = time.time() - start_time
            except Exception as e:
                evaluation["attempts"].append({
                    "attempt_number": attempt_num,
                    "sql": None,
                    "status": f"Agent error: {str(e)}",
                    "result": None,
                    "generation_time": gen_time,
                    "execution_time": 0
                })
                continue

            start_time = time.time()
            agent_result, error = await self.execute_sql(agent_sql)
            exec_time = time.time() - start_time

            status = "SUCCESS" if not error else f"ERROR: {error}"

            evaluation["attempts"].append({
                "attempt_number": attempt_num,
                "sql": agent_sql,
                "status": status,
                "result": agent_result,
                "generation_time": gen_time,
                "execution_time": exec_time
            })

            if not error:
                evaluation["sql_execution_success"] = True
                break

        evaluation["total_attempts"] = len(evaluation["attempts"])
        evaluation["total_time"] = sum(
            a["generation_time"] + a["execution_time"]
            for a in evaluation["attempts"]
        )

        if evaluation["sql_execution_success"] and evaluation["total_attempts"] > 1:
            evaluation["self_corrected"] = True

        if evaluation["sql_execution_success"]:
            last_attempt = evaluation["attempts"][-1]

            llm_eval = self.llm_judge.evaluate_complete(
                question=q_text,
                gold_sql=correct_sql,
                agent_sql=last_attempt["sql"],
                expected_result=correct_result,
                agent_result=last_attempt["result"]
            )

            evaluation["sql_equivalent"] = llm_eval["sql_evaluation"]["equivalent"]
            evaluation["sql_score"] = llm_eval["sql_evaluation"]["score"]
            evaluation["result_accurate"] = llm_eval["result_evaluation"]["correct"]
            evaluation["result_score"] = llm_eval["result_evaluation"]["score"]
            evaluation["semantic_score"] = int(llm_eval["overall_score"] * 5)
            evaluation["overall_correct"] = llm_eval["overall_correct"]
            evaluation["comparison_method"] = "llm_judge"

        return evaluation

    async def run_evaluation(self):
        print("=" * 70)
        print("TEXT-TO-SQL AGENT AUTOMATED EVALUATION")
        print("=" * 70)

        questions = self.load_ground_truth()
        await self.setup_database()

        for question in questions:
            result = await self.evaluate_question(question)
            self.results.append(result)

        await self.close_database()

    def save_detailed_results(self, filename: Optional[str] = None):
        if not self.results:
            return

        if filename is None:
            output_dir = Path(__file__).parent / 'results'
            output_dir.mkdir(exist_ok=True)
            filename = output_dir / 'evaluation_results_detailed.csv'

        fieldnames = [
            "id", "natural_language_question", "difficulty_level",
            "business_category", "sql_patterns",
            "sql_execution_success", "result_accurate",
            "semantic_score", "total_attempts",
            "self_corrected", "total_time",
            "comparison_method", "sql_equivalent",
            "sql_score", "result_score",
            "correct_sql", "agent_sql",
            "final_status", "correct_result",
            "agent_result"
        ]

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for r in self.results:
                final_attempt = r["attempts"][-1]

                writer.writerow({
                    "id": r["question_id"],
                    "natural_language_question": r["question"],
                    "difficulty_level": r["difficulty"],
                    "business_category": r["category"],
                    "sql_patterns": r["sql_patterns"],
                    "sql_execution_success": r["sql_execution_success"],
                    "result_accurate": r["result_accurate"],
                    "semantic_score": r["semantic_score"],
                    "total_attempts": r["total_attempts"],
                    "self_corrected": r["self_corrected"],
                    "total_time": round(r["total_time"], 2),
                    "comparison_method": r.get("comparison_method", ""),
                    "sql_equivalent": r.get("sql_equivalent", ""),
                    "sql_score": round(r.get("sql_score", 0.0), 3),
                    "result_score": round(r.get("result_score", 0.0), 3),
                    "correct_sql": r.get("correct_sql", ""),
                    "agent_sql": final_attempt.get("sql", ""),
                    "final_status": final_attempt.get("status", ""),
                    "correct_result": r.get("correct_result", ""),
                    "agent_result": json.dumps(final_attempt.get("result"), default=str)
                })

    def save_summary(self, metrics: Dict[str, Any], filename: Optional[str] = None):
        if filename is None:
            output_dir = Path(__file__).parent / 'results'
            output_dir.mkdir(exist_ok=True)
            filename = output_dir / 'evaluation_summary.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, default=str)


async def main():
    evaluator = AgentEvaluator(max_attempts=3)
    await evaluator.run_evaluation()

    calculator = MetricsCalculator(evaluator.results)
    metrics = calculator.calculate_all_metrics()

    evaluator.save_detailed_results()
    evaluator.save_summary(metrics)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
