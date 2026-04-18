import chainlit as cl
import os
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv()


async def main(user_msg: str):

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

        # Retrieve the chat history from the session, if it exists
        history = cl.user_session.get("chat_history", [])

        # Append the user's message to the history
        history.append({"role": "user", "content": user_msg})

        print(f"🌟 History: {history}")

        github_agent = Agent(
            name="github_agent",
            instructions="You are a GitHub Agent. You can access the GitHub API to perform various tasks.",
            mcp_servers=[mcp_github_server]
        )

        # Call the agent and send the history to keep the context
        response = Runner.run_sync(github_agent, history)

        print("✅ Agent finished")
        print("\nCALLING AGENT\n")
        print("Agent response:", response.final_output)

        # Update the session with the new history
        cl.user_session.set("chat_history", response.to_input_list())

        return response.final_output

# =========

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Create a Github repository",
            message="Can you create a Github repository for me?",
            icon="",
        ),
        cl.Starter(
            label="Create a file in the repository",
            message="Can you create a file in the repository?",
            icon="",
        ),
        cl.Starter(
            label="Create a pull request",
            message="Can you create a pull request?",
            icon="",
        ),
        cl.Starter(
            label="Create a branch",
            message="Can you create a branch?",
            icon="",
        ),
    ]

@cl.on_message
async def app(message: cl.Message):
    # Pass the message to the agent with the chat history
    response = await main(message.content)

    print("🌟 response from agent:", response)

    # Send the response to the Chainlit UI
    await cl.Message(
        content=f"Agent: {response}",
    ).send()
