# mcp-inspector python mcp_server.py
# mcp-inspector

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
You are a careful memory assistant.

Rules:
1. Use only the memories provided.
2. Do not invent facts.
3. If memories are weak or unrelated, say you don't have enough memory context.
4. Answer briefly and clearly.

Memories:
{memories}

Question:
{question}

Answer:
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]

def build_memory_context(results):
    return "\n".join([
        f"- ID {item['id']}: {item['text']} | category: {item['category']} | similarity: {item['similarity']}"
        for item in results
    ])

def calculate_confidence(results):
    if not results:
        return "none"

    best_similarity = max(item["similarity"] for item in results)

    if best_similarity >= 0.55:
        return "high"
    elif best_similarity >= 0.35:
        return "medium"
    else:
        return "low"
    
def filter_relevant_results(results):
    return [
        item for item in results
        if item["keyword_match"] is True or item["similarity"] >= 0.65
    ][:3]

def auto_tag_memory(text: str) -> list[str]:
    prompt = f"""
Generate 3 short tags for this memory.
Return only comma-separated tags.

Memory:
{text}
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )

    tags_text = response["message"]["content"]

    return [
        tag.strip().lower()
        for tag in tags_text.split(",")
        if tag.strip()
    ]

def find_duplicate_memory(user_id: str, text: str):
    embedding = create_embedding(text)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, text, 1 - (embedding <=> %s::vector) AS similarity
        FROM memories
        WHERE user_id = %s
        AND is_active = TRUE
        AND embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT 1;
        """,
        (embedding, user_id)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row and float(row[2]) >= 0.88:
        return {
            "id": row[0],
            "text": row[1],
            "similarity": round(float(row[2]), 4)
        }

    return None

def calculate_importance(text: str, category: str) -> int:
    important_words = ["goal", "project", "business", "startup", "deadline", "important"]

    score = 3

    if category.lower() in ["business", "project", "career"]:
        score += 1

    if any(word in text.lower() for word in important_words):
        score += 1

    return min(score, 5)


# ============================= Memory Tools ==============================

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

    tags = auto_tag_memory(text)
    duplicate = find_duplicate_memory(user_id, text)

    if duplicate:
        return json.dumps({
            "status": "duplicate_detected",
            "message": "Similar memory already exists.",
            "existing_memory": duplicate
        }, indent=2)
    
    importance = calculate_importance(text, category)

    cur.execute(
        """
        INSERT INTO memories (user_id, text, category, metadata, embedding, tags, importance)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (user_id, text, category, json.dumps(metadata), embedding, tags, importance)
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
        AND is_active = TRUE
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
        AND is_active = TRUE
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
        AND is_active = TRUE
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
        AND is_active = TRUE
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
    """Answer a question using only strongly relevant retrieved memories."""

    search_result = hybrid_search_memory(user_id=user_id, query=question, limit=5)
    data = json.loads(search_result)

    raw_results = data.get("results", [])
    results = filter_relevant_results(raw_results)

    if not results:
        return json.dumps({
            "answer": "I don't have enough memory context.",
            "confidence": "none",
            "sources": []
        }, indent=2)

    confidence = calculate_confidence(results)
    memory_context = build_memory_context(results)
    answer = generate_answer(question, memory_context)

    return json.dumps({
        "answer": answer,
        "confidence": confidence,
        "sources": results
    }, indent=2)

@mcp.tool()
def summarize_memories(user_id: str, topic: str = "") -> str:
    """Summarize memories for a user, optionally by topic."""

    conn = get_conn()
    cur = conn.cursor()

    if topic:
        cur.execute(
            """
            SELECT text, category, tags
            FROM memories
            WHERE user_id = %s
            AND is_active = TRUE
            AND (
                text ILIKE %s
                OR category ILIKE %s
                OR %s = ANY(tags)
            )
            ORDER BY created_at DESC
            LIMIT 20;
            """,
            (user_id, f"%{topic}%", f"%{topic}%", topic.lower())
        )
    else:
        cur.execute(
            """
            SELECT text, category, tags
            FROM memories
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 20;
            """,
            (user_id,)
        )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return "No memories found to summarize."

    memory_text = "\n".join([
        f"- {text} | category: {category} | tags: {tags}"
        for text, category, tags in rows
    ])

    prompt = f"""
Summarize these user memories clearly and briefly.
Group related ideas if useful.

Memories:
{memory_text}

Summary:
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]

@mcp.tool()
def search_by_tag(user_id: str, tag: str) -> str:
    """Search memories by tag using flexible partial matching."""

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, text, category, tags, created_at
        FROM memories
        WHERE user_id = %s
        AND is_active = TRUE
        AND EXISTS (
            SELECT 1
            FROM unnest(tags) AS t
            WHERE t ILIKE %s
        )
        ORDER BY created_at DESC;
        """,
        (user_id, f"%{tag.lower()}%")
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = [
        {
            "id": row[0],
            "text": row[1],
            "category": row[2].strip() if row[2] else None,
            "tags": row[3],
            "created_at": row[4].isoformat()
        }
        for row in rows
    ]

    return json.dumps({"results": results}, indent=2)

@mcp.tool()
def delete_memory(memory_id: int) -> str:
    """Soft delete a memory."""

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE memories
        SET is_active = FALSE, updated_at = NOW()
        WHERE id = %s;
        """,
        (memory_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return f"Memory {memory_id} deleted."

@mcp.tool()
def update_memory(memory_id: int, new_text: str) -> str:
    """Update memory text and refresh embedding/tags."""

    try:
        embedding = create_embedding(new_text)
        tags = auto_tag_memory(new_text)

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE memories
            SET text = %s,
                embedding = %s,
                tags = %s,
                updated_at = NOW()
            WHERE id = %s
            AND is_active = TRUE
            RETURNING id;
            """,
            (new_text, embedding, tags, memory_id)
        )

        updated = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        if not updated:
            return json.dumps({
                "status": "not_found",
                "message": "No active memory found with this id."
            }, indent=2)

        return json.dumps({
            "status": "updated",
            "memory_id": memory_id,
            "new_text": new_text,
            "tags": tags
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2)

if __name__ == "__main__":
    mcp.run()