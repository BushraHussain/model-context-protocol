import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

cur.execute("""
CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    text TEXT NOT NULL,
    category TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

conn.commit()
cur.close()
conn.close()

print("Database ready")