# uv run --with mcp mcp run app/mcp_server.py
# cd app mcp-inspector
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Personal Memory Server")


@mcp.tool()
def store_memory(text: str) -> str:
    """Store a memory note."""
    return f"Memory received: {text}"


@mcp.tool()
def search_memory(query: str) -> str:
    """Search memory notes."""
    return f"No memories found for: {query}"


if __name__ == "__main__":
    mcp.run()