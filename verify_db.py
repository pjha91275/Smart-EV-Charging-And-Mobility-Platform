from models.db import get_db

conn = get_db()
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Database tables created:")
for table in tables:
    print(f"  ✓ {table[0]}")

# Check users table
cur.execute("SELECT COUNT(*) FROM users")
user_count = cur.fetchone()[0]
print(f"\nUsers in database: {user_count}")

conn.close()
