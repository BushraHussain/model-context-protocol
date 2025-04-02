# How to Add a Tool in MCP Server

Follow these steps to add and test a resource in an MCP server using the MCP Inspector.

## Steps

1. **Initialize a new UV project**

   ```
    uv init mcp_server_tools
   ```

2. **Create and activate a virtual environment**

    - 💡 Make sure you're working inside your virtual environment before proceeding.

3. **Install MCP with CLI support**

    ```
    uv add "mcp[cli]"
    ```

4. **Create the weather.py file**

    - Add your tool code to a new file named weather.py.

5. **Run the server using MCP Inspector**

    ```
    mcp dev weather.py
    ```
6. Open MCP Inspector

    - Navigate to http://localhost:5173 in your browser. 🚀

7. Test your resource - Open the MCP Inspector UI

    - Click on "Tools"

    - Navigate to the "List tools" tab

    - Click on tool name

    - Test it using the panel on the right side