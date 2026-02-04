

# 🚀 QueryMate

QueryMate is an advanced AI-powered multi-agent Text-to-SQL system designed to bridge the gap between natural language and complex relational databases. Instead of writing manual SQL, users can ask questions in plain English and receive accurate, validated database results.

Unlike traditional Text-to-SQL systems, QueryMate uses a self-healing multi-agent architecture. If a generated SQL query fails, a specialized Repair Agent analyzes the database error and automatically fixes the query before returning results to the user.

---

## ✨ Key Features

- 🧠 Text-to-SQL Engine – Converts natural language into PostgreSQL queries  
- 🔁 Self-Healing Architecture – Repairs SQL errors automatically  
- ✅ Execution-Based Evaluation – Tested on 90 ground-truth business queries  
- 🗄️ Northwind Schema Support  
- 📊 Automatic Visualization Planning  
- 🌐 Interactive Streamlit UI  

---

## 🛠️ Tools & Technologies

| Component | Technology |
|----------|------------|
| Language | Python 3.11+ |
| LLM | OpenAI GPT-4o |
| Orchestration | LangGraph |
| Backend | FastAPI |
| Database | Supabase (PostgreSQL) |
| Frontend | Streamlit |
| Package Manager | UV |
| Deployment | Railway |
| Evaluation | Custom LLM-as-a-Judge |

---

## 🏗️ System Architecture

<img width="1920" height="1080" alt="Untitled design (2)" src="https://github.com/user-attachments/assets/42433852-7c27-417f-996a-d40f0cd3f172" />




##  System Flow Chart Digram:

<img width="1920" height="1080" alt="Untitled design" src="https://github.com/user-attachments/assets/286564e7-115c-4c12-b783-c43f65285b79" />



## Evalution Metric
Evaluation & Benchmarking
QueryMate was evaluated using a Golden Dataset of 85 natural language questions spanning simple filters to complex multi-join aggregations.
The +47.1% Repair Agent Improvement demonstrates the system's ability to autonomously debug and iterate on SQL syntax until execution success is achieved.


| Metric Name | Result |
|----------|------------|
|Architectural Recovery Gain | +47.1% |
| Logical Pass Rate | 69.5% |
| System Stability | 100% |






## 🌐 Deployment Link:
Live App: Click here to view QueryMate: https://querymate-frontend-production.up.railway.app

API Documentation: FastAPI Swagger UI



## Colne project : 
1-git clone https://github.com/yourusername/querymate.git

2-uv sync

### Run evalution:
uv run python tests/evaluate_agent.py
