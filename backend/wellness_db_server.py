from mcp.server.fastmcp import FastMCP
import sqlite3
import json
from datetime import datetime
import os

# Initialize FastMCP server
mcp = FastMCP("wellness-db")

DB_FILE = "wellness.db"

def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  mood TEXT,
                  objectives TEXT,
                  summary TEXT)''')
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

@mcp.tool()
def add_log(mood: str, objectives: list[str], summary: str) -> str:
    """Add a new wellness log entry.
    
    Args:
        mood: User's mood.
        objectives: List of objectives.
        summary: Agent's summary.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    # Store objectives as JSON string
    objectives_json = json.dumps(objectives)
    
    c.execute("INSERT INTO logs (timestamp, mood, objectives, summary) VALUES (?, ?, ?, ?)",
              (timestamp, mood, objectives_json, summary))
    conn.commit()
    conn.close()
    return "Log added successfully."

@mcp.tool()
def get_latest_log() -> str:
    """Get the most recent wellness log entry.
    
    Returns:
        JSON string of the latest log or None if empty.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT timestamp, mood, objectives, summary FROM logs ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if row:
        return json.dumps({
            "timestamp": row[0],
            "mood": row[1],
            "objectives": json.loads(row[2]),
            "summary": row[3]
        })
    return "No previous logs found."

if __name__ == "__main__":
    mcp.run()
