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
        """
        Initialize evaluator

        Args:
            ground_truth_path: Path to ground truth CSV (default: tests/data/ground_truth.csv)
            max_attempts: Maximum retry attempts per question
        """
        if ground_truth_path is None:
            ground_truth_path = Path(__file__).parent / 'data' / 'ground_truth.csv'

        self.ground_truth_path = ground_truth_path
        self.max_attempts = max_attempts
        self.results = []
        self.db_tool = None

        print("Using LLM-as-a-Judge for evaluation")
        self.llm_judge = LLMJudgeEvaluator()

    async def setup_database(self):
        """Setup PostgreSQL database connection"""
        print("Setting up database connection...")

        db_config = DBToolConfig(
            database_url="postgresql://postgres.mifszuwhtketjxkqgdji:Northwind2026%21@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require",
            max_repairs=0  
        )

        self.db_tool = SupabaseDBToolAsync(db_config)
        await self.db_tool.start()

        print("✓ Database connection established")

    async def close_database(self):
        """Close database connection"""
        if self.db_tool:
            await self.db_tool.close()

    def load_ground_truth(self) -> List[Dict[str, Any]]:
        """Load ground truth questions"""
        questions = []

        with open(self.ground_truth_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                questions.append(row)

        return questions

    async def execute_sql(self, sql: str) -> Tuple[Any, str]:
        """
        Execute SQL against PostgreSQL database

        Returns:
            (result, error_message)
        """
        try:
            result = await self.db_tool.run_sql(sql)

            if result.get("ok"):
                rows = result["data"]["rows"]
                return rows, None
            else:
                error_info = result.get("error", {})
                error_msg = error_info.get("message", "Unknown error")
                return None, error_msg

        except Exception as e:
            return None, str(e)

    async def evaluate_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single question with retry logic

        Returns:
            Evaluation result with all metrics
        """
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
            "sql_equivalent": False,
            "sql_explanation": None
        }

        for attempt_num in range(1, self.max_attempts + 1):
            print(f"  Attempt {attempt_num}/{self.max_attempts}...")

            start_time = time.time()
            try:
                agent_sql = generate_sql_from_nl(q_text)
                gen_time = time.time() - start_time
            except Exception as e:
                gen_time = time.time() - start_time
                agent_sql = None
                error_msg = f"Agent error: {str(e)}"

                evaluation["attempts"].append({
                    "attempt_number": attempt_num,
                    "sql": None,
                    "status": error_msg,
                    "result": None,
                    "generation_time": gen_time,
                    "execution_time": 0
                })

                continue

            print(f"    Generated SQL in {gen_time:.2f}s")

            start_time = time.time()
            agent_result, error = await self.execute_sql(agent_sql)
            exec_time = time.time() - start_time

            if error:
                status = f"ERROR: {error}"
                print(f"    ✗ Execution failed: {error[:100]}")
            else:
                status = "SUCCESS"
                print(f"    ✓ Executed in {exec_time:.2f}s")

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
            agent_sql = last_attempt["sql"]
            agent_result = last_attempt["result"]

            print(f"    Evaluating with LLM judge...")
            llm_eval = self.llm_judge.evaluate_complete(
                question=q_text,
                gold_sql=correct_sql,
                agent_sql=agent_sql,
                expected_result=correct_result,
                agent_result=agent_result
            )

            sql_eval = llm_eval["sql_evaluation"]
            result_eval = llm_eval["result_evaluation"]

            evaluation["sql_equivalent"] = sql_eval["equivalent"]
            evaluation["sql_explanation"] = sql_eval["explanation"]
            evaluation["sql_score"] = sql_eval["score"]
            evaluation["result_accurate"] = result_eval["correct"]
            evaluation["result_explanation"] = result_eval["explanation"]
            evaluation["result_score"] = result_eval["score"]
            evaluation["semantic_score"] = int(llm_eval["overall_score"] * 5)  # Convert to 1-5 scale
            evaluation["overall_correct"] = llm_eval["overall_correct"]
            evaluation["comparison_method"] = "llm_judge"

            if llm_eval["overall_correct"]:
                print(f"    ✓ Overall correct (SQL: {sql_eval['score']:.2f}, Result: {result_eval['score']:.2f})")
            else:
                print(f"    ✗ Issues found:")
                if not sql_eval["equivalent"]:
                    print(f"      SQL: {sql_eval['explanation'][:100]}...")
                if not result_eval["correct"]:
                    print(f"      Result: {result_eval['explanation'][:100]}...")
        else:
            print(f"    ✗ Execution failed after {evaluation['total_attempts']} attempts")

        return evaluation

    async def run_evaluation(self):
        """Run full evaluation"""
        print("="*70)
        print("TEXT-TO-SQL AGENT AUTOMATED EVALUATION")
        print("="*70)
        print(f"\nGround Truth: {self.ground_truth_path}")
        print(f"Max Attempts per Question: {self.max_attempts}")
        print(f"Evaluation Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        print("Loading ground truth...")
        questions = self.load_ground_truth()
        print(f"✓ Loaded {len(questions)} questions")

        await self.setup_database()

        print(f"\nEvaluating {len(questions)} questions...")
        print("="*70)

        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] ", end="")

            try:
                result = await self.evaluate_question(question)
                self.results.append(result)
            except Exception as e:
                print(f"\n  ERROR: {e}")
                import traceback
                traceback.print_exc()

            if i < len(questions):
                time.sleep(0.1)

        await self.close_database()

        print("\n" + "="*70)
        print("Evaluation completed!")
        print("="*70)

    def save_detailed_results(self, filename: Optional[str] = None):
        """Save detailed per-question results to CSV"""
        if not self.results:
            return

        if filename is None:
            output_dir = Path(__file__).parent / 'results'
            output_dir.mkdir(exist_ok=True)
            filename = output_dir / 'evaluation_results_detailed.csv'

        fieldnames = [
            "id", "natural_language_question", "difficulty_level", "business_category", "sql_patterns",
            "sql_execution_success", "result_accurate", "semantic_score",
            "total_attempts", "self_corrected", "total_time",
            "comparison_method",
            "sql_equivalent", "sql_score", "sql_explanation",
            "result_score", "result_explanation",
            "correct_sql", "agent_sql", "final_status",
            "correct_result", "agent_result"
        ]

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for r in self.results:
                final_attempt = r["attempts"][-1] if r["attempts"] else {}

                row = {
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
                    "sql_explanation": r.get("sql_explanation", "")[:200] if r.get("sql_explanation") else "",
                    "result_score": round(r.get("result_score", 0.0), 3),
                    "result_explanation": r.get("result_explanation", "")[:200] if r.get("result_explanation") else "",
                    "correct_sql": r.get("correct_sql", ""),
                    "agent_sql": final_attempt.get("sql", ""),
                    "final_status": final_attempt.get("status", ""),
                    "correct_result": r.get("correct_result", ""),
                    "agent_result": json.dumps(final_attempt.get("result"), default=str) if final_attempt.get("result") else ""
                }

                writer.writerow(row)

        print(f"\n✓ Saved detailed results to {filename}")

    def save_summary(self, metrics: Dict[str, Any], filename: Optional[str] = None):
        """Save metrics summary to JSON"""
        if filename is None:
            output_dir = Path(__file__).parent / 'results'
            output_dir.mkdir(exist_ok=True)
            filename = output_dir / 'evaluation_summary.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, default=str)

        print(f"✓ Saved metrics summary to {filename}")

    def generate_report(self, metrics: Dict[str, Any]):
        """Generate human-readable evaluation report"""
        print("\n" + "="*70)
        print("EVALUATION REPORT")
        print("="*70)

        print(f"\nTotal Questions: {metrics['total_questions']}")
        print(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        exec_metrics = metrics['sql_execution_success']
        print(f"\n--- SQL EXECUTION SUCCESS ---")
        print(f"Success Rate: {exec_metrics['success_rate']}% ({exec_metrics['successful_queries']}/{metrics['total_questions']})")
        print(f"Failed Queries: {exec_metrics['failed_queries']}")

        if exec_metrics['error_breakdown']:
            print(f"\nError Breakdown:")
            for error_type, count in exec_metrics['error_breakdown'].items():
                print(f"  - {error_type}: {count}")

        acc_metrics = metrics['result_accuracy']
        print(f"\n--- RESULT ACCURACY ---")
        print(f"Result Accuracy: {acc_metrics['accuracy']}% ({acc_metrics['correct_queries']}/{metrics['total_questions']})")
        print(f"Weighted Accuracy: {acc_metrics['weighted_accuracy']}%")
        print(f"Average Semantic Score: {acc_metrics['average_score']}/5")

        print(f"\nScore Distribution:")
        for score in [5, 4, 3, 2, 1]:
            count = acc_metrics['score_distribution'].get(score, 0)
            pct = (count / metrics['total_questions'] * 100) if metrics['total_questions'] > 0 else 0
            print(f"  {score} (Perfect): {count} ({pct:.1f}%)" if score == 5 else f"  {score}: {count} ({pct:.1f}%)")

        print(f"\nComparison Methods:")
        for method, count in acc_metrics['comparison_methods'].items():
            print(f"  {method}: {count}")

        self_corr = metrics['self_correction']
        print(f"\n--- SELF-CORRECTION CAPABILITY ---")
        print(f"First-Attempt Success: {self_corr['first_attempt_success_rate']}% ({self_corr['first_attempt_successes']}/{metrics['total_questions']})")
        print(f"Self-Correction Success: {self_corr['self_correction_success_rate']}% ({self_corr['self_corrected']}/{self_corr['failed_first_attempts']})")
        print(f"Average Attempts: {self_corr['average_attempts']}")

        time_perf = metrics['time_performance']
        print(f"\n--- QUERY EXECUTION TIME ---")
        print(f"Average Total Time: {time_perf['average_time']}s")
        print(f"Median (P50): {time_perf['median_time']}s")
        print(f"P95: {time_perf['p95_time']}s")
        print(f"P99: {time_perf['p99_time']}s")
        print(f"Range: {time_perf['min_time']}s - {time_perf['max_time']}s")

        print(f"\n--- BY DIFFICULTY LEVEL ---")
        for difficulty, stats in metrics['by_difficulty'].items():
            print(f"{difficulty} ({stats['total']}): {stats['accuracy']}% accuracy")

        print(f"\n--- BY BUSINESS CATEGORY ---")
        sorted_categories = sorted(metrics['by_category'].items(), key=lambda x: x[1]['accuracy'], reverse=True)
        for category, stats in sorted_categories[:10]:  # Top 10
            print(f"{category}: {stats['accuracy']}% ({stats['correct']}/{stats['total']})")

        error_patterns = metrics['error_patterns']
        if error_patterns['total_failures'] > 0:
            print(f"\n--- ERROR PATTERNS ---")
            print(f"Total Failures: {error_patterns['total_failures']}")

            if error_patterns['by_difficulty']:
                print(f"\nFailures by Difficulty:")
                for diff, count in sorted(error_patterns['by_difficulty'].items(), key=lambda x: x[1], reverse=True):
                    print(f"  {diff}: {count}")

            if error_patterns['common_errors'][:5]:
                print(f"\nSample Failed Questions:")
                for err in error_patterns['common_errors'][:5]:
                    print(f"  {err['question_id']}: {err['question']}...")

        print("\n" + "="*70)


async def main():
    """Main evaluation function"""
    try:
        evaluator = AgentEvaluator(max_attempts=3)

        await evaluator.run_evaluation()

        print("\nCalculating metrics...")
        calculator = MetricsCalculator(evaluator.results)
        metrics = calculator.calculate_all_metrics()

        evaluator.generate_report(metrics)

        evaluator.save_detailed_results()
        evaluator.save_summary(metrics)

        print("\n✓ Evaluation complete!")
        print(f"\nResults saved to tests/results/")

        return 0

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
