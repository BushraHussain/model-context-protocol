from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server

mcp = FastMCP("Demo")

# add a tool in mcp server
@mcp.tool()
def add(a:int, b:int) -> int:
    """Add two numbers"""
    return a+b

# add a dynamic resource in mcp server
@mcp.resource("greeting://{name}")
def get_greeting(name:str) -> str:
    """Get a personalized greeting"""
    return f"Good morning dear {name}"

