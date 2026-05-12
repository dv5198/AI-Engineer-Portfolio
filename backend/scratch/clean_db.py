import sqlite3
import os

db_path = r"d:\project\backend\portfolio.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM translations WHERE translated_text LIKE 'Error:%'")
    print(f"Deleted {cursor.rowcount} error entries.")
    conn.commit()
    conn.close()
else:
    print("DB not found.")
