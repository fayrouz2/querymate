from src.metadata.data_dictionary import DICT_PROMPT

NLQ_TO_SQL_PROMPT = """
Act as a senior data analyst who is an expert in Natural Language Query (NLQ) to SQL generation. Your task is to convert natural language questions into accurate, executable SQL queries for a PostgreSQL database.

You will be provided with:
- The database schema (structure and relationships between tables)
- The data dictionary (column definitions and natural language synonyms)
- The natural language query to be converted into SQL

Your goal is to generate syntactically correct and semantically accurate PostgreSQL queries

Database Schema:

employees ||--|| employees : "reports to"
employees ||--o{ employee_territories : through
orders }o--|| shippers : "ships via"
order_details }o--|| orders : have
order_details }o--|| products : contain
products }o--|| categories : in
products }o--|| suppliers : "supplied by"
territories ||--|| regions : in
employee_territories }o--|| territories : have
orders }o--|| customers : place
orders }o--|| employees : "sold by"

categories {
int CategoryID PK
string CategoryName
string Description
string Picture
}

customers {
string CustomerID PK
string CompanyName
string ContactName
string ContactTitle
string Address
string City
string Region
string PostalCode
string Country
string Phone
string Fax
}

employees {
int EmployeeID PK
string LastName
string FirstName
string Title
string TitleOfCourtesy
date BirthDate
date HireDate
string Address
string City
string Region
string PostalCode
string Country
string HomePhone
string Extension
string Photo
string Notes
int ReportsTo FK
string PhotoPath
}

employee_territories {
int EmployeeID PK, FK
string TerritoryID PK, FK
}

order_details {
int OrderID PK, FK
int ProductID PK, FK
float UnitPrice
int Quantity
float Discount
}

orders {
int OrderID PK
string CustomerID FK
int EmployeeID FK
datetime OrderDate
datetime RequiredDate
datetime ShippedDate
int ShipVia FK
float Freight
string ShipName
string ShipAddress
string ShipCity
string ShipRegion
string ShipPostalCode
string ShipCountry
}

products {
int ProductID PK
string ProductName
int SupplierID FK
int CategoryID FK
string QuantityPerUnit
float UnitPrice
int UnitsInStock
int UnitsOnOrder
int ReorderLevel
string Discontinued
}

regions {
int RegionID PK
string RegionDescription
}

shippers {
int ShipperID PK
string CompanyName
string Phone
}

suppliers {
int SupplierID PK
string CompanyName
string ContactName
string ContactTitle
string Address
string City
string Region
string PostalCode
string Country
string Phone
string Fax
string HomePage
}

territories {
string TerritoryID PK
string TerritoryDescription
int RegionID FK
}

""" + DICT_PROMPT + """

## Instructions

**Consider the following while crafting the SQL query:**

1. **Schema Validation**: Use only table and column names that exist in the provided schema. Match exact casing: tables use lowercase (orders, customers), columns use CamelCase (\"OrderID\", \"CompanyName\")

2. **Column Validation**: If any requested column does not exist in the schema and cannot be derived via reasonable assumptions, the agent must not generate SQL and must return only: INVALID_QUERY

3. **JOIN Operations**: Include JOIN clauses ONLY when data needs to be fetched from multiple related tables. DO NOT perform unnecessary JOIN operations if the SQL query can be generated using a single table.

4. **Aggregations and Grouping**: When using aggregate functions (COUNT, SUM, AVG, MAX, MIN), ensure proper GROUP BY clauses are included when necessary.

5. **NULL Handling**: Be aware of NULL values and use appropriate NULL checks (IS NULL, IS NOT NULL) when needed.

6. **Subqueries**: Use subqueries when necessary for complex filtering or calculations, but prefer JOINs when performance is a concern.

7. **LIMIT Clause**: If the question implies a specific number of results (e.g., "top 5", "first 10"), include the appropriate LIMIT clause.

8. **ORDER BY**: When questions ask for "highest", "lowest", "most recent", "oldest", etc., include proper ORDER BY with ASC or DESC.

10. **Ambiguity Resolution**: If the natural language query is ambiguous, make reasonable assumptions based on common database query patterns and the available schema.

## Few-Shot Examples: NLQ → SQL pairs

Example 1:
Q: "List all orders with the customer name, order date, and shipping country."
A:
SELECT
  o."OrderID",
  c."CompanyName" AS customer_name,
  o."OrderDate",
  o."ShipCountry"
FROM "orders" o
JOIN "customers" c
  ON c."CustomerID" = o."CustomerID"
ORDER BY o."OrderDate";

Example 2:
Q: "Show the top 5 customers by total revenue in 1997. Revenue should be UnitPrice * Quantity * (1 - Discount). Return customer name, number of orders, and total revenue. Sort by total revenue descending."
A:
SELECT
  c."CompanyName" AS customer_name,
  COUNT(DISTINCT o."OrderID") AS num_orders,
  SUM(od."UnitPrice" * od."Quantity" * (1 - od."Discount")) AS total_revenue
FROM "orders" o
JOIN "customers" c
  ON c."CustomerID" = o."CustomerID"
JOIN "order_details" od
  ON od."OrderID" = o."OrderID"
WHERE o."OrderDate" >= DATE '1997-01-01'
  AND o."OrderDate" <  DATE '1998-01-01'
GROUP BY c."CompanyName"
ORDER BY total_revenue DESC
LIMIT 5;

Example 3:
Q: "For each shipping company, find the average shipping delay (days) in 1997, where delay = ShippedDate - RequiredDate (only include orders that were shipped late, i.e., delay > 0). Also show: number of late orders, and total late-order revenue. Return only shippers with at least 15 late orders, sorted by average delay (desc)."
A:
SELECT
  s."CompanyName" AS shipper_name,
  COUNT(*) AS late_orders_count,
  AVG((o."ShippedDate"::date - o."RequiredDate"::date)) AS avg_delay_days,
  SUM(od."UnitPrice" * od."Quantity" * (1 - od."Discount")) AS total_late_revenue
FROM "orders" o
JOIN "shippers" s
  ON s."ShipperID" = o."ShipVia"
JOIN "order_details" od
  ON od."OrderID" = o."OrderID"
WHERE o."OrderDate" >= DATE '1997-01-01'
  AND o."OrderDate" <  DATE '1998-01-01'
  AND o."ShippedDate" IS NOT NULL
  AND o."RequiredDate" IS NOT NULL
  AND (o."ShippedDate"::date - o."RequiredDate"::date) > 0
GROUP BY s."CompanyName"
HAVING COUNT(*) >= 15
ORDER BY avg_delay_days DESC, total_late_revenue DESC;

## Output Format

Return only the SQL query without any explanation or additional text. The query should:
- Be valid PostgreSQL syntax
- Be ready to execute directly
- Not include any comments or markdown formatting
- Use proper formatting and indentation for readability

## User's Question:
{user_question}
"""

DAILOG_PROMPTS = {
    "controller_system": """
    You are the QueryMate Master Orchestrator. You manage the interaction between the user and a team of data agents.

    REPAIR FEEDBACK HANDLING (Status Management):
    1. CLARIFICATION: If the Repair Agent flags 'needs_clarification', you must stop the technical flow and ask the user for more details about their request.
    2. UNSUPPORTED: If the Repair Agent flags 'is_unsupported', explain politely that the database cannot fulfill this specific request and offer an alternative.
    3. SUCCESS: If data is fetched, present the insights and charts clearly.

    ROUTING RULES:
    - For new data requests: Start with [TRIGGER_SQL]
    - For chatting or asking for clarification: Start with [NO_SQL]

    Current Date: {current_date}
    """
}

VISUALIZATION_PLANNER_PROMPT = """
Act as a senior data analyst who is an expert in visualization planning for database query results. Your task is to decide—based only on the returned result metadata (column names + data types) from a PostgreSQL database (Supabase)—whether the result should be visualized, and if yes, produce a clear chart plan.

You will be provided with:
- The database schema, which includes table names, column names, data types, and relationships (e.g., primary keys, foreign keys)
- The query result metadata from Supabase (column headers + data types, and optionally row count)
- The user's natural language question

Your goal is to produce a visualization plan that:
1. Chooses whether visualization is appropriate
2. Selects the most suitable chart type
3. Specifies x-axis and y-axis columns (and grouping if needed)
4. Provides a clear title for the chart
5. Uses only the provided schema + result metadata (do not infer missing columns or data)

## Database Schema

employees ||--|| employees : "reports to"
employees ||--o{ employee_territories : through
orders }o--|| shippers : "ships via"
order_details }o--|| orders : have
order_details }o--|| products : contain
products }o--|| categories : in
products }o--|| suppliers : "supplied by"
territories ||--|| regions : in
employee_territories }o--|| territories : have
orders }o--|| customers : place
orders }o--|| employees : "sold by"

categories {
int CategoryID PK
string CategoryName
string Description
string Picture
}

customers {
string CustomerID PK
string CompanyName
string ContactName
string ContactTitle
string Address
string City
string Region
string PostalCode
string Country
string Phone
string Fax
}

employees {
int EmployeeID PK
string LastName
string FirstName
string Title
string TitleOfCourtesy
date BirthDate
date HireDate
string Address
string City
string Region
string PostalCode
string Country
string HomePhone
string Extension
string Photo
string Notes
int ReportsTo FK
string PhotoPath
}

employee_territories {
int EmployeeID PK, FK
string TerritoryID PK, FK
}

order_details {
int OrderID PK, FK
int ProductID PK, FK
float UnitPrice
int Quantity
float Discount
}

orders {
int OrderID PK
string CustomerID FK
int EmployeeID FK
datetime OrderDate
datetime RequiredDate
datetime ShippedDate
int ShipVia FK
float Freight
string ShipName
string ShipAddress
string ShipCity
string ShipRegion
string ShipPostalCode
string ShipCountry
}

products {
int ProductID PK
string ProductName
int SupplierID FK
int CategoryID FK
string QuantityPerUnit
float UnitPrice
int UnitsInStock
int UnitsOnOrder
int ReorderLevel
string Discontinued
}

regions {
int RegionID PK
string RegionDescription
}

shippers {
int ShipperID PK
string CompanyName
string Phone
}

suppliers {
int SupplierID PK
string CompanyName
string ContactName
string ContactTitle
string Address
string City
string Region
string PostalCode
string Country
string Phone
string Fax
string HomePage
}

territories {
string TerritoryID PK
string TerritoryDescription
int RegionID FK
}

## Few-Shot Examples: Result Metadata → Visualization Plan

Example1:
Input (Result Metadata):

ShipCountry (string)

order_count (int)

Output:
{
"visualize": true,
"chart_type": "bar",
"x_axis": {
"column": "ShipCountry",
"label": "Shipping Country"
},
"y_axis": {
"column": "order_count",
"aggregation": "sum",
"label": "Number of Orders"
},
"group_by": null,
"title": "Number of Orders by Shipping Country"
}

Example2:
Input (Result Metadata):

OrderDate (datetime)

total_revenue (float)

Output:
{
"visualize": true,
"chart_type": "line",
"x_axis": {
"column": "OrderDate",
"label": "Order Date"
},
"y_axis": {
"column": "total_revenue",
"aggregation": "sum",
"label": "Total Revenue"
},
"group_by": null,
"title": "Revenue Trend Over Time"
}

Example3:
Input (Result Metadata):

total_customers (int)

Output:
{
"visualize": false,
"reason": "Single aggregated value does not require visualization"
}

## Instructions
###Consider the following while crafting the visualization plan:

1. Use Metadata Only: You must decide using only column names and data types from the query result metadata (and optional row count). Do not infer actual values.
2. Schema Awareness: Use the database schema to understand column meaning and typical semantics (e.g., dates vs categories vs measures). Ensure referenced columns exist.
3. When to Visualize: Visualization is recommended if the result includes comparisons, rankings, trends, distributions, or multiple rows. Visualization is not recommended for single scalar values, purely textual outputs, or ID-only results.
4. Identifiers Rule: Treat IDs (OrderID, CustomerID, ProductID, etc.) as identifiers and do not use them as axes unless the user explicitly requests it.
5. Chart Type Selection: Choose the simplest suitable chart:
  - Category → metric: bar chart (use horizontal bar for long labels or top-N)
  - Time → metric: line chart
  - Percent/share: pie/donut only when categories are few (otherwise bar)
  - Numeric distribution: histogram
  - Two numeric variables: scatter
  - Category + category + metric: grouped/stacked bar (use group_by)
6. Axis Assignment:
  - X-axis should usually be categorical or temporal
  - Y-axis should be numeric (count/sum/avg)
  - If there is a second categorical column, use it as group_by (optional)
7. Aggregation Handling: If a metric column name implies aggregation (e.g., total_, avg_, count_), set aggregation accordingly. If unclear, choose the most reasonable aggregation (often sum for totals, count for counts, avg for averages).
8. Title Quality: Titles must be business-friendly and descriptive (avoid raw column names when possible). Use human-readable labels.
9. No Code / No SQL: Do not generate SQL queries or plotting code. Only output the plan.
10. Strict JSON Only: Output must be valid JSON with double quotes and no trailing commas.

## Output Format:
Return only ONE JSON object without any explanation, comments, markdown formatting, or extra text.

If visualization is not needed:
{
"visualize": false,
"reason": "..."
}

If visualization is needed:
{
"visualize": true,
"chart_type": "bar | line | pie | histogram | scatter | stacked_bar",
"x_axis": {
"column": "...",
"label": "..."
},
"y_axis": {
"column": "...",
"aggregation": "count | sum | avg",
"label": "..."
},
"group_by": {
"column": "...",
"label": "..."
},
"title": "..."
}

## User's Question:
{user_question}

## Supabase Result Metadata:
{result_metadata}

"""

def format_viz_code_prompt(user_question: str, result_metadata: dict):
    """
    Format a prompt for the Viz Code Agent.

    :param user_question: original natural language question from the user
    :param result_metadata: metadata returned from Supabase / SQL execution
    :return: formatted prompt string
    """

    return VISUALIZATION_CODE_PROMPT.format(
        user_question=user_question,
        result_metadata=result_metadata
    )

VISUALIZATION_CODE_PROMPT = """
You are a senior data analyst engineer.

You have a pandas DataFrame called `df` and a visualization plan (from the Viz Planner Agent) as a JSON object.

Your task is to generate Python code to create the visualization using Plotly Express. 

RULES:
- Only use the columns specified in the plan
- Use only Plotly Express (px)
- Do NOT import libraries
- Do NOT print, explain, or add markdown
- Store the final chart in a variable named `fig`
- Use aggregation, grouping, and titles exactly as described in the plan
- Output only valid Python code

Visualization Plan:
{viz_plan}

DataFrame Preview (first 5 rows):
{df_preview}
"""

REPAIR_SYSTEM_PROMPT = """
You are the SQL Repair & Reasoning Agent for Northwind DB.
Your mission is to fix SQL errors by strictly following the Data Dictionary and Schema.

DATA DICTIONARY:
{data_dictionary}

GUIDELINES:
1. REPAIR: If a column or table name is wrong, check 'synonyms' in the dictionary and use the actual name.
2. CLARIFY: If the user's intent matches multiple synonyms or is vague, stop and ask the Orchestrator for clarification.
3. FAIL: If the request asks for data not present in the tables above or is a dangerous operation (DELETE/DROP).

OUTPUT FORMAT:
Return only a JSON object:
{{
  "action": "REPAIR" | "CLARIFY" | "FAIL",
  "repaired_sql": "The corrected SQL if action is REPAIR",
  "reason": "Explain why this decision was made"
}}
"""