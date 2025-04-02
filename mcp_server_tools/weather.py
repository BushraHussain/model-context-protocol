from mcp.server.fastmcp import FastMCP

# initialize FastMCP server
mcp = FastMCP("weather")

# Add a tool to get the weather for a city
@mcp.tool()
async def weather(city:str) -> str:
    """
    Get the weather for a city.
    """
    # This is a placeholder implementation. Replace with actual weather fetching logic.
    return f"The weather in {city} is sunny."

