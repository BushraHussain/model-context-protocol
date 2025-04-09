import os
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv()

async def main():
    async with MCPServerStdio(
        params={
            "command": "docker",
                "args": [
                "run",
                "--rm",
                "-i",  # <--- Interactive mode flag that is crucial for stdio-based communication.
                "--env", f"GITHUB_PERSONAL_ACCESS_TOKEN={os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
                "github-mcp-server"
            ],
        },
        cache_tools_list=True
    ) as mcp_github_server:

        github_agent = Agent(
            name="github_agent",
            instructions="You are a GitHub Agent. You can access the GitHub API to perform various tasks.",
            mcp_servers=[mcp_github_server]
        )

        # tools = await mcp_github_server.list_tools()
        # print("🔧 Tools loaded from MCP:", tools)


        print("🌟 Agent created... running now!")

        response = await Runner.run(
            github_agent,
            # "Who created the repo bushra-hussain/openai-agent-sdk? and can u add a new file to it? ",
            "Who created the repo bushra-hussain/openai-agent-sdk? and can u add a new file to it? if yes, then create a file called test.txt with the content 'Hello World!",

        )

        print("✅ Agent finished")
        print("\nCALLING AGENT\n")
        print("Agent response:", response.final_output)


if __name__ == '__main__':
    asyncio.run(main())
