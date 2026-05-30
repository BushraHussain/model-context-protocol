import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS importance INTEGER DEFAULT 3,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
""")

conn.commit()
cur.close()
conn.close()

print("Phase 7 DB upgrade complete")