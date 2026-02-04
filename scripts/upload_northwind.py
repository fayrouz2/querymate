'''
This script migrates all tables and data from your local SQLite Northwind database 
(northwind.db) into Supabase PostgreSQL, replacing existing tables if they exist.

RUN THIS CODE ONCE
'''

import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = "data/northwind.db"
SUPABASE_DB_URL = os.environ["SUPABASE_DB_URL"]

sqlite_conn = sqlite3.connect(SQLITE_PATH)
pg_engine = create_engine(SUPABASE_DB_URL, pool_pre_ping=True)

tables = pd.read_sql(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
    sqlite_conn
)["name"].tolist()

print("Found tables:", tables)

for t in tables:
    df = pd.read_sql(f'SELECT * FROM "{t}"', sqlite_conn) 
    df.to_sql(t, pg_engine, if_exists="replace", index=False) 
    print(f"✅ Uploaded {t} ({len(df)} rows)")

print("🎉 Done: SQLite → Supabase")