import sqlite3
import os

# Connect to database
db_path = "ev_charging.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("=" * 50)
print("Admin Account Setup")
print("=" * 50)

# Delete existing admin if any
cur.execute("DELETE FROM admin")
print("✅ Cleared old admin accounts")

# Create new admin with simple credentials
username = "admin"
password = "admin123"

cur.execute(
    "INSERT INTO admin (username, password) VALUES (?, ?)",
    (username, password)
)
conn.commit()
print(f"✅ Created admin account")
print(f"   Username: {username}")
print(f"   Password: {password}")

# Verify
cur.execute("SELECT * FROM admin")
admin = cur.fetchone()
if admin:
    print(f"✅ Admin verified in database")
else:
    print(f"❌ Admin not found in database")

conn.close()

print("\n" + "=" * 50)
print("Admin Login Credentials:")
print("=" * 50)
print(f"URL: http://localhost:5000/admin/login")
print(f"Username: {username}")
print(f"Password: {password}")
print("=" * 50)
