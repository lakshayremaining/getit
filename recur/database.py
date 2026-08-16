import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "cache.db")

def init_db():
    """Initializes the cache database and tables if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Cache for search queries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            query_key TEXT PRIMARY KEY,
            results_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Cache for individual candidate profiles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_cache (
            url TEXT PRIMARY KEY,
            data_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def get_cached_search(query_key: str, expiry_days: int = 7) -> list:
    """Retrieves cached search results if they are not expired."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT results_json, timestamp FROM search_cache WHERE query_key = ?", (query_key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        results_json, timestamp_str = row
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - timestamp < timedelta(days=expiry_days):
            return json.loads(results_json)
    return None

def set_cached_search(query_key: str, results: list):
    """Saves search results to the cache."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO search_cache (query_key, results_json, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (query_key, json.dumps(results))
    )
    conn.commit()
    conn.close()

def get_cached_profile(url: str, expiry_days: int = 30) -> dict:
    """Retrieves cached candidate profile if it is not expired."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT data_json, timestamp FROM profile_cache WHERE url = ?", (url,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        data_json, timestamp_str = row
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - timestamp < timedelta(days=expiry_days):
            return json.loads(data_json)
    return None

def set_cached_profile(url: str, data: dict):
    """Saves an extracted profile to the cache."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO profile_cache (url, data_json, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (url, json.dumps(data))
    )
    conn.commit()
    conn.close()

# Auto-initialize the database on import
init_db()
