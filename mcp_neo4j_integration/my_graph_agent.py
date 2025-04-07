import os
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from agents.run import RunConfig
import requests

# Load the environment variables from the .env file
load_dotenv()

# ------------------ Gemini configuration -------------------

# gemini_api_key = os.getenv("GEMINI_API_KEY")

# # Check if the API key is present; if not, raise an error
# if not gemini_api_key:
#     raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")

# #Reference: https://ai.google.dev/gemini-api/docs/openai
# external_client = AsyncOpenAI(
#     api_key=gemini_api_key,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# )

# model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=external_client
# )

# config = RunConfig(
#     model=model,
#     model_provider=external_client,
#     tracing_disabled=True
# )

# ------------------ Neo4j configuration ------

def query_neo4j(query: str) -> str:
    print(f"\n[TOOL] Sending query to Neo4j MCP: {query}")
    response = requests.post(
        "http://localhost:8000/tools/run_cypher_query/invoke",
        json={"query": query}  
    )
    print(f"[TOOL] Response: {response.status_code} - {response.text}")
    return str(response.json())

@function_tool
def neo4j_tool(query: str) -> str:
    """
    Query a Neo4j database using a Cypher query.
    """
    return query_neo4j(query)


# ------------------ Agent -------------------

async def main():

    # define the agent 
    # Create an Assistant
    agent = Agent(
        name="GraphAgent",
        instructions="You are a helpful agent that uses graph knowledge to answer questions.",
        tools=[neo4j_tool]
    )

    # Run the agent asynchronously using run_sync
    result = await Runner.run(
        agent, 
        "hi who likes the matrix"
    )

    print("\nCALLING AGENT\n")
    print("Agent response:", result.final_output)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())