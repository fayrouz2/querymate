
import sys
import os
import json
import asyncio
import pandas as pd
import sqlparse
import re
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date
from dotenv import load_dotenv
from difflib import SequenceMatcher
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage


CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

from src.app_graph.workflow import build_querymate_workflow
from src.database.db_tool import SupabaseDBToolAsync, DBToolConfig

load_dotenv(PROJECT_ROOT / '.env')


def clean_data(data):
    """Recursively clean data for JSON serialization and comparison."""
    if isinstance(data, list):
        return [clean_data(i) for i in data]
    elif isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif data is None:
        return None
    return data


def normalize_sql(sql: str) -> str:
    """Normalize SQL for comparison (removes whitespace, formatting differences)."""
    if not sql:
        return ""
    formatted = sqlparse.format(
        sql,
        reindent=True,
        keyword_case='upper',
        strip_comments=True
    )
    return ' '.join(formatted.split()).strip()


def sql_similarity(sql1: str, sql2: str) -> float:
    """Calculate similarity between two SQL queries (0-1 scale)."""
    norm1 = normalize_sql(sql1)
    norm2 = normalize_sql(sql2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def extract_table_names(sql: str) -> set:
    """Extract table names from SQL query."""
    sql_lower = sql.lower()
    tables = set()
    import re
    pattern = r'(?:from|join)\s+["\']?(\w+)["\']?'
    matches = re.findall(pattern, sql_lower)
    tables.update(matches)
    return tables


def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]:
    """Comprehensive DataFrame comparison."""
    result = {
        "exact_match": False,
        "row_count_match": False,
        "column_count_match": False,
        "columns_match": False,
        "semantic_match": False,
        "similarity_score": 0.0,
        "details": {}
    }
    
    if df1.empty and df2.empty:
        result["exact_match"] = True
        result["row_count_match"] = True
        result["column_count_match"] = True
        result["semantic_match"] = True
        result["similarity_score"] = 1.0
        return result
    
    if df1.empty or df2.empty:
        result["details"]["error"] = "One DataFrame is empty"
        return result
    
    result["row_count_match"] = len(df1) == len(df2)
    result["details"]["agent_rows"] = len(df1)
    result["details"]["expected_rows"] = len(df2)
    
    result["column_count_match"] = len(df1.columns) == len(df2.columns)
    
    df1_cols = sorted([c.lower().strip() for c in df1.columns])
    df2_cols = sorted([c.lower().strip() for c in df2.columns])
    result["columns_match"] = df1_cols == df2_cols
    
    if result["row_count_match"]:
        try:
            df1_sorted = df1.apply(lambda x: x.astype(str)).values.tolist()
            df2_sorted = df2.apply(lambda x: x.astype(str)).values.tolist()
            
            df1_sorted = sorted(df1_sorted, key=lambda x: str(x))
            df2_sorted = sorted(df2_sorted, key=lambda x: str(x))
            
            result["semantic_match"] = df1_sorted == df2_sorted
            
            if result["semantic_match"]:
                result["similarity_score"] = 1.0
            else:
                matching_rows = sum(1 for r1, r2 in zip(df1_sorted, df2_sorted) if r1 == r2)
                result["similarity_score"] = matching_rows / len(df1)
        except Exception as e:
            result["details"]["comparison_error"] = str(e)
    
    if result["row_count_match"] and result["columns_match"] and result["semantic_match"]:
        result["exact_match"] = True
    
    return result





async def evaluate_test_case(
    case: Dict[str, Any],
    app,
    db_tool: SupabaseDBToolAsync
) -> Dict[str, Any]:
    """Evaluate a single test case with metrics."""
    result = {
        "id": case['id'],
        "category": case.get('category', 'unknown'),
        "question": case['user_question'],
        "status": "FAIL",
        "match_type": None,
        "repair_attempts": 0,
        "metrics": {},
        "errors": []
    }
    
    try:
        print(f"📡 Testing {case['id']}: {case['user_question'][:60]}...")
        
        inputs = {"messages": [HumanMessage(content=case['user_question'])]}
        config = {"configurable": {"thread_id": f"eval_{case['id']}"}, "recursion_limit": 30}
        
        final_state = await app.ainvoke(inputs, config=config)
        
        generated_sql = final_state.get("sql_query")
        agent_res = final_state.get("db_result")
        repair_count = final_state.get("repair_count", 0)
        
        result["repair_attempts"] = repair_count
        result["generated_sql"] = generated_sql
        
        truth_res = await db_tool.run_sql(case['expected_sql'])
        
        if not agent_res or not agent_res.get("ok"):
            result["status"] = "EXECUTION_FAIL"
            result["errors"].append(agent_res.get("error", {}).get("message", "Unknown error") if agent_res else "No response")
            return result
        
        sql_sim = sql_similarity(generated_sql or "", case['expected_sql'])
        result["metrics"]["sql_similarity"] = round(sql_sim, 3)
        
        agent_df = pd.DataFrame(clean_data(agent_res['data']['rows']))
        truth_df = pd.DataFrame(clean_data(truth_res['data']['rows']))
        
        df_comparison = compare_dataframes(agent_df, truth_df)
        result["metrics"]["dataframe"] = df_comparison
        
        if df_comparison["exact_match"]:
            result["status"], result["match_type"] = "PASS", "EXACT"
        elif df_comparison["semantic_match"]:
            result["status"], result["match_type"] = "PASS", "SEMANTIC"
        elif df_comparison["row_count_match"]:
            result["status"], result["match_type"] = "PARTIAL", "ROW_COUNT_ONLY"
        
        if result["status"] == "PASS":
            result["success_method"] = "ZERO_SHOT" if repair_count == 0 else "AFTER_REPAIR"
        
    except Exception as e:
        result["status"] = "ERROR"
        result["errors"].append(str(e))
    
    return result


# REPORTING


def generate_detailed_report(results: List[Dict[str, Any]]):
    total = len(results)
    if total == 0: return
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    partial = sum(1 for r in results if r['status'] == 'PARTIAL')
    exec_fails = sum(1 for r in results if r['status'] == 'EXECUTION_FAIL')
    zero_shot = sum(1 for r in results if r.get('success_method') == 'ZERO_SHOT')
    after_repair = sum(1 for r in results if r.get('success_method') == 'AFTER_REPAIR')
    
    print("\n" + "="*70)
    print(" "*20 + "QUERYMATE EVALUATION REPORT")
    print("="*70)
    print(f"\n📊 OVERALL RESULTS:")
    print(f"{'Total Test Cases:':<35} {total}")
    print(f"{'Passed (Exact/Semantic):':<35} {passed} ({(passed/total)*100:.1f}%)")
    print(f"{'Partial Matches:':<35} {partial} ({(partial/total)*100:.1f}%)")
    print(f"{'Execution Errors:':<35} {exec_fails} ({(exec_fails/total)*100:.1f}%)")
    print(f"\n🎯 ACCURACY METRICS:")
    print(f"{'Zero-Shot Success:':<35} {zero_shot} ({(zero_shot/total)*100:.1f}%)")
    print(f"{'Success After Repair:':<35} {after_repair} ({(after_repair/total)*100:.1f}%)")
    print(f"{'Repair Agent Improvement:':<35} +{(after_repair/total)*100:.1f}%")
    print("="*70 + "\n")



async def run_golden_set_eval():
    # Dynamic Path for tests/data/golden_set.json
    json_path = CURRENT_DIR / "data" / "golden_set.json"
    
    if not os.path.exists(json_path):
        print(f"❌ Error: {json_path} not found.")
        return

    with open(json_path, 'r', encoding="utf-8") as f:
        data = json.load(f)
        test_cases = data['evaluations']

    db_tool = SupabaseDBToolAsync(DBToolConfig(database_url=os.getenv("SUPABASE_DB_URL")))
    await db_tool.start()
    app = build_querymate_workflow(db_tool)
    
    results = []
    print(f"🚀 Starting Evaluation on {len(test_cases)} cases...")

    for i, case in enumerate(test_cases, 1):
        result = await evaluate_test_case(case, app, db_tool)
        results.append(result)
        icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌", "EXECUTION_FAIL": "🔴"}.get(result['status'], "❓")
        print(f"[{i}/{len(test_cases)}] {icon} {result['status']}")

    with open(CURRENT_DIR / "results" / "evaluation_match_results_detailed.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    generate_detailed_report(results)
    await db_tool.close()

if __name__ == "__main__":
    asyncio.run(run_golden_set_eval())