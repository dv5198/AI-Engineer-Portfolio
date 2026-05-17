import sqlite3
import json

db_path = 'd:/project/backend/portfolio.db'
output_path = 'd:/project/current_data.json'

conn = sqlite3.connect(db_path)
data_str = conn.execute('SELECT data FROM portfolio_data WHERE id=1').fetchone()[0]
conn.close()

data = json.loads(data_str)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Data exported to {output_path}")
