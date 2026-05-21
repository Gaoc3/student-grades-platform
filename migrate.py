import sqlite3
import os

db_path = "data/tenants/doctor_1.db"
if not os.path.exists(db_path):
    print("No database found at", db_path)
    exit()

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA table_info(grade_components)")
cols = [c[1] for c in cur.fetchall()]

try:
    if "semester" not in cols:
        cur.execute("ALTER TABLE grade_components ADD COLUMN semester INTEGER NOT NULL DEFAULT 1")
    if "category" not in cols:
        cur.execute("ALTER TABLE grade_components ADD COLUMN category VARCHAR(30) NOT NULL DEFAULT 'coursework'")
    if "order_index" not in cols:
        cur.execute("ALTER TABLE grade_components ADD COLUMN order_index INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    print("Migrated successfully.")
except Exception as e:
    print("Migration failed:", e)
finally:
    conn.close()
