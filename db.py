import sqlite3
import threading

DB_PATH = "api_key_store.db"
_LOCK = threading.Lock()

def _get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def initialize_db():
    with _LOCK:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY,
                service TEXT UNIQUE,
                api_key TEXT
            )
        """)
        conn.commit()
        conn.close()

def save_api_key(service: str, api_key: str):
    with _LOCK:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_keys (service, api_key)
            VALUES (?, ?)
            ON CONFLICT(service) DO UPDATE SET api_key=excluded.api_key
        """, (service, api_key))
        conn.commit()
        conn.close()

def get_api_key(service: str):
    with _LOCK:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT api_key FROM api_keys WHERE service = ?", (service,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        return None

# Initialize DB on import
initialize_db()
