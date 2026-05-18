# uv run --with mcp mcp run app/mcp_server.py
# cd app mcp-inspector

import os
import json
import psycopg2
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("Personal Memory Server")


def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


@mcp.tool()
def store_memory(
    user_id: str,
    text: str,
    category: str = "general",
    metadata: str = "{}"
) -> str:
    """Store a memory note in PostgreSQL."""

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO memories (user_id, text, category, metadata)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """,
        (user_id, text, category, json.dumps(json.loads(metadata)))
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

if __name__ == "__main__":
    mcp.run()