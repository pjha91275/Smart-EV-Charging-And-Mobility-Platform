import sqlite3
import os

# Ensure database folder exists
os.makedirs("database", exist_ok=True)

def get_db():
    # One single DB path used everywhere
    return sqlite3.connect("database/ev.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ===============================
    # ADMIN TABLE
    # ===============================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    # ===============================
    # USERS TABLE (EV USERS + OWNERS)
    # ===============================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        blacklisted INTEGER DEFAULT 0
    )
    """)

    # ===============================
    # CHARGING STATIONS TABLE
    # ===============================
    cur.execute("""
CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    location TEXT,
    chargers INTEGER,
    price REAL,
    green_score INTEGER,
    owner_id INTEGER,
    approved INTEGER DEFAULT 0
)
""")


    # ===============================
    # CHARGING SESSIONS TABLE
    # ===============================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS charging_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        station_name TEXT,
        units REAL,
        amount REAL,
        tx_hash TEXT,
        status TEXT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        duration_minutes INTEGER
    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS waiting_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_name TEXT,
        user_id INTEGER,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    # Insert some sample users for testing (non-destructive)
    try:
        cur.execute("INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    ("Jane Hopper", "jane.hopper@example.com", "jane123", "user"))
        cur.execute("INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    ("Michael Wheeler", "michael.wheeler@example.com", "mike123", "user"))
    except Exception:
        pass

    conn.commit()
    conn.close()

    # Ensure 'blacklisted' column exists for older DBs
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cur.fetchall()]
        if 'blacklisted' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN blacklisted INTEGER DEFAULT 0")
            conn.commit()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
