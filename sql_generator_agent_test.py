from src.agent.sql_generator_agent import generate_sql_from_nlq

# ---------- Test Cases ----------
test_cases = [
    {
        "question": "Show the top 5 customers by total revenue in 1997",
        "tables": ["customers", "orders", "order_details"],
        "keywords": ["SELECT", "FROM", "SUM", "GROUP BY", "ORDER BY", "LIMIT 5", "1997"]
    },
    {
        "question": "List products with total sales quantity greater than 100",
        "tables": ["products", "order_details"],
        "keywords": ["SELECT", "FROM", "SUM", "GROUP BY", "HAVING"]
    }
]

for case in test_cases:
    question = case["question"]
    sql_query = generate_sql_from_nlq(question)
    
    print("\n--- Generated SQL ---\n")
    print(sql_query)
    
    # ---------- Basic structure ----------
    assert sql_query is not None, "SQL query should not be None"
    assert isinstance(sql_query, str), "SQL query should be a string"
    assert "SELECT" in sql_query.upper(), "SQL must contain SELECT"
    assert "FROM" in sql_query.upper(), "SQL must contain FROM"
    
    # ---------- Security / safety ----------
    for forbidden in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]:
        assert forbidden not in sql_query.upper(), f"Forbidden SQL operation detected: {forbidden}"
    
    # ---------- Semantic correctness ----------
    for table in case["tables"]:
        assert table in sql_query.lower(), f"Query must reference {table} table"
    
    # ---------- Keywords check ----------
    for keyword in case["keywords"]:
        assert keyword.upper() in sql_query.upper(), f"Query must contain keyword: {keyword}"

print("\nAll SQL Generator tests passed successfully!")