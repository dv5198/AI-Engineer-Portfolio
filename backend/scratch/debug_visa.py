import sqlite3
import json
import os

def debug_visa():
    db_path = "backend/portfolio.db"
    if not os.path.exists(db_path):
        db_path = "portfolio.db"
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM portfolio_data WHERE id = 1")
    row = cursor.fetchone()
    if row:
        data = json.loads(row[0])
        profile = data.get("profile", {})
        print("VISA MAP IN DATABASE:")
        print(json.dumps(profile.get("visa", {}), indent=2))
        print("\nPERSONAL INFO:")
        print(json.dumps(profile.get("personal", {}), indent=2))
    conn.close()

if __name__ == "__main__":
    debug_visa()
