import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

cur.execute("""
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS embedding VECTOR(384);
""")

conn.commit()
cur.close()
conn.close()

print("Phase 4 DB upgrade complete")