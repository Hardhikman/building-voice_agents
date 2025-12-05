import os
import sqlite3
import pytest
from pathlib import Path
from src.db import Database

# Use a temporary database for testing
TEST_DB_PATH = "test_mastery.db"

@pytest.fixture
def db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    database = Database(TEST_DB_PATH)
    yield database
    
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_init_db(db):
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concept_mastery'")
    assert cursor.fetchone() is not None
    conn.close()

def test_upsert_concept(db):
    db.upsert_concept("test_concept", "Test Concept")
    
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM concept_mastery WHERE concept_id='test_concept'")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "Test Concept"
    conn.close()

def test_update_teach_back_score(db):
    db.upsert_concept("concept1", "Concept 1")
    
    # First score
    stats = db.update_teach_back_score("concept1", 80)
    assert stats["avg_score"] == 80.0
    assert stats["score_count"] == 1
    assert stats["times_taught_back"] == 1
    assert stats["last_score"] == 80
    
    # Second score
    stats = db.update_teach_back_score("concept1", 100)
    assert stats["avg_score"] == 90.0
    assert stats["score_count"] == 2
    assert stats["times_taught_back"] == 2
    assert stats["last_score"] == 100

def test_get_weakest_concepts(db):
    db.upsert_concept("c1", "Concept 1")
    db.upsert_concept("c2", "Concept 2")
    db.upsert_concept("c3", "Concept 3")
    
    db.update_teach_back_score("c1", 50)
    db.update_teach_back_score("c2", 90)
    db.update_teach_back_score("c3", 70)
    
    weakest = db.get_weakest_concepts(limit=2)
    assert len(weakest) == 2
    assert weakest[0][0] == "Concept 1" # 50
    assert weakest[1][0] == "Concept 3" # 70
