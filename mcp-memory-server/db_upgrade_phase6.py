# db_upgrade_phase6.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';
""")

conn.commit()
cur.close()
conn.close()

print("Phase 6 DB upgrade complete")