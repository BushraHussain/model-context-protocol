import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from google import genai

load_dotenv()

# Gemini config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

assert GEMINI_API_KEY, "GEMINI_API_KEY missing in .env"

# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


class GeminiService:
    def __init__(self, model: str):
        self.model = model

    async def generate(self, message: str):
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=self.model,
                contents=message,
            ),
        )
        return response.text


class CliChat:
    def __init__(self, gemini_service, clients, tools):
        self.gemini = gemini_service
        self.clients = clients
        self.tools = tools

    async def run(self):
        print("CLI Chatbot with MCP Agent (type 'exit' to quit)\n")

        while True:
            user_input = input("You: ")

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            # 🔹 Ask Gemini to decide tool usage
            tool_prompt = f"""

    You are an AI agent.

    Available tools:

    1. read_doc_content
    - description: Reads a document
    - required args:
            doc_id (string): filename like "plan.md", "report.pdf"

    2. edit_document
    - description: Edit a document
    - required args:
            doc_id (string)
            old_str (string)
            new_str (string)

    IMPORTANT:
    - If user mentions a filename like "plan.md", use it as doc_id
    - NEVER ask for doc_id if filename is already given
    - ALWAYS extract filename from user query

    User request:
    {user_input}

    Respond ONLY in JSON:

    If tool needed:
    {{
    "tool": "tool_name",
    "args": {{
        "doc_id": "filename_here"
    }}
    }}

    If no tool:
    {{
    "tool": null,
    "answer": "your response"
    }}

User request:
{user_input}

If a tool is needed, respond ONLY in JSON:
{{
  "tool": "tool_name",
  "args": {{...}}
}}

If no tool is needed:
{{
  "tool": null,
  "answer": "your response"
}}
"""

            decision = await self.gemini.generate(tool_prompt)

            # 🔹 Parse decision
            try:
                decision_json = json.loads(decision)
            except:
                print("Bot:", decision, "\n")
                continue

            # 🔹 Tool execution
            if decision_json.get("tool"):
                tool_name = decision_json["tool"]
                args = decision_json.get("args", {})

                result = await self.clients["doc_client"].call_tool(
                    tool_name, args
                )

                # 🔹 Send result back to Gemini
                final_prompt = f"""
Tool result:
{result.content[0].text}

Now answer the user:
{user_input}
"""
                reply = await self.gemini.generate(final_prompt)
                print("Bot:", reply, "\n")

            else:
                print("Bot:", decision_json.get("answer", ""), "\n")


async def main():
    gemini_service = GeminiService(model=MODEL)

    clients = {}

    command = "python"
    args = ["mcp_server.py"]

    async with AsyncExitStack() as stack:
        # connect MCP server
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)
        )
        clients["doc_client"] = doc_client

        # 🔹 fetch tools
        tools = await doc_client.list_tools()

        chat = CliChat(
            gemini_service=gemini_service,
            clients=clients,
            tools=tools,
        )

        await chat.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())