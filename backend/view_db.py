# view_db.py
import sqlite3
import json

conn = sqlite3.connect('wellness.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM logs ORDER BY id DESC")
rows = cursor.fetchall()

for row in rows:
    print(f"\n{'='*50}")
    print(f"ID: {row[0]}")
    print(f"Timestamp: {row[1]}")
    print(f"Mood: {row[2]}")
    print(f"Objectives: {json.loads(row[3])}")
    print(f"Summary: {row[4]}")

conn.close()