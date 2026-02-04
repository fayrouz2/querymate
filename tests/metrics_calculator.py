"""
Metrics Calculator Module
Calculates all evaluation metrics from results
"""

import numpy as np
from typing import List, Dict, Any
from collections import defaultdict


class MetricsCalculator:
    """Calculate comprehensive evaluation metrics"""

    def __init__(self, results: List[Dict[str, Any]]):
        """
        Initialize with evaluation results

        Args:
            results: List of evaluation results for each question
        """
        self.results = results
        self.total = len(results)

    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all metrics"""
        metrics = {
            "total_questions": self.total,
            "sql_execution_success": self.calc_execution_success(),
            "result_accuracy": self.calc_result_accuracy(),
            "self_correction": self.calc_self_correction(),
            "time_performance": self.calc_time_performance(),
            "by_difficulty": self.calc_by_difficulty(),
            "by_category": self.calc_by_category(),
            "by_sql_feature": self.calc_by_sql_feature(),
            "error_patterns": self.analyze_error_patterns()
        }

        return metrics

    def calc_execution_success(self) -> Dict[str, Any]:
        """
        Metric 1: SQL Execution Success Rate
        """
        successful = sum(1 for r in self.results if r.get('sql_execution_success', False))
        success_rate = (successful / self.total * 100) if self.total > 0 else 0

        error_types = defaultdict(int)
        for r in self.results:
            if not r.get('sql_execution_success', False):
                attempts = r.get('attempts', [])
                if attempts:
                    last_attempt = attempts[-1]
                    error = last_attempt.get('status', 'Unknown error')

                    if 'syntax' in error.lower():
                        error_types['Syntax Error'] += 1
                    elif 'column' in error.lower() or 'table' in error.lower():
                        error_types['Semantic Error'] += 1
                    elif 'timeout' in error.lower():
                        error_types['Timeout'] += 1
                    else:
                        error_types['Runtime Error'] += 1

        return {
            "success_rate": round(success_rate, 2),
            "successful_queries": successful,
            "failed_queries": self.total - successful,
            "error_breakdown": dict(error_types)
        }

    def calc_result_accuracy(self) -> Dict[str, Any]:
        """
        Metric 2: Result Accuracy (Semantic Correctness)
        """
        correct_count = sum(1 for r in self.results if r.get('result_accurate', False))
        accuracy = (correct_count / self.total * 100) if self.total > 0 else 0

        score_distribution = defaultdict(int)
        total_score = 0
        comparison_methods = defaultdict(int)

        for r in self.results:
            score = r.get('semantic_score', 1)
            score_distribution[score] += 1
            total_score += score

            method = r.get('comparison_method', 'unknown')
            comparison_methods[method] += 1

        weighted_accuracy = (total_score / (self.total * 5) * 100) if self.total > 0 else 0

        return {
            "accuracy": round(accuracy, 2),
            "weighted_accuracy": round(weighted_accuracy, 2),
            "correct_queries": correct_count,
            "incorrect_queries": self.total - correct_count,
            "average_score": round(total_score / self.total, 2) if self.total > 0 else 0,
            "score_distribution": dict(score_distribution),
            "comparison_methods": dict(comparison_methods)
        }

    def calc_self_correction(self) -> Dict[str, Any]:
        """
        Metric 3: Self-Correction Capability
        """
        first_attempt_success = sum(
            1 for r in self.results
            if r.get('sql_execution_success', False) and r.get('total_attempts', 0) == 1
        )

        self_corrected = sum(
            1 for r in self.results
            if r.get('self_corrected', False)
        )

        failed_first_attempts = self.total - first_attempt_success
        self_correction_success_rate = (
            (self_corrected / failed_first_attempts * 100)
            if failed_first_attempts > 0 else 0
        )

        total_attempts = sum(r.get('total_attempts', 0) for r in self.results)
        avg_attempts = total_attempts / self.total if self.total > 0 else 0

        return {
            "first_attempt_success_rate": round(
                (first_attempt_success / self.total * 100) if self.total > 0 else 0,
                2
            ),
            "self_correction_success_rate": round(self_correction_success_rate, 2),
            "first_attempt_successes": first_attempt_success,
            "self_corrected": self_corrected,
            "failed_first_attempts": failed_first_attempts,
            "average_attempts": round(avg_attempts, 2),
            "total_attempts": total_attempts
        }

    def calc_time_performance(self) -> Dict[str, Any]:
        """
        Metric 4: Query Execution Time
        """
        total_times = [r.get('total_time', 0) for r in self.results if r.get('total_time')]

        if not total_times:
            return {
                "average_time": 0,
                "median_time": 0,
                "p95_time": 0,
                "p99_time": 0,
                "min_time": 0,
                "max_time": 0
            }

        return {
            "average_time": round(np.mean(total_times), 2),
            "median_time": round(np.median(total_times), 2),
            "p95_time": round(np.percentile(total_times, 95), 2),
            "p99_time": round(np.percentile(total_times, 99), 2),
            "min_time": round(min(total_times), 2),
            "max_time": round(max(total_times), 2)
        }

    def calc_by_difficulty(self) -> Dict[str, Dict[str, Any]]:
        """Breakdown by difficulty level"""
        difficulties = {}

        for difficulty in ["EASY", "MEDIUM", "HARD", "EXTRA_HARD"]:
            diff_results = [r for r in self.results if r.get('difficulty') == difficulty]

            if not diff_results:
                continue

            total = len(diff_results)
            correct = sum(1 for r in diff_results if r.get('result_accurate', False))
            executed = sum(1 for r in diff_results if r.get('sql_execution_success', False))

            difficulties[difficulty] = {
                "total": total,
                "accuracy": round((correct / total * 100) if total > 0 else 0, 2),
                "execution_success": round((executed / total * 100) if total > 0 else 0, 2),
                "correct": correct,
                "executed": executed
            }

        return difficulties

    def calc_by_category(self) -> Dict[str, Dict[str, Any]]:
        """Breakdown by business category"""
        categories = defaultdict(lambda: {"total": 0, "correct": 0, "executed": 0})

        for r in self.results:
            category = r.get('category', 'Unknown')
            categories[category]["total"] += 1

            if r.get('result_accurate', False):
                categories[category]["correct"] += 1

            if r.get('sql_execution_success', False):
                categories[category]["executed"] += 1

        for category, stats in categories.items():
            total = stats["total"]
            stats["accuracy"] = round((stats["correct"] / total * 100) if total > 0 else 0, 2)
            stats["execution_success"] = round((stats["executed"] / total * 100) if total > 0 else 0, 2)

        return dict(categories)

    def calc_by_sql_feature(self) -> Dict[str, Dict[str, Any]]:
        """Breakdown by SQL feature"""
        features = defaultdict(lambda: {"total": 0, "correct": 0, "executed": 0})

        for r in self.results:
            feature_list = r.get('sql_features', '').split(', ')

            for feature in feature_list:
                feature = feature.strip()
                if feature:
                    features[feature]["total"] += 1

                    if r.get('result_accurate', False):
                        features[feature]["correct"] += 1

                    if r.get('sql_execution_success', False):
                        features[feature]["executed"] += 1

        for feature, stats in features.items():
            total = stats["total"]
            stats["accuracy"] = round((stats["correct"] / total * 100) if total > 0 else 0, 2)
            stats["execution_success"] = round((stats["executed"] / total * 100) if total > 0 else 0, 2)

        return dict(features)

    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze common error patterns"""
        failed_questions = [r for r in self.results if not r.get('result_accurate', False)]

        error_patterns = {
            "total_failures": len(failed_questions),
            "by_difficulty": defaultdict(int),
            "by_category": defaultdict(int),
            "by_sql_feature": defaultdict(int),
            "common_errors": []
        }

        for r in failed_questions:
            error_patterns["by_difficulty"][r.get('difficulty', 'Unknown')] += 1
            error_patterns["by_category"][r.get('category', 'Unknown')] += 1

            features = r.get('sql_features', '').split(', ')
            for feature in features:
                feature = feature.strip()
                if feature:
                    error_patterns["by_sql_feature"][feature] += 1

            if r.get('attempts'):
                last_attempt = r.get('attempts', [])[-1]
                error_msg = last_attempt.get('status', '')
                if error_msg and error_msg != 'SUCCESS':
                    error_patterns["common_errors"].append({
                        "question_id": r.get('question_id'),
                        "question": r.get('question', '')[:80],
                        "error": error_msg[:100]
                    })

        error_patterns["by_difficulty"] = dict(error_patterns["by_difficulty"])
        error_patterns["by_category"] = dict(error_patterns["by_category"])
        error_patterns["by_sql_feature"] = dict(error_patterns["by_sql_feature"])

        return error_patterns


def test_metrics():
    """Test metrics calculator"""
    sample_results = [
        {
            "question_id": "NW-001",
            "difficulty": "EASY",
            "category": "Inventory",
            "sql_features": "COUNT",
            "sql_execution_success": True,
            "result_accurate": True,
            "semantic_score": 5,
            "total_attempts": 1,
            "self_corrected": False,
            "total_time": 2.5,
            "comparison_method": "exact_match"
        },
        {
            "question_id": "NW-002",
            "difficulty": "MEDIUM",
            "category": "Sales",
            "sql_features": "JOIN, GROUP BY",
            "sql_execution_success": True,
            "result_accurate": False,
            "semantic_score": 3,
            "total_attempts": 2,
            "self_corrected": True,
            "total_time": 5.2,
            "comparison_method": "cosine_borderline",
            "attempts": [{"status": "Syntax error"}, {"status": "SUCCESS"}]
        }
    ]

    calculator = MetricsCalculator(sample_results)
    metrics = calculator.calculate_all_metrics()

    print("Test Metrics:")
    print(f"  SQL Execution Success: {metrics['sql_execution_success']['success_rate']}%")
    print(f"  Result Accuracy: {metrics['result_accuracy']['accuracy']}%")
    print(f"  Self-Correction: {metrics['self_correction']}")
    print(f"  Time Performance: {metrics['time_performance']}")
    print("\n✓ Metrics calculator test passed!")


if __name__ == "__main__":
    test_metrics()
