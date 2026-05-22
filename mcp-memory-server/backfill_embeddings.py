import os
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
SELECT id, text
FROM memories
WHERE embedding IS NULL;
""")

rows = cur.fetchall()

for memory_id, text in rows:
    embedding = model.encode(text).tolist()

    cur.execute(
        """
        UPDATE memories
        SET embedding = %s
        WHERE id = %s;
        """,
        (embedding, memory_id)
    )

conn.commit()
cur.close()
conn.close()

print(f"Backfilled embeddings for {len(rows)} memories.")