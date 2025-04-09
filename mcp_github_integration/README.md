# GitHub MCP Server Integration with OpenAI Agent SDK

## Step 1: Set Up the GitHub MCP Server

### 1. Clone the Repository:
```bash
git clone https://github.com/github/github-mcp-server.git
cd github-mcp-server
```

### 2. Build the Docker Image:

```bash
docker build -t github-mcp-server .
```

**Purpose:** This will create a Docker image named github-mcp-server that contains the server.

## Step 2: Obtain a GitHub Personal Access Token (PAT)
The GitHub MCP server requires authentication to interact with GitHub's API.

1. Generate a PAT:

    - Go to GitHub's token settings.

    - Click on Fine-grained Token and create a new fine-grained personal access token:

    - Select one of your organizations as the resource owner.

    - Repository access: Choose Only select repositories and select the repository you want to interact with.

    - Under Permissions, set Repo permissions as read & write for Contents (Repository contents, commits, branches, downloads, releases, and merges).

    - Leave the other permissions unchanged for now.

    - Click Generate new token.

    - Copy the generated token.

**Purpose:** Authenticate the MCP server's requests to GitHub.

## Step 3: Create an OpenAI Agent SDK-based App

1. Create a New UV Project:

```bash
uv init project-name
```

2. Create a New Virtual Environment:

```bash
uv venv
source .venv/bin/activate
```

3. Install the Dependencies:
```bash
uv add openai-agents python-dotenv
```

4. Create an .env File and Add the Following:
```bash
OPENAI_API_KEY=Your_open_ai_key
GITHUB_PERSONAL_ACCESS_TOKEN=Paste_the_generated_token_here
```
5. Create a File Named github_agent.py and Add the MCP Configuration and Agent Code.
6. Run the App:

```bash
uv run github_agent.py
```

## Output:

```bash
GitHub MCP Server running on stdio
🌟 Agent created... running now!
✅ Agent finished

CALLING AGENT

Agent response: The file `test.txt` has been added to the repository with the content "Hello World!" You can view it [here](https://github.com/bushra-hussain/openai-agent-sdk/blob/main/test.txt).

```

That's it! You've successfully set up the GitHub MCP server, generated your GitHub token, and created an OpenAI Agent SDK-based app that interacts with the GitHub API.