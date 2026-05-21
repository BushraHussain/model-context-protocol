# uv run --with mcp mcp run app/mcp_server.py
# cd app mcp-inspector

import os
import json
import psycopg2
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer

load_dotenv()

mcp = FastMCP("Personal Memory Server")
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def create_embedding(text: str):
    embedding = embedding_model.encode(text)
    return embedding.tolist()

@mcp.tool()
def store_memory(
    user_id: str,
    text: str,
    category: str = "general",
    metadata: dict = {}
) -> str:
    """Store a memory note in PostgreSQL."""

    embedding = create_embedding(text)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO memories (user_id, text, category, metadata, embedding)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (user_id, text, category, json.dumps(metadata), embedding)
    )

    memory_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return f"Memory stored successfully with id: {memory_id}"


@mcp.tool()
def get_memories(user_id: str) -> str:
    """Get all memories for a user."""

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, text, category, created_at
        FROM memories
        WHERE user_id = %s
        ORDER BY created_at DESC;
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return str(rows)


@mcp.tool()
def search_memory(user_id: str, query: str) -> str:
    """Search memories by keyword for a user."""

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, text, category, created_at
        FROM memories
        WHERE user_id = %s
        AND (
            text ILIKE %s
            OR category ILIKE %s
        )
        ORDER BY created_at DESC;
        """,
        (user_id, f"%{query}%", f"%{query}%")
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:
        return "No matching memories found."

    return str(rows)


@mcp.tool()
def semantic_search_memory(user_id: str, query: str, limit: int = 5) -> str:
    """Search memories by semantic meaning using embeddings."""

    query_embedding = create_embedding(query)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            id, 
            text, 
            category, 
            created_at,
            embedding <=> %s::vector AS distance
        FROM memories
        WHERE user_id = %s
        AND embedding IS NOT NULL
        AND embedding <=> %s::vector < 0.7
        ORDER BY distance ASC
        LIMIT %s;
        """,
        (query_embedding, user_id, query_embedding, limit)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:
        return "No strong semantic matches found."

    return str(rows)

if __name__ == "__main__":
    mcp.run()