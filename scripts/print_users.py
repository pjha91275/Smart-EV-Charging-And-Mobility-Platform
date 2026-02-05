import sqlite3
conn = sqlite3.connect('database/ev.db')
cur = conn.cursor()
try:
    cur.execute('SELECT id, name, email, password, role FROM users')
    rows = cur.fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print('ERROR:', e)
finally:
    conn.close()