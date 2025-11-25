import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger("db")

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize the database schema."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS concept_mastery (
                        concept_id TEXT PRIMARY KEY,
                        title TEXT,
                        times_explained INTEGER DEFAULT 0,
                        times_quizzed INTEGER DEFAULT 0,
                        times_taught_back INTEGER DEFAULT 0,
                        last_score INTEGER DEFAULT 0,
                        avg_score REAL DEFAULT 0.0,
                        score_count INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def upsert_concept(self, concept_id: str, title: str):
        """Ensure a concept exists in the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Insert if not exists, otherwise do nothing (ignore)
                cursor.execute("""
                    INSERT OR IGNORE INTO concept_mastery (concept_id, title)
                    VALUES (?, ?)
                """, (concept_id, title))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to upsert concept {concept_id}: {e}")

    def update_teach_back_score(self, concept_id: str, score: int) -> Dict:
        """Update stats after a teach-back session and return updated stats."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current stats
                cursor.execute("""
                    SELECT avg_score, score_count, times_taught_back 
                    FROM concept_mastery WHERE concept_id = ?
                """, (concept_id,))
                row = cursor.fetchone()
                
                if row:
                    current_avg, current_count, current_taught = row
                    new_count = current_count + 1
                    new_taught = current_taught + 1
                    # Calculate new running average
                    new_avg = ((current_avg * current_count) + score) / new_count
                    
                    cursor.execute("""
                        UPDATE concept_mastery 
                        SET last_score = ?, avg_score = ?, score_count = ?, times_taught_back = ?
                        WHERE concept_id = ?
                    """, (score, new_avg, new_count, new_taught, concept_id))
                    conn.commit()
                    
                    return {
                        "avg_score": new_avg,
                        "score_count": new_count,
                        "times_taught_back": new_taught,
                        "last_score": score
                    }
                else:
                    logger.warning(f"Concept {concept_id} not found during update")
                    return {}
        except Exception as e:
            logger.error(f"Failed to update score for {concept_id}: {e}")
            return {}

    def get_weakest_concepts(self, limit: int = 3) -> List[Tuple[str, float, int]]:
        """Retrieve concepts with the lowest average score (that have been attempted)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, avg_score, score_count
                    FROM concept_mastery
                    WHERE score_count > 0
                    ORDER BY avg_score ASC
                    LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to get weakest concepts: {e}")
            return []

    def get_all_stats(self) -> Dict[str, Dict]:
        """Get all stats for in-memory cache initialization if needed."""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM concept_mastery")
                rows = cursor.fetchall()
                result = {}
                for row in rows:
                    result[row["concept_id"]] = dict(row)
                return result
        except Exception as e:
            logger.error(f"Failed to get all stats: {e}")
            return {}
