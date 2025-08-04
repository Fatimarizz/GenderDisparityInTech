import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('data/social_computing.db')
cursor = conn.cursor()

# Check what tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:", [t[0] for t in tables])

# Check each table
for table in tables:
    table_name = table[0]
    print(f"\n--- Table: {table_name} ---")
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        if not df.empty:
            print(f"First few rows:")
            print(df.head(2))
        else:
            print("Table is empty")
    except Exception as e:
        print(f"Error reading table {table_name}: {e}")

# Specifically check stackoverflow_questions structure
print(f"\n--- Detailed Stack Overflow Questions Structure ---")
try:
    questions_df = pd.read_sql_query("SELECT * FROM stackoverflow_questions LIMIT 3", conn)
    print(f"Columns: {list(questions_df.columns)}")
    print(f"Sample data:")
    print(questions_df)
except Exception as e:
    print(f"Error reading stackoverflow_questions: {e}")

conn.close() 