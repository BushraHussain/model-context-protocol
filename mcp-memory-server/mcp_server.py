# uv run --with mcp mcp run app/mcp_server.py
# cd app mcp-inspector

import os
import json
import psycopg2
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
from datetime import datetime
import ollama

load_dotenv()

mcp = FastMCP("Personal Memory Server")
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def create_embedding(text: str):
    embedding = embedding_model.encode(text)
    return embedding.tolist()

def format_memory_results(rows):
    results = []

    for row in rows:
        memory_id, text, category, created_at, distance = row

        similarity = round(1 - float(distance), 4)

        results.append({
            "id": memory_id,
            "text": text,
            "category": category,
            "created_at": created_at.isoformat(),
            "similarity": similarity
        })

    return json.dumps({"results": results}, indent=2)

def generate_answer(question: str, memories: str) -> str:
    prompt = f"""
You are a helpful memory assistant.

Use only the memories below to answer the question.
If the answer is not in the memories, say: I don't have enough memory context.

Memories:
{memories}

Question:
{question}

Answer:
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response["message"]["content"]

# ================ Memory Tools ================

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

    # Avoid weak semantic search for very short queries
    if len(query.strip().split()) < 2:
        return json.dumps({
            "results": [],
            "message": "Use keyword or hybrid search for short one-word queries."
        }, indent=2)

    query_embedding = create_embedding(query)
    min_similarity = 0.30

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            id, 
            text, 
            category, 
            created_at,
            1 - (embedding <=> %s::vector) AS similarity
        FROM memories
        WHERE user_id = %s
        AND embedding IS NOT NULL
        AND 1 - (embedding <=> %s::vector) >= %s
        ORDER BY similarity DESC
        LIMIT %s;
        """,
        (query_embedding, user_id, query_embedding, min_similarity, limit)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return json.dumps({"results": [], "message": "No strong semantic matches found."}, indent=2)

    results = []
    for memory_id, text, category, created_at, similarity in rows:
        results.append({
            "id": memory_id,
            "text": text,
            "category": category.strip() if category else None,
            "created_at": created_at.isoformat(),
            "similarity": round(float(similarity), 4)
        })

    return json.dumps({"results": results}, indent=2)

@mcp.tool()
def hybrid_search_memory(user_id: str, query: str, limit: int = 5) -> str:
    """Search memories using keyword + semantic search."""

    query_embedding = create_embedding(query)
    min_similarity = 0.30
    keyword_pattern = f"%{query}%"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            id,
            text,
            category,
            created_at,
            1 - (embedding <=> %s::vector) AS similarity,
            CASE 
                WHEN text ILIKE %s THEN 1
                WHEN TRIM(category) ILIKE %s THEN 1
                ELSE 0
            END AS keyword_match
        FROM memories
        WHERE user_id = %s
        AND embedding IS NOT NULL
        AND (
            1 - (embedding <=> %s::vector) >= %s
            OR text ILIKE %s
            OR TRIM(category) ILIKE %s
        )
        ORDER BY
            CASE 
                WHEN text ILIKE %s THEN 1
                WHEN TRIM(category) ILIKE %s THEN 1
                ELSE 0
            END DESC,
            similarity DESC
        LIMIT %s;
        """,
        (
            query_embedding,
            keyword_pattern,
            keyword_pattern,
            user_id,
            query_embedding,
            min_similarity,
            keyword_pattern,
            keyword_pattern,
            keyword_pattern,
            keyword_pattern,
            limit
        )
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return json.dumps({"results": [], "message": "No hybrid matches found."}, indent=2)

    results = []
    for memory_id, text, category, created_at, similarity, keyword_match in rows:
        results.append({
            "id": memory_id,
            "text": text,
            "category": category.strip() if category else None,
            "created_at": created_at.isoformat(),
            "similarity": round(float(similarity), 4),
            "keyword_match": bool(keyword_match)
        })

    return json.dumps({"results": results}, indent=2)

@mcp.tool()
def answer_from_memory(user_id: str, question: str) -> str:
    """Answer a question using retrieved memories."""

    search_result = hybrid_search_memory(user_id=user_id, query=question, limit=5)

    data = json.loads(search_result)

    if not data.get("results"):
        return "I don't have enough memory context."

    memories_text = "\n".join([
        f"- {item['text']} (category: {item['category']})"
        for item in data["results"]
    ])

    return generate_answer(question, memories_text)

if __name__ == "__main__":
    mcp.run()