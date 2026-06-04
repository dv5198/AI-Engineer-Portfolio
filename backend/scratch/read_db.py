import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'portfolio.db')
conn = sqlite3.connect(db_path)
rows = conn.execute("SELECT * FROM translations WHERE original_text LIKE '%Parkinson%'").fetchall()
conn.close()

for r in rows:
    print(r)
