from src.agent.sql_validator_agent import validate_sql_query

valid_sql = """
SELECT
  c."CompanyName",
  SUM(od."UnitPrice" * od."Quantity") AS total_revenue
FROM "orders" o
JOIN "customers" c ON c."CustomerID" = o."CustomerID"
JOIN "order_details" od ON od."OrderID" = o."OrderID"
GROUP BY c."CompanyName"
LIMIT 5;
"""

state = {"sql_query": valid_sql}

is_valid, message = validate_sql_query(state["sql_query"])

result = {
    "is_valid": is_valid,
    "validation_message": message,
    "next_step": "execute_sql" if is_valid else "sql_generator"
}

print("\n--- Validation Result (VALID SQL) ---\n")
print("is_valid:", result["is_valid"])
print("message:", result["validation_message"])
print("next_step:", result["next_step"])

# Assertions
assert result["is_valid"] is True
assert "VALID" in result["validation_message"].upper() or "safe" in result["validation_message"].lower()
assert result["next_step"] == "execute_sql"