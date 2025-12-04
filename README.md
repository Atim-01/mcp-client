# Building an MCP Client from Scratch: A Complete Guide

## Table of Contents
1. [Introduction & What You'll Build](#introduction--what-youll-build)
2. [Prerequisites](#prerequisites)
3. [Quick Start (For Experienced Developers)](#quick-start-for-experienced-developers)
4. [Detailed Setup from Scratch](#detailed-setup-from-scratch)
5. [Code Architecture Overview](#code-architecture-overview-for-senior-developers)
6. [Detailed Code Walkthrough](#detailed-code-walkthrough-line-by-line-for-beginners)
7. [Using Different LLM Providers](#using-different-llm-providers)
8. [Running the Client](#running-the-client)
9. [Testing Your Setup](#testing-your-setup)
10. [Troubleshooting](#troubleshooting)
11. [Project Structure Reference](#project-structure-reference)
12. [Next Steps & Extensions](#next-steps--extensions)
13. [Additional Resources](#additional-resources)

---

## Introduction & What You'll Build

### What is MCP (Model Context Protocol)?

The **Model Context Protocol (MCP)** is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). Think of it as a universal translator that lets AI assistants (like Claude, ChatGPT, or Gemini) interact with external tools, databases, and services in a consistent way.

### What This Client Does

This MCP client is a **conversational AI interface** that:
- 🔌 **Connects to MCP servers** that provide tools (like file systems, databases, APIs)
- 💬 **Maintains conversation history** for context-aware interactions
- 🛠️ **Executes tool calls** automatically when the LLM needs them
- 🔄 **Handles multi-turn conversations** with intelligent follow-ups
- 🎯 **Works with multiple LLM providers** (Gemini, Claude, or others)

### Key Features

| Feature | Description |
|---------|-------------|
| **Async Architecture** | Non-blocking I/O for efficient communication with MCP servers |
| **Tool Calling Loop** | Automatically executes multiple tool calls in a single conversation turn |
| **Conversation Memory** | Maintains full conversation history for contextual responses |
| **Provider Agnostic** | Easy to swap between different LLM providers (Gemini, Claude, etc.) |
| **Error Handling** | Robust error recovery and informative error messages |
| **Interactive CLI** | Simple command-line interface for testing and exploration |

---

## Prerequisites

### Required Software

1. **Python 3.11 or higher** (3.13 recommended)
   - Check your version: `python --version` or `python3 --version`
   - Download from: [python.org](https://www.python.org/downloads/)

2. **uv Package Manager** (Highly Recommended)
   - **Why uv?** It's 10-100x faster than pip, has better dependency resolution, and makes virtual environment management seamless.
   - Install on Windows:
     ```powershell
     powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - Install on macOS/Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Verify installation: `uv --version`

### Required API Keys

You'll need an API key from one of these providers:

**Option 1: Google Gemini (Primary - This Guide Uses This)**
- Get your API key from: [Google AI Studio](https://aistudio.google.com/apikey)
- Free tier available
- Model used: `gemini-2.0-flash-001`

**Option 2: Anthropic Claude (Alternative)**
- Get your API key from: [Anthropic Console](https://console.anthropic.com/)
- Requires payment setup
- Model options: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`

---

## Quick Start (For Experienced Developers)

If you're already familiar with Python development and just want to get running fast:

```bash
# Create project
uv init mcp-client
cd mcp-client

# Install dependencies
uv add mcp google-genai python-dotenv

# Create .env file with your API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Remove boilerplate
rm hello.py

# Create the client (copy code from this repo's client.py)
# Then run it
uv run client.py path/to/your/mcp-server.py
```

For everyone else, continue to the detailed setup below! 👇

---

## Detailed Setup from Scratch

Let's build this step-by-step, assuming you're starting with nothing.

### Step 1: Create Project Directory

Open your terminal and run:

```bash
uv init mcp-client
cd mcp-client
```

**What this does:**
- `uv init` creates a new Python project with proper structure
- It automatically creates `pyproject.toml` (dependency configuration)
- It generates a sample `hello.py` file (we'll delete this)

### Step 2: Set Up Virtual Environment

```bash
uv venv
```

**What this does:**
- Creates a `.venv` directory containing an isolated Python environment
- This keeps your project dependencies separate from system Python
- **Note:** With `uv`, you often don't need to manually activate the venv! `uv run` handles it automatically.

**If you want to activate manually:**
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

### Step 3: Install Dependencies

```bash
uv add mcp google-genai python-dotenv
```

**What this installs:**

| Package | Purpose | Version |
|---------|---------|---------|
| `mcp` | MCP SDK with CLI tools for connecting to servers | >=1.23.1 |
| `google-genai` | Google's Gemini AI SDK for LLM interactions | >=1.52.0 |
| `python-dotenv` | Loads environment variables from .env files | >=1.2.1 |

**Alternative for Claude users:**
```bash
uv add mcp anthropic python-dotenv
```

### Step 4: Remove Boilerplate Files

```bash
# Windows
del hello.py

# macOS/Linux
rm hello.py
```

### Step 5: Create Environment Variables File

```bash
# Windows
echo. > .env

# macOS/Linux
touch .env
```

Now open `.env` in your text editor and add:

```env
# For Gemini (Primary)
GEMINI_API_KEY=your_actual_api_key_here

# OR for Claude (Alternative)
# ANTHROPIC_API_KEY=your_actual_api_key_here
```

**Important:** Replace `your_actual_api_key_here` with your real API key!

### Step 6: Configure Git Ignore

```bash
echo ".env" >> .gitignore
```

**Why?** This prevents accidentally committing your API keys to version control.

Your `.gitignore` should also include (usually already there):
```
.venv/
__pycache__/
*.pyc
```

### Step 7: Create the Client File

```bash
# Windows
type nul > client.py

# macOS/Linux
touch client.py
```

Now you're ready to add the code! Continue to the next sections to understand what goes in `client.py`.

---

## Code Architecture Overview (For Senior Developers)

Before we dive into line-by-line explanations, here's a high-level overview of the architecture for those who want to understand the big picture quickly.

### Class Structure

```python
MCPClient
├── __init__()                    # Initialize LLM client, setup conversation state
├── connect_to_server()           # Establish stdio connection to MCP server
├── process_query()               # Main query processing loop with tool calling
├── _execute_tool_call()          # Execute single MCP tool call
├── _extract_tool_result()        # Parse tool results from various formats
├── chat_loop()                   # Interactive CLI interface
└── cleanup()                     # Resource cleanup
```

### Key Functions Explained

#### 1. `__init__(self)` - Initialization
**Purpose:** Set up the LLM client and initialize conversation state.

**Key operations:**
- Load API key from environment
- Initialize the LLM client (Gemini/Claude)
- Create conversation history list
- Set up async resource manager (`AsyncExitStack`)

**Why it matters:** Proper initialization prevents runtime errors and sets up state management.

---

#### 2. `connect_to_server(server_script_path: str)` - MCP Server Connection
**Purpose:** Establish a stdio-based connection to an MCP server and discover available tools.

**Key operations:**
- Detect server type (Python with uv, plain Python, or Node.js)
- Configure stdio subprocess parameters
- Initialize MCP client session
- Fetch and convert tool definitions

**Why it matters:** MCP uses stdio (standard input/output) for communication. This function handles the complexity of different server types and environments.

---

#### 3. `process_query(query: str)` - Query Processing Engine
**Purpose:** Core conversation loop that processes user input, calls tools, and generates responses.

**Flow:**
```
User Query → LLM → [Tool Call?] → Execute Tool → LLM → Response
                         ↓
                     [Multiple tool calls possible]
                         ↓
                     [Loop until no more tools needed]
```

**Key operations:**
- Add user message to conversation history
- Send to LLM with available tools
- Detect and execute tool calls
- Loop until final text response
- Update conversation history

**Why it matters:** This implements the "agentic loop" that makes the AI truly useful - it can use tools autonomously to accomplish tasks.

---

#### 4. `_execute_tool_call(tool_name: str, tool_args: dict)` - Tool Execution
**Purpose:** Execute a single tool call via the MCP server and format the result.

**Key operations:**
- Call `session.call_tool()` with tool name and arguments
- Extract result using `_extract_tool_result()`
- Handle errors gracefully
- Format result for LLM consumption

**Why it matters:** Bridges the gap between LLM requests and actual tool execution.

---

#### 5. `_extract_tool_result(result)` - Result Parsing
**Purpose:** Parse MCP tool results that can come in various formats (TextContent, dicts, lists, JSON strings).

**Handles:**
- List of content blocks
- JSON-encoded strings
- Plain text
- Dict objects
- Multiple content parts

**Why it matters:** MCP servers can return data in different formats. This function normalizes everything into a consistent structure the LLM can understand.

---

#### 6. `chat_loop()` - Interactive Interface
**Purpose:** Provide a simple CLI for testing and interacting with the client.

**Features:**
- Read user input in a loop
- Process each query
- Display responses
- Support commands (`quit`, `clear`)

**Why it matters:** Essential for testing and debugging. Simple but effective user interface.

---

### Utility Functions

#### `convert_mcp_tools_to_gemini(mcp_tools)` - Tool Format Conversion
**Purpose:** Convert MCP tool definitions (JSON Schema) to Gemini's FunctionDeclaration format.

**Why needed:** Each LLM provider has its own tool/function calling schema. This converts MCP's standard format to what Gemini expects.

---

#### `clean_schema(schema)` - Schema Cleaning
**Purpose:** Remove `title` fields from JSON Schema definitions.

**Why needed:** Some LLM providers choke on `title` fields in schemas. This recursively removes them while preserving the actual schema structure.

---

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User Input                                                  │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  MCPClient.process_query()                                   │
│  - Add to conversation history                               │
│  - Format for LLM                                            │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM (Gemini/Claude)                                         │
│  - Analyze query with available tools                        │
│  - Decide: respond directly OR call tools                    │
└────────────┬────────────────────────────────────────────────┘
             │
        ┌────┴────┐
        │         │
        ▼         ▼
   Text Response  Tool Call(s)
        │         │
        │         ▼
        │    ┌─────────────────────────────────────┐
        │    │  _execute_tool_call()                │
        │    │  - Call MCP server via stdio         │
        │    └────────────┬────────────────────────┘
        │                 │
        │                 ▼
        │    ┌─────────────────────────────────────┐
        │    │  _extract_tool_result()              │
        │    │  - Parse various formats             │
        │    │  - Normalize to dict                 │
        │    └────────────┬────────────────────────┘
        │                 │
        │                 ▼
        │    ┌─────────────────────────────────────┐
        │    │  Send tool result back to LLM       │
        │    └────────────┬────────────────────────┘
        │                 │
        │                 ▼
        │         [LLM processes result]
        │                 │
        └─────────────────┴──────► Final Response
                                        │
                                        ▼
                              ┌──────────────────────┐
                              │  Display to User     │
                              └──────────────────────┘
```

---

## Detailed Code Walkthrough (Line-by-Line for Beginners)

Now let's build the complete `client.py` file, explaining every line as we go.

### Section 1: Imports and Why We Need Them

```python
# Import necessary libraries
import asyncio  # For handling asynchronous operations
import os       # For environment variable access
import sys      # For system-specific parameters and functions
import json     # For handling JSON data (used when printing function declarations)
```

**Breaking it down:**

- **`asyncio`**: Python's built-in library for asynchronous programming. MCP uses stdio (pipes) for communication, which works best with async code. Think of async as "non-blocking" - while waiting for the MCP server to respond, our program can do other things.

- **`os`**: Provides access to operating system functionality. We use it to read environment variables (like API keys) and check file paths.

- **`sys`**: Gives us access to system-specific parameters. We use `sys.argv` to get command-line arguments (the path to the MCP server).

- **`json`**: Handles JSON (JavaScript Object Notation) data. MCP tools use JSON for parameters and responses, so we need this for parsing.

---

```python
# Import MCP client components
from typing import Optional  # For type hinting optional values
from contextlib import AsyncExitStack  # For managing multiple async tasks
from mcp import ClientSession, StdioServerParameters  # MCP session management
from mcp.client.stdio import stdio_client  # MCP client for standard I/O communication
```

**Breaking it down:**

- **`Optional`**: A type hint that says "this variable can be a specific type OR None". For example, `Optional[ClientSession]` means "either a ClientSession object or None". This helps catch bugs early.

- **`AsyncExitStack`**: A context manager that helps us clean up async resources when we're done. Think of it as making sure all doors are closed and lights are off when leaving a building.

- **`ClientSession`**: The main MCP client class that handles communication with an MCP server.

- **`StdioServerParameters`**: Configuration for how to start and communicate with an MCP server via standard input/output (like piping data to/from a subprocess).

- **`stdio_client`**: The function that actually creates the connection to an MCP server using stdio.

---

```python
# Import Google's Gen AI SDK
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration
from google.genai.types import GenerateContentConfig
from dotenv import load_dotenv  # For loading API keys from a .env file
```

**Breaking it down:**

- **`google.genai`**: Google's official SDK for their Gemini AI models. This is how we'll communicate with Gemini.

- **`types`**: Contains all the data types Gemini uses (like Content, Part, etc.).

- **`Tool` and `FunctionDeclaration`**: Classes for defining tools/functions that Gemini can call. We convert MCP tools into this format.

- **`GenerateContentConfig`**: Configuration object for customizing how Gemini generates responses (including what tools are available).

- **`dotenv`**: Library that loads environment variables from a `.env` file. This keeps our API keys secure and separate from code.

---

```python
# Load environment variables from .env file
load_dotenv()
```

**What this does:**
- Reads the `.env` file in your project directory
- Loads all variables (like `GEMINI_API_KEY=abc123`) into `os.environ`
- Now we can access them with `os.getenv("GEMINI_API_KEY")`

**Why we do this:**
- Keeps secrets out of code (never commit API keys to Git!)
- Makes it easy to use different keys in different environments

---

### Section 2: The MCPClient Class - Initialization

```python
class MCPClient:
    def __init__(self):
        """Initialize the MCP client and configure the Gemini API."""
        self.session: Optional[ClientSession] = None  # MCP session for communication
        self.exit_stack = AsyncExitStack()  # Manages async resource cleanup
        self.conversation_history = []  # Maintain conversation history
```

**Breaking it down:**

- **`class MCPClient:`**: Defines a class (blueprint) for our MCP client. A class bundles data and functions that work together.

- **`def __init__(self):`**: The constructor - runs automatically when you create a new MCPClient instance. It sets up initial state.

- **`self.session: Optional[ClientSession] = None`**: 
  - `self.` means this variable belongs to the instance
  - Starts as `None`, will be set when we connect to a server
  - Stores our active MCP session

- **`self.exit_stack = AsyncExitStack()`**: 
  - Creates a resource manager for async cleanup
  - Think of it as a "cleanup checklist" that ensures we properly close connections

- **`self.conversation_history = []`**: 
  - Empty list to store the conversation
  - Each entry is a message (user or assistant)
  - This gives the AI context from previous turns

---

```python
        # Retrieve the Gemini API key from environment variables
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")
```

**Breaking it down:**

- **`os.getenv("GEMINI_API_KEY")`**: 
  - Looks for an environment variable named `GEMINI_API_KEY`
  - Returns the value if found, or `None` if not found
  - This came from our `.env` file (via `load_dotenv()`)

- **`if not gemini_api_key:`**: 
  - Checks if the key is missing (None or empty string)
  - If so, raises an error to alert the user

- **`raise ValueError(...)`**: 
  - Immediately stops the program with an error message
  - This is a "fail fast" approach - better to crash early with a clear error than fail mysteriously later

**Why this matters:** API keys are required for LLM access. Checking early prevents wasted time and confusing errors.

---

```python
        # Configure the Gemini AI client
        self.genai_client = genai.Client(api_key=gemini_api_key)
```

**Breaking it down:**

- **`genai.Client(api_key=...)`**: Creates a Gemini API client
- **`self.genai_client =`**: Stores it as an instance variable so all methods can use it
- This client handles all communication with Gemini's servers

---

### Section 3: Connecting to an MCP Server

```python
    async def connect_to_server(self, server_script_path: str):
        """Connect to the MCP server and list available tools."""
        # Determine whether the server script is written in Python or JavaScript
        if server_script_path.endswith('.py'):
```

**Breaking it down:**

- **`async def`**: Defines an asynchronous function (can use `await` inside)
- **`server_script_path: str`**: Parameter expecting a string - the path to the MCP server script
- **`if server_script_path.endswith('.py'):`**: Checks if the file is Python (vs Node.js)

---

```python
            # Use uv run to ensure the server runs in its own virtual environment
            server_dir = os.path.dirname(os.path.abspath(server_script_path))
            script_name = os.path.basename(server_script_path)
```

**Breaking it down:**

- **`os.path.abspath(server_script_path)`**: Converts a relative path to absolute (full) path
  - Example: `../server.py` → `/Users/you/projects/server.py`

- **`os.path.dirname(...)`**: Gets the directory part of a path
  - Example: `/Users/you/projects/server.py` → `/Users/you/projects`

- **`os.path.basename(...)`**: Gets just the filename
  - Example: `/Users/you/projects/server.py` → `server.py`

**Why we do this:** We need to run the server from its own directory (so it can find its dependencies), but we might receive a relative path.

---

```python
            # Check if server directory has uv project files
            if os.path.exists(os.path.join(server_dir, 'uv.lock')) or os.path.exists(os.path.join(server_dir, 'pyproject.toml')):
                command = "uv"
                # Use --directory to run from the server's directory
                args = ["run", "--directory", server_dir, "python", script_name]
            else:
                command = "python"
                args = [server_script_path]
```

**Breaking it down:**

- **`os.path.join(server_dir, 'uv.lock')`**: Safely combines path parts
  - Example: `("/Users/you/projects", "uv.lock")` → `/Users/you/projects/uv.lock`
  - Cross-platform (works on Windows, Mac, Linux)

- **`os.path.exists(...)`**: Checks if a file or directory exists

- **Logic**: 
  - If the server uses `uv` (has `uv.lock` or `pyproject.toml`), use `uv run`
  - Otherwise, use regular `python` command

- **Why?** `uv run` automatically handles the server's virtual environment. This prevents dependency conflicts.

---

```python
        else:
            command = "node"
            args = [server_script_path]
```

**Breaking it down:**

- If the server file doesn't end in `.py`, assume it's a Node.js server
- Run it with `node` command

---

```python
        # Define the parameters for connecting to the MCP server
        server_params = StdioServerParameters(command=command, args=args)
```

**Breaking it down:**

- **`StdioServerParameters`**: Configuration object that tells MCP how to start the server
- **`command=command`**: The executable to run (`uv`, `python`, or `node`)
- **`args=args`**: The arguments to pass to that command

**Result examples:**
- For uv Python server: `uv run --directory /path/to/server python server.py`
- For plain Python server: `python /path/to/server.py`
- For Node.js server: `node /path/to/server.js`

---

```python
        # Establish communication with the MCP server using standard input/output (stdio)
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
```

**Breaking it down:**

- **`stdio_client(server_params)`**: Creates an async context manager that:
  1. Starts the MCP server as a subprocess
  2. Connects to its stdin/stdout
  3. Returns read/write streams

- **`await self.exit_stack.enter_async_context(...)`**: 
  - Registers the connection with our cleanup stack
  - When we call `cleanup()` later, this ensures the subprocess is properly terminated
  - `await` means "wait for this async operation to complete"

- **`stdio_transport =`**: Stores the transport object (contains read/write streams)

---

```python
        # Extract the read/write streams from the transport object
        self.stdio, self.write = stdio_transport
```

**Breaking it down:**

- **Tuple unpacking**: `stdio_transport` contains two values (read stream, write stream)
- **`self.stdio`**: Stream for reading from the MCP server
- **`self.write`**: Stream for writing to the MCP server
- These are the "pipes" for bidirectional communication

---

```python
        # Initialize the MCP client session, which allows interaction with the server
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
```

**Breaking it down:**

- **`ClientSession(self.stdio, self.write)`**: Creates an MCP session using our streams
- This session provides high-level methods like `call_tool()`, `list_tools()`, etc.
- Again registered with `exit_stack` for proper cleanup

---

```python
        # Send an initialization request to the MCP server
        await self.session.initialize()
```

**Breaking it down:**

- **`await self.session.initialize()`**: Sends the MCP initialization handshake
- This tells the server we're ready and negotiates protocol details
- Must be done before any other operations

---

```python
        # Request the list of available tools from the MCP server
        response = await self.session.list_tools()
        tools = response.tools  # Extract the tool list from the response

        # Print a message showing the names of the tools available on the server
        print("\nConnected to server with tools:", [tool.name for tool in tools])
```

**Breaking it down:**

- **`await self.session.list_tools()`**: Asks the server "what tools do you provide?"
- Returns a response object with a `tools` attribute
- **`[tool.name for tool in tools]`**: List comprehension - creates a list of just the tool names
- Prints confirmation so the user knows connection succeeded

---

```python
        # Convert MCP tools to Gemini format
        self.function_declarations = convert_mcp_tools_to_gemini(tools)
```

**Breaking it down:**

- Calls our helper function (defined later) to convert tools
- MCP tools use JSON Schema format
- Gemini needs `FunctionDeclaration` format
- This conversion makes the tools usable by Gemini

---

### Section 4: Extracting Tool Results

This is one of the trickier parts because MCP servers can return data in many different formats.

```python
    def _extract_tool_result(self, result):
        """Extract content from MCP tool result, handling different formats."""
        if not result or not hasattr(result, 'content'):
            return None
```

**Breaking it down:**

- **`_extract_tool_result`**: The underscore prefix is a Python convention meaning "private method" (internal use only)
- **`if not result`**: If result is None or empty, return None
- **`hasattr(result, 'content')`**: Checks if result has a `content` attribute
- If result is malformed, fail gracefully by returning None

---

```python
        content = result.content
        
        # Handle list of content blocks - collect ALL content, not just first
        if isinstance(content, list) and len(content) > 0:
            extracted_parts = []
```

**Breaking it down:**

- **`result.content`**: The actual data from the tool
- **`isinstance(content, list)`**: Checks if content is a list
- **`extracted_parts = []`**: Will store all pieces of content we extract

**Why a list?** Some tools return multiple content blocks (e.g., multiple files, multiple results).

---

```python
            for content_block in content:
                # Check if it's a TextContent object with text attribute
                if hasattr(content_block, 'text'):
                    text = content_block.text
                    # Try to parse as JSON if it looks like JSON
                    try:
                        parsed = json.loads(text)
                        extracted_parts.append(parsed)
                    except (json.JSONDecodeError, TypeError):
                        extracted_parts.append(text)
```

**Breaking it down:**

- Loop through each content block
- **`hasattr(content_block, 'text')`**: Check if it's a TextContent object
- **`json.loads(text)`**: Try to parse the text as JSON
  - Example: `'{"name":"John"}'` → `{"name":"John"}` (dict)
- **`except (json.JSONDecodeError, TypeError):`**: If it's not valid JSON, keep as plain text
- Add to `extracted_parts` list

**Why try/except?** Some text looks like JSON but isn't, some tools return JSON strings that need parsing.

---

```python
                # Check if it's a dict with text key
                elif isinstance(content_block, dict):
                    if 'text' in content_block:
                        text = content_block['text']
                        # Try to parse as JSON if it looks like JSON
                        try:
                            parsed = json.loads(text)
                            extracted_parts.append(parsed)
                        except (json.JSONDecodeError, TypeError):
                            extracted_parts.append(text)
                    else:
                        # If it's a dict without 'text', it might be the data itself
                        extracted_parts.append(content_block)
```

**Breaking it down:**

- **`elif isinstance(content_block, dict):`**: If it's already a dictionary
- **`if 'text' in content_block:`**: Check if it has a 'text' key
  - If yes, extract and try to parse it
- **`else:`**: If it's a plain dict, it might be the actual data - use as-is

**Example:**
- `{"text": "{'result': 5}"}` → Try to parse the text
- `{"result": 5}` → Use directly

---

```python
                # Check if it's already a string
                elif isinstance(content_block, str):
                    # Try to parse as JSON
                    try:
                        parsed = json.loads(content_block)
                        extracted_parts.append(parsed)
                    except (json.JSONDecodeError, TypeError):
                        extracted_parts.append(content_block)
                # Try to convert to string
                else:
                    extracted_parts.append(str(content_block))
```

**Breaking it down:**

- **`elif isinstance(content_block, str):`**: If it's a plain string, try to parse as JSON
- **`else:`**: Last resort - convert whatever it is to a string

**This handles edge cases** like numeric results, boolean results, etc.

---

```python
            # If we have multiple parts, combine them appropriately
            if len(extracted_parts) == 1:
                return extracted_parts[0]
            else:
                # If all parts are lists, flatten them
                if all(isinstance(p, list) for p in extracted_parts):
                    flattened = []
                    for p in extracted_parts:
                        flattened.extend(p)
                    return flattened
                return extracted_parts
```

**Breaking it down:**

- **`if len(extracted_parts) == 1:`**: If only one result, return it directly (not wrapped in a list)
- **`all(isinstance(p, list) for p in extracted_parts)`**: Check if ALL parts are lists
  - If so, flatten them: `[[1,2], [3,4]]` → `[1,2,3,4]`
- **`flattened.extend(p)`**: Adds all elements from p to flattened
- Otherwise, return the list of parts as-is

---

```python
        # Handle direct content (string or dict)
        elif isinstance(content, str):
            # Try to parse as JSON
            try:
                return json.loads(content)
            except (json.JSONDecodeError, TypeError):
                return content
        elif isinstance(content, dict):
            return content
        else:
            # Fallback: convert to string
            return str(content) if content else None
```

**Breaking it down:**

- This handles cases where `content` is NOT a list
- Direct string → try to parse as JSON
- Direct dict → return as-is
- Anything else → convert to string

**Why all this complexity?** Different MCP servers format their responses differently. This function normalizes all formats into something consistent.

---

### Section 5: Executing Tool Calls

```python
    async def _execute_tool_call(self, tool_name: str, tool_args: dict):
        """Execute a tool call and return the result in a format suitable for Gemini."""
        try:
            result = await self.session.call_tool(tool_name, tool_args)
            extracted_result = self._extract_tool_result(result)
```

**Breaking it down:**

- **`async def`**: Async because tool execution might take time
- **`tool_name: str`**: Name of the tool to call (e.g., "read_file")
- **`tool_args: dict`**: Arguments for the tool (e.g., `{"path": "/path/to/file"}`)
- **`await self.session.call_tool(...)`**: Sends the tool call request to MCP server
- **`extracted_result = self._extract_tool_result(result)`**: Parses the raw result

---

```python
            # If the result is a string that looks like JSON, try to parse it
            if isinstance(extracted_result, str):
                try:
                    parsed = json.loads(extracted_result)
                    return {"result": parsed}
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, return as string
                    return {"result": extracted_result}
            
            return {"result": extracted_result}
```

**Breaking it down:**

- One more attempt to parse JSON if we got a string
- **Always returns a dict with "result" key**
  - Why? Gemini expects tool results in a consistent format
- Example: `"hello"` → `{"result": "hello"}`
- Example: `'{"count": 5}'` → `{"result": {"count": 5}}`

---

```python
        except Exception as e:
            print(f"[Error executing tool {tool_name}: {e}]")
            return {"error": str(e), "result": None}
```

**Breaking it down:**

- **`except Exception as e:`**: Catches ANY error
- Prints error message to console
- Returns an error dict so the LLM knows something went wrong
- The program continues running (doesn't crash)

**Why?** Tool failures shouldn't crash the entire client. The LLM can handle errors gracefully.

---

### Section 6: Processing User Queries (The Main Loop)

This is the heart of the client - where the magic happens!

```python
    async def process_query(self, query: str) -> str:
        """
        Process a user query using the Gemini API and execute tool calls if needed.
        Args:
            query (str): The user's input query.
        Returns:
            str: The response generated by the Gemini model.
        """
        # Format user input as a structured Content object for Gemini
        user_prompt_content = types.Content(
            role='user',
            parts=[types.Part.from_text(text=query)]
        )
```

**Breaking it down:**

- **`async def process_query(self, query: str) -> str:`**:
  - Takes user's question as string
  - Returns AI's response as string
  - `-> str` is a type hint for the return value

- **`types.Content`**: Gemini's message format
  - **`role='user'`**: This message is from the user
  - **`parts=[...]`**: List of message parts (can be text, images, etc.)
  - **`types.Part.from_text(text=query)`**: Creates a text part from the query

**Example:** If query is "What's 2+2?", this creates:
```python
Content(role='user', parts=[Part(text="What's 2+2?")])
```

---

```python
        # Add user message to conversation history
        self.conversation_history.append(user_prompt_content)
```

**Breaking it down:**

- Adds the user's message to our history list
- This maintains context across multiple turns
- The AI can reference earlier messages

---

```python
        # Send user input to Gemini AI and include available tools for function calling
        response = self.genai_client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=self.conversation_history,
            config=types.GenerateContentConfig(
                tools=self.function_declarations,
            ),
        )
```

**Breaking it down:**

- **`self.genai_client.models.generate_content(...)`**: Calls Gemini API
- **`model='gemini-2.0-flash-001'`**: Specifies which model to use
  - `2.0-flash` is fast and cost-effective
  - You could use `gemini-2.0-pro-001` for more complex reasoning
- **`contents=self.conversation_history`**: Sends full conversation for context
- **`tools=self.function_declarations`**: Tells Gemini what tools are available

**What happens:** Gemini analyzes the conversation and decides whether to:
1. Respond with text directly, OR
2. Call one or more tools first

---

```python
        # Initialize variables to store final response text
        final_text = []
        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        # Process the response - handle multiple function calls and follow-up responses
        while iteration < max_iterations:
            iteration += 1
            function_calls_made = False
```

**Breaking it down:**

- **`final_text = []`**: Will collect all text responses
- **`max_iterations = 10`**: Safety limit to prevent infinite tool-calling loops
- **`function_calls_made = False`**: Tracks if any tools were called this iteration

**Why a loop?** The AI might:
1. Call a tool
2. Get the result
3. Call another tool based on that result
4. Get that result
5. Finally respond with text

This loop handles that entire chain.

---

```python
            # Process all candidates in the response
            for candidate in response.candidates:
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if isinstance(part, types.Part):
                            if part.function_call:
```

**Breaking it down:**

- **`response.candidates`**: Gemini can return multiple response candidates (usually just one)
- **`candidate.content.parts`**: Each candidate has content split into parts
- **`if part.function_call:`**: Check if this part is a tool call (vs. text)

**Structure:**
```
Response
└── Candidates [list]
    └── Candidate
        └── Content
            └── Parts [list]
                ├── Part (text)
                └── Part (function_call)
```

---

```python
                                # Extract function call details
                                function_call_part = part
                                tool_name = function_call_part.function_call.name
                                tool_args = function_call_part.function_call.args

                                # Print debug info
                                print(f"\n[Gemini requested tool call: {tool_name} with args {tool_args}]")
```

**Breaking it down:**

- **`function_call_part.function_call.name`**: The name of the tool to call
- **`function_call_part.function_call.args`**: The arguments (as a dict)
- Prints info so the user sees what's happening

**Example output:**
```
[Gemini requested tool call: read_file with args {'path': '/home/user/data.txt'}]
```

---

```python
                                # Execute the tool using the MCP server
                                function_response = await self._execute_tool_call(tool_name, tool_args)
```

**Breaking it down:**

- Calls our `_execute_tool_call` method
- This sends the request to the MCP server
- Returns the tool's result

---

```python
                                # Format the tool response for Gemini
                                function_response_part = types.Part.from_function_response(
                                    name=tool_name,
                                    response=function_response
                                )

                                # Structure the tool response as a Content object for Gemini
                                function_response_content = types.Content(
                                    role='tool',
                                    parts=[function_response_part]
                                )
```

**Breaking it down:**

- **`types.Part.from_function_response(...)`**: Creates a function response part
  - Includes the tool name and the result
- **`types.Content(role='tool', ...)`**: Wraps it in a Content object
  - `role='tool'` indicates this message is from a tool execution

---

```python
                                # Add function call and response to conversation history
                                self.conversation_history.append(
                                    types.Content(role='model', parts=[function_call_part])
                                )
                                self.conversation_history.append(function_response_content)
                                
                                function_calls_made = True
```

**Breaking it down:**

- Adds TWO messages to history:
  1. The AI's function call request (`role='model'`)
  2. The tool's response (`role='tool'`)
- Sets `function_calls_made = True` to continue the loop
- This maintains complete conversation context

**History example:**
```
[user] "What files are in my directory?"
[model] <calls list_files tool>
[tool] ["file1.txt", "file2.py"]
[model] "Your directory contains file1.txt and file2.py"
```

---

```python
                            else:
                                # Direct text response (no function call)
                                if hasattr(part, 'text') and part.text:
                                    final_text.append(part.text)
```

**Breaking it down:**

- If the part is NOT a function call, it must be text
- **`hasattr(part, 'text')`**: Make sure it has a text attribute
- Add the text to our `final_text` list

---

```python
            # If no function calls were made, we're done
            if not function_calls_made:
                break
```

**Breaking it down:**

- If the AI didn't call any tools, we have our final response
- Break out of the loop

---

```python
            # Get follow-up response from Gemini after tool execution
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=self.conversation_history,
                config=types.GenerateContentConfig(
                    tools=self.function_declarations,
                ),
            )
```

**Breaking it down:**

- Call Gemini again with updated history (now includes tool results)
- Gemini can:
  - Call more tools (loop continues)
  - Respond with final text (loop ends)

**This is the "agentic loop"** - the AI can chain multiple tool calls autonomously.

---

```python
        # Add final response to conversation history
        if final_text:
            response_text = "\n".join(final_text)
            self.conversation_history.append(
                types.Content(
                    role='model',
                    parts=[types.Part.from_text(text=response_text)]
                )
            )

        # Return the combined response as a single formatted string
        return "\n".join(final_text) if final_text else "No response generated."
```

**Breaking it down:**

- **`"\n".join(final_text)`**: Combines all text parts with newlines
  - Example: `["Hello", "World"]` → `"Hello\nWorld"`
- Adds the final response to history
- Returns the combined text to display to the user

---

### Section 7: Helper Methods

```python
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
```

**Breaking it down:**

- Simple helper to reset the conversation
- Useful for starting fresh without restarting the program

---

```python
    async def chat_loop(self):
        """Run an interactive chat session with the user."""
        print("\nMCP Client Started! Type 'quit' to exit, 'clear' to clear history.")
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break
            if query.lower() == 'clear':
                self.clear_history()
                print("Conversation history cleared.")
                continue
            
            # Process the user's query and display the response
            response = await self.process_query(query)
            print("\n" + response)
```

**Breaking it down:**

- **`while True:`**: Infinite loop (until user types 'quit')
- **`input("\nQuery: ")`**: Wait for user input
- **`.strip()`**: Remove leading/trailing whitespace
- **`if query.lower() == 'quit':`**: Check for quit command (case-insensitive)
- **`break`**: Exit the loop
- **`if query.lower() == 'clear':`**: Check for clear command
- **`continue`**: Skip to next iteration without processing
- Otherwise, process the query and print the response

---

```python
    async def cleanup(self):
        """Clean up resources before exiting."""
        await self.exit_stack.aclose()
```

**Breaking it down:**

- **`await self.exit_stack.aclose()`**: Closes all registered async contexts
- This:
  - Closes the MCP session
  - Closes stdio streams
  - Terminates the MCP server subprocess
- Essential for clean shutdown

---

### Section 8: Utility Functions

```python
def clean_schema(schema):
    """
    Recursively removes 'title' fields from the JSON schema.
    Args:
        schema (dict): The schema dictionary.
    Returns:
        dict: Cleaned schema without 'title' fields.
    """
    if isinstance(schema, dict):
        schema.pop("title", None)  # Remove title if present
        # Recursively clean nested properties
        if "properties" in schema and isinstance(schema["properties"], dict):
            for key in schema["properties"]:
                schema["properties"][key] = clean_schema(schema["properties"][key])
    return schema
```

**Breaking it down:**

- **`schema.pop("title", None)`**: Removes 'title' key if it exists
  - `pop` with second argument doesn't raise error if key missing
- **Recursion**: If the schema has nested properties, clean those too
- **Why?** Some LLMs (including Gemini) have issues with 'title' fields in JSON Schema

**Example:**
```python
# Before
{"type": "object", "title": "MyObject", "properties": {"name": {"type": "string", "title": "Name"}}}

# After
{"type": "object", "properties": {"name": {"type": "string"}}}
```

---

```python
def convert_mcp_tools_to_gemini(mcp_tools):
    """
    Converts MCP tool definitions to the correct format for Gemini API function calling.
    Args:
        mcp_tools (list): List of MCP tool objects with 'name', 'description', and 'inputSchema'.
    Returns:
        list: List of Gemini Tool objects with properly formatted function declarations.
    """
    gemini_tools = []
    for tool in mcp_tools:
        # Ensure inputSchema is a valid JSON schema and clean it
        parameters = clean_schema(tool.inputSchema.copy() if hasattr(tool.inputSchema, 'copy') else tool.inputSchema)
```

**Breaking it down:**

- Loops through each MCP tool
- **`tool.inputSchema`**: The JSON Schema defining the tool's parameters
- **`.copy()`**: Creates a copy so we don't modify the original
- **`clean_schema(...)`**: Removes problematic 'title' fields

---

```python
        # Construct the function declaration
        function_declaration = FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=parameters
        )

        # Wrap in a Tool object
        gemini_tool = Tool(function_declarations=[function_declaration])
        gemini_tools.append(gemini_tool)

    return gemini_tools
```

**Breaking it down:**

- **`FunctionDeclaration`**: Gemini's format for defining a callable function
  - Name: what to call it
  - Description: what it does (helps AI decide when to use it)
  - Parameters: JSON Schema of accepted inputs
- **`Tool(function_declarations=[...])`**: Wraps the function declaration
- Collect all tools into a list and return

**Format conversion:**
```
MCP Tool → FunctionDeclaration → Tool → List of Tools
```

---

### Section 9: Main Entry Point

```python
async def main():
    """Main function to start the MCP client."""
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
```

**Breaking it down:**

- **`sys.argv`**: List of command-line arguments
  - `sys.argv[0]` is the script name (`client.py`)
  - `sys.argv[1]` should be the server path
- **`if len(sys.argv) < 2:`**: Check if server path was provided
- **`sys.exit(1)`**: Exit with error code 1 (indicating failure)

---

```python
    client = MCPClient()
    try:
        # Connect to the MCP server and start the chat loop
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        # Ensure resources are cleaned up
        await client.cleanup()
```

**Breaking it down:**

- **`client = MCPClient()`**: Create an instance of our client
- **`try:`**: Start a try block
- **`await client.connect_to_server(sys.argv[1])`**: Connect using provided path
- **`await client.chat_loop()`**: Start the interactive loop
- **`finally:`**: This block ALWAYS runs, even if there's an error or user quits
- **`await client.cleanup()`**: Clean up resources

**Why try/finally?** Ensures cleanup happens even if something goes wrong.

---

```python
if __name__ == "__main__":
    # Run the main function within the asyncio event loop
    asyncio.run(main())
```

**Breaking it down:**

- **`if __name__ == "__main__":`**: Only runs if this file is executed directly (not imported)
- **`asyncio.run(main())`**: Starts the async event loop and runs `main()`
  - This is the entry point for all async code

---

## Using Different LLM Providers

### Current Implementation: Google Gemini

#### Why Gemini?

This implementation uses Google's Gemini for several reasons:

1. **Free Tier**: Generous free quota for development and testing
2. **Latest Features**: Gemini 2.0 has excellent function calling support
3. **Fast Response**: The Flash model is optimized for speed
4. **Simple SDK**: Google's `google-genai` package is straightforward to use
5. **Good Documentation**: Clear examples and API references

#### Model Selection

```python
model='gemini-2.0-flash-001'
```

**Available models:**
- `gemini-2.0-flash-001`: Fast, efficient, great for most tasks
- `gemini-2.0-pro-001`: More capable reasoning, slower, for complex tasks
- `gemini-1.5-flash`: Previous generation, still very capable
- `gemini-1.5-pro`: Previous generation pro model

#### API Setup

The Gemini setup is minimal:

```python
from google import genai

gemini_api_key = os.getenv("GEMINI_API_KEY")
self.genai_client = genai.Client(api_key=gemini_api_key)
```

#### Message Format

Gemini uses a `Content` and `Part` structure:

```python
types.Content(
    role='user',  # or 'model' or 'tool'
    parts=[
        types.Part.from_text(text="Hello"),
        # Can also include images, function calls, etc.
    ]
)
```

---

### Alternative: Anthropic Claude

If you prefer to use Claude instead of Gemini, here's how to adapt the code.

#### Step 1: Change Dependencies

In your terminal:

```bash
# Remove Gemini
uv remove google-genai

# Add Claude
uv add anthropic
```

#### Step 2: Update Environment Variables

In your `.env` file:

```env
# Change from:
# GEMINI_API_KEY=your_key_here

# To:
ANTHROPIC_API_KEY=your_key_here
```

#### Step 3: Modify Imports

Replace the Gemini imports:

```python
# OLD (Gemini)
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration
from google.genai.types import GenerateContentConfig

# NEW (Claude)
from anthropic import Anthropic
```

#### Step 4: Update Initialization

Replace the `__init__` method:

```python
def __init__(self):
    """Initialize the MCP client and configure the Claude API."""
    self.session: Optional[ClientSession] = None
    self.exit_stack = AsyncExitStack()
    self.conversation_history = []  # Format: [{"role": "user", "content": "..."}, ...]
    
    # Retrieve the Anthropic API key
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not found. Please add it to your .env file.")
    
    # Configure the Anthropic client
    self.anthropic_client = Anthropic(api_key=anthropic_api_key)
```

#### Step 5: Adapt Tool Format Conversion

Claude uses a different tool format. Replace `convert_mcp_tools_to_gemini`:

```python
def convert_mcp_tools_to_claude(mcp_tools):
    """
    Converts MCP tool definitions to Claude's tool format.
    Args:
        mcp_tools (list): List of MCP tool objects.
    Returns:
        list: List of tool definitions in Claude format.
    """
    claude_tools = []
    for tool in mcp_tools:
        parameters = clean_schema(
            tool.inputSchema.copy() if hasattr(tool.inputSchema, 'copy') else tool.inputSchema
        )
        
        claude_tool = {
            "name": tool.name,
            "description": tool.description,
            "input_schema": parameters
        }
        claude_tools.append(claude_tool)
    
    return claude_tools
```

#### Step 6: Update `connect_to_server`

Change the tool conversion line:

```python
# OLD (Gemini)
self.function_declarations = convert_mcp_tools_to_gemini(tools)

# NEW (Claude)
self.claude_tools = convert_mcp_tools_to_claude(tools)
```

#### Step 7: Completely Rewrite `process_query`

Claude's API is different. Here's the full replacement:

```python
async def process_query(self, query: str) -> str:
    """
    Process a user query using Claude API and execute tool calls if needed.
    Args:
        query (str): The user's input query.
    Returns:
        str: The response generated by Claude.
    """
    # Add user message to conversation history
    self.conversation_history.append({
        "role": "user",
        "content": query
    })
    
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Call Claude with conversation history and available tools
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=self.conversation_history,
            tools=self.claude_tools
        )
        
        # Add assistant response to history
        assistant_message = {
            "role": "assistant",
            "content": response.content
        }
        self.conversation_history.append(assistant_message)
        
        # Check if Claude wants to use tools
        tool_uses = [block for block in response.content if block.type == "tool_use"]
        
        if not tool_uses:
            # No tools needed, extract text and return
            text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
            return "\n".join(text_blocks) if text_blocks else "No response generated."
        
        # Execute all tool calls
        tool_results = []
        for tool_use in tool_uses:
            print(f"\n[Claude requested tool call: {tool_use.name} with args {tool_use.input}]")
            
            result = await self._execute_tool_call(tool_use.name, tool_use.input)
            
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result)
            })
        
        # Add tool results as a user message
        self.conversation_history.append({
            "role": "user",
            "content": tool_results
        })
    
    return "Maximum iterations reached without final response."
```

#### Comparison Table

| Aspect | Gemini | Claude |
|--------|--------|--------|
| **Package** | `google-genai` | `anthropic` |
| **Client Init** | `genai.Client(api_key=...)` | `Anthropic(api_key=...)` |
| **Message Format** | `Content` objects with `Parts` | Dicts with `role` and `content` |
| **Tool Format** | `FunctionDeclaration` in `Tool` | Dict with `name`, `description`, `input_schema` |
| **API Call** | `client.models.generate_content()` | `client.messages.create()` |
| **Tool Detection** | Check `part.function_call` | Check `block.type == "tool_use"` |
| **Tool Results** | `Content(role='tool', ...)` | User message with `tool_result` type |
| **Free Tier** | Yes, generous | No, requires payment |
| **Streaming** | Supported | Supported |
| **Max Tokens** | Set in model config | Explicit `max_tokens` parameter |

#### Which Should You Choose?

**Choose Gemini if:**
- You want a free option for development
- You need fast responses
- You're building a prototype or personal project

**Choose Claude if:**
- You need the absolute best reasoning capability
- You're building a production application
- Budget isn't a constraint
- You need Claude's specific features (like 200K context window)

---

## Running the Client

### Command Syntax

```bash
uv run client.py <path_to_server_script>
```

**Examples:**

```bash
# Python MCP server with uv
uv run client.py ../my-mcp-server/server.py

# Python MCP server (plain)
uv run client.py /path/to/server.py

# Node.js MCP server
uv run client.py ./server.js
```

### Interactive Commands

Once running, you'll see:

```
Connected to server with tools: ['read_file', 'write_file', 'list_directory']

MCP Client Started! Type 'quit' to exit, 'clear' to clear history.

Query: 
```

**Available commands:**

| Command | Action |
|---------|--------|
| Any text | Processes your query with the AI |
| `quit` | Exits the program |
| `clear` | Clears conversation history (fresh start) |

### Example Session

```
Query: What files are in my current directory?

[Gemini requested tool call: list_directory with args {'path': '.'}]

Your current directory contains:
- client.py
- pyproject.toml
- .env
- README.md

Query: Read the pyproject.toml file

[Gemini requested tool call: read_file with args {'path': 'pyproject.toml'}]

The pyproject.toml file contains your project configuration:
- Project name: mcp-client
- Python version: >=3.13
- Dependencies: google-genai, mcp, python-dotenv

Query: quit
```

---

## Testing Your Setup

### 1. Verify MCP Server Connection

**Good output:**
```
Connected to server with tools: ['tool1', 'tool2', 'tool3']
MCP Client Started! Type 'quit' to exit, 'clear' to clear history.
```

**Bad output:**
```
Error: Could not connect to server
```

**Fix:** Check that:
- Server path is correct
- Server file is executable
- Server dependencies are installed

---

### 2. Test a Simple Tool Call

Try a query that should trigger a tool:

```
Query: Use the [tool_name] tool to [do something]
```

**Good output:**
```
[Gemini requested tool call: tool_name with args {...}]
[Tool response shown]
```

**Bad output:**
```
I don't have access to that tool.
```

**Fix:**
- Make sure the tool is listed in "Connected to server with tools"
- Be specific about what you want

---

### 3. Test Conversation Memory

```
Query: My favorite color is blue

Response: Got it, I'll remember that your favorite color is blue.

Query: What's my favorite color?

Response: Your favorite color is blue.
```

If the second response doesn't remember, check that:
- You're not calling `clear` between messages
- The `conversation_history` isn't being reset

---

### 4. Debugging Tips

**Enable detailed logging:**

Add this after imports:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Print conversation history:**

Add to `process_query`:

```python
print(f"[DEBUG] Conversation has {len(self.conversation_history)} messages")
```

**Print raw tool results:**

In `_extract_tool_result`, uncomment:

```python
print(f"[DEBUG] Tool returned: {type(extracted_result)} = {extracted_result}")
```

---

## Troubleshooting

### Error: "GEMINI_API_KEY not found"

**Cause:** API key not set in `.env` file.

**Fix:**
1. Create `.env` file in project root
2. Add: `GEMINI_API_KEY=your_actual_key`
3. Restart the client

---

### Error: "Module not found: mcp" or "google"

**Cause:** Dependencies not installed.

**Fix:**
```bash
uv add mcp google-genai python-dotenv
```

---

### Error: "Could not connect to server"

**Possible causes:**
1. Wrong server path
2. Server has errors
3. Missing server dependencies

**Fix:**
```bash
# Test server directly
python path/to/server.py

# Or for Node.js
node path/to/server.js

# Check server has dependencies
cd path/to/server
uv sync  # for Python with uv
# or npm install for Node.js
```

---

### Error: "Maximum iterations reached"

**Cause:** Tool calling loop didn't terminate (AI kept calling tools).

**Possible reasons:**
- Tool returning malformed results
- AI stuck in a loop
- Bug in tool logic

**Fix:**
1. Check tool result format
2. Try `clear` to reset conversation
3. Increase `max_iterations` if needed (but investigate root cause)

---

### Tools Not Being Called

**Symptoms:** AI responds with text instead of using tools.

**Causes:**
1. Query not specific enough
2. Tool description unclear
3. Tool schema has errors

**Fix:**
- Be explicit: "Use the read_file tool to read example.txt"
- Check tool descriptions are clear
- Verify tool schemas are valid JSON Schema

---

### API Rate Limiting

**Error:** "429 Too Many Requests" or "Resource exhausted"

**Fix:**
- Wait a few seconds between requests
- Check your API quota/limits
- Consider upgrading API plan

---

### Windows-Specific: Path Issues

**Problem:** Server path not found on Windows.

**Fix:** Use forward slashes or raw strings:
```bash
# Good
uv run client.py ../server/server.py

# Also good
uv run client.py C:/Users/You/server/server.py

# Or in Python code use raw string
r"C:\Users\You\server\server.py"
```

---

## Project Structure Reference

After completing all setup steps, your project should look like this:

```
mcp-client/
├── .venv/                      # Virtual environment (created by uv venv)
│   ├── Scripts/                # (Windows) or bin/ (Unix)
│   ├── Lib/
│   └── ...
├── client.py                   # Main MCP client code (YOU CREATE THIS)
├── main.py                     # Boilerplate (can be ignored or deleted)
├── pyproject.toml              # Project metadata and dependencies
├── uv.lock                     # Locked dependency versions
├── .env                        # API keys (YOU CREATE THIS)
├── .gitignore                  # Git ignore rules
└── README.md                   # This documentation
```

### File Descriptions

| File | Purpose | Created By |
|------|---------|------------|
| `client.py` | Main MCP client implementation | You |
| `pyproject.toml` | Python project configuration, dependencies | `uv init` |
| `uv.lock` | Locked dependency versions for reproducibility | `uv add` |
| `.env` | Environment variables (API keys) | You |
| `.venv/` | Isolated Python environment | `uv venv` |
| `.gitignore` | Files to exclude from version control | `uv init` |
| `README.md` | Documentation (this file) | You/Updated |

### Important Notes

**Don't commit to Git:**
- `.env` (contains secrets!)
- `.venv/` (too large, easily recreated)
- `__pycache__/` (Python bytecode)

**Do commit to Git:**
- `client.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `.gitignore`

---

## Next Steps & Extensions

Congratulations! You now have a fully functional MCP client. Here are ideas for extending it:

### 1. Add More MCP Servers

Connect to multiple servers simultaneously:

```python
# In __init__
self.sessions = []  # List of sessions

# Create multiple connections
await client.connect_to_server("server1.py")
await client.connect_to_server("server2.js")

# Merge tool lists
all_tools = self.sessions[0].tools + self.sessions[1].tools
```

---

### 2. Implement Streaming Responses

Get responses word-by-word instead of all at once:

**For Gemini:**

```python
response_stream = self.genai_client.models.generate_content_stream(
    model='gemini-2.0-flash-001',
    contents=self.conversation_history,
    config=types.GenerateContentConfig(tools=self.function_declarations),
)

for chunk in response_stream:
    if chunk.text:
        print(chunk.text, end='', flush=True)
```

---

### 3. Build a GUI Interface

Replace the CLI with a graphical interface using:

**Option A: Tkinter (built-in)**
```python
import tkinter as tk
from tkinter import scrolledtext

class MCPClientGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MCP Client")
        
        self.chat_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.chat_display.pack(expand=True, fill='both')
        
        self.input_field = tk.Entry(self.root)
        self.input_field.pack(fill='x')
        self.input_field.bind('<Return>', self.send_message)
    
    def send_message(self, event):
        query = self.input_field.get()
        # Process with MCP client...
```

**Option B: Streamlit (web-based)**
```bash
uv add streamlit
```

```python
import streamlit as st

st.title("MCP Client")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    response = asyncio.run(client.process_query(prompt))
    st.session_state.messages.append({"role": "assistant", "content": response})
```

---

### 4. Advanced Error Recovery

Add retry logic for transient failures:

```python
async def _execute_tool_call_with_retry(self, tool_name: str, tool_args: dict, max_retries=3):
    """Execute tool call with automatic retry on failure."""
    for attempt in range(max_retries):
        try:
            return await self._execute_tool_call(tool_name, tool_args)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"[Retry {attempt + 1}/{max_retries}] Tool call failed: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

### 5. Conversation Persistence

Save and load conversation history:

```python
import json
from datetime import datetime

def save_conversation(self, filename=None):
    """Save conversation history to a JSON file."""
    if filename is None:
        filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(self.conversation_history, f, indent=2)
    
    print(f"Conversation saved to {filename}")

def load_conversation(self, filename):
    """Load conversation history from a JSON file."""
    with open(filename, 'r') as f:
        self.conversation_history = json.load(f)
    
    print(f"Conversation loaded from {filename}")
```

**Usage:**
```python
# In chat_loop, add new commands:
if query.lower() == 'save':
    self.save_conversation()
    continue
if query.lower().startswith('load '):
    filename = query[5:].strip()
    self.load_conversation(filename)
    continue
```

---

### 6. Multiple Model Support

Switch between models dynamically:

```python
def set_model(self, model_name: str):
    """Change the LLM model being used."""
    valid_models = [
        'gemini-2.0-flash-001',
        'gemini-2.0-pro-001',
        'gemini-1.5-flash',
        'gemini-1.5-pro'
    ]
    
    if model_name not in valid_models:
        print(f"Invalid model. Choose from: {valid_models}")
        return
    
    self.current_model = model_name
    print(f"Switched to model: {model_name}")
```

---

### 7. Tool Usage Analytics

Track which tools are being used:

```python
from collections import Counter

class MCPClient:
    def __init__(self):
        # ... existing code ...
        self.tool_usage_stats = Counter()
    
    async def _execute_tool_call(self, tool_name: str, tool_args: dict):
        self.tool_usage_stats[tool_name] += 1
        # ... rest of existing code ...
    
    def show_stats(self):
        """Display tool usage statistics."""
        print("\n=== Tool Usage Statistics ===")
        for tool, count in self.tool_usage_stats.most_common():
            print(f"{tool}: {count} times")
```

---

### 8. Custom System Prompts

Add personality or specialized behavior:

```python
def __init__(self, system_prompt=None):
    # ... existing code ...
    
    if system_prompt:
        # For Gemini, add as first user message
        self.conversation_history.append(
            types.Content(
                role='user',
                parts=[types.Part.from_text(text=f"System: {system_prompt}")]
            )
        )
```

**Usage:**
```python
client = MCPClient(
    system_prompt="You are a helpful coding assistant. Always explain your reasoning."
)
```

---

### 9. Async Tool Execution

Execute multiple tools in parallel:

```python
async def _execute_tool_calls_parallel(self, tool_calls):
    """Execute multiple tool calls concurrently."""
    tasks = [
        self._execute_tool_call(call.name, call.args) 
        for call in tool_calls
    ]
    return await asyncio.gather(*tasks)
```

---

### 10. Web API Server

Turn your client into an API:

```bash
uv add fastapi uvicorn
```

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
client = None  # Initialize globally

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"

@app.post("/query")
async def process_query_endpoint(request: QueryRequest):
    try:
        response = await client.process_query(request.query)
        return {"response": response, "session_id": request.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear")
async def clear_history_endpoint():
    client.clear_history()
    return {"status": "cleared"}

# Run with: uvicorn your_file:app --reload
```

---

## Additional Resources

### Official Documentation

- **MCP Documentation**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **MCP Python SDK**: [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- **Google Gemini API**: [ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)
- **Anthropic Claude API**: [docs.anthropic.com](https://docs.anthropic.com)
- **uv Package Manager**: [docs.astral.sh/uv](https://docs.astral.sh/uv)

### Example MCP Servers

Try these open-source MCP servers:

1. **Filesystem Server**: Browse files and directories
   ```bash
   git clone https://github.com/modelcontextprotocol/servers
   cd servers/src/filesystem
   uv run client.py path/to/servers/src/filesystem/index.js
   ```

2. **GitHub Server**: Interact with GitHub repos
   ```bash
   # Install from MCP servers repository
   npm install @modelcontextprotocol/server-github
   ```

3. **PostgreSQL Server**: Query databases
   ```bash
   # Python-based server
   pip install mcp-server-postgres
   ```

4. **Web Search Server**: Search the internet
   ```bash
   # Check MCP server directory for web search implementations
   ```

### Community & Support

- **MCP GitHub Discussions**: Ask questions and share projects
- **Discord**: Join the MCP community (link in official docs)
- **Stack Overflow**: Tag questions with `model-context-protocol`

### Learning Resources

- **AsyncIO Tutorial**: [realpython.com/async-io-python](https://realpython.com/async-io-python)
- **JSON Schema Guide**: [json-schema.org/learn](https://json-schema.org/learn)
- **LLM Function Calling**: Understanding how AI uses tools
- **Python Type Hints**: [mypy.readthedocs.io](https://mypy.readthedocs.io)

---

## Conclusion

You've now built a complete, production-ready MCP client from scratch! This guide covered:

✅ **Setup**: From zero to running in minutes  
✅ **Code Architecture**: Understanding the high-level design  
✅ **Line-by-Line Walkthrough**: Deep dive into every function  
✅ **Multi-Provider Support**: Gemini and Claude alternatives  
✅ **Testing & Debugging**: Ensuring everything works  
✅ **Extensions**: Ideas for taking it further  

### Key Takeaways

1. **MCP standardizes tool access** - One protocol, many AI providers
2. **Async is essential** - Stdio communication requires async/await
3. **Conversation history enables context** - The AI remembers previous turns
4. **Tool format conversion is crucial** - Each LLM has specific requirements
5. **Error handling prevents crashes** - Robust code handles edge cases

### What's Next?

1. **Build your own MCP server** - Create custom tools for your needs
2. **Experiment with different models** - Compare Gemini, Claude, GPT-4
3. **Add advanced features** - Streaming, GUI, persistence
4. **Share your creation** - Contribute back to the community

**Happy coding!** 🚀

---

## License

This guide and code are provided as educational resources. Feel free to use, modify, and distribute.

## Contributing

Found an issue or want to improve this guide?

1. Fork the repository
2. Make your changes
3. Submit a pull request
4. Or open an issue for discussion

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Author**: Built with Claude and the MCP community