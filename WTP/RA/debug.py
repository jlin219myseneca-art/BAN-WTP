import sqlite3
import pandas as pd

conn = sqlite3.connect("job_market_research.db")
print("--- REQUIREMENTS TABLE ---")
print(pd.read_sql("SELECT * FROM requirements", conn))
print("\n--- JOBS TABLE ---")
print(pd.read_sql("SELECT * FROM jobs", conn))
conn.close()