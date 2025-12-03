# Import necessary libraries
import asyncio  # For handling asynchronous operations
import os       # For environment variable access
import sys      # For system-specific parameters and functions
import json     # For handling JSON data (used when printing function declarations)

# Import MCP client components
from typing import Optional  # For type hinting optional values
from contextlib import AsyncExitStack  # For managing multiple async tasks
from mcp import ClientSession, StdioServerParameters  # MCP session management
from mcp.client.stdio import stdio_client  # MCP client for standard I/O communication

# Import Google's Gen AI SDK
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration
from google.genai.types import GenerateContentConfig
from dotenv import load_dotenv  # For loading API keys from a .env file

# Load environment variables from .env file
load_dotenv()

class MCPClient:
    def __init__(self):
        """Initialize the MCP client and configure the Gemini API."""
        self.session: Optional[ClientSession] = None  # MCP session for communication
        self.exit_stack = AsyncExitStack()  # Manages async resource cleanup
        self.conversation_history = []  # Maintain conversation history
        
        # Retrieve the Gemini API key from environment variables
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")

        # Configure the Gemini AI client
        self.genai_client = genai.Client(api_key=gemini_api_key)

    async def connect_to_server(self, server_script_path: str):
        """Connect to the MCP server and list available tools."""
        # Determine whether the server script is written in Python or JavaScript
        if server_script_path.endswith('.py'):
            # Use uv run to ensure the server runs in its own virtual environment
            server_dir = os.path.dirname(os.path.abspath(server_script_path))
            script_name = os.path.basename(server_script_path)
            
            # Check if server directory has uv project files
            if os.path.exists(os.path.join(server_dir, 'uv.lock')) or os.path.exists(os.path.join(server_dir, 'pyproject.toml')):
                command = "uv"
                # Use --directory to run from the server's directory
                args = ["run", "--directory", server_dir, "python", script_name]
            else:
                command = "python"
                args = [server_script_path]
        else:
            command = "node"
            args = [server_script_path]

        # Define the parameters for connecting to the MCP server
        server_params = StdioServerParameters(command=command, args=args)

        # Establish communication with the MCP server using standard input/output (stdio)
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))

        # Extract the read/write streams from the transport object
        self.stdio, self.write = stdio_transport

        # Initialize the MCP client session, which allows interaction with the server
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        # Send an initialization request to the MCP server
        await self.session.initialize()

        # Request the list of available tools from the MCP server
        response = await self.session.list_tools()
        tools = response.tools  # Extract the tool list from the response

        # Print a message showing the names of the tools available on the server
        print("\nConnected to server with tools:", [tool.name for tool in tools])

        # Convert MCP tools to Gemini format
        self.function_declarations = convert_mcp_tools_to_gemini(tools)

    def _extract_tool_result(self, result):
        """Extract content from MCP tool result, handling different formats."""
        if not result or not hasattr(result, 'content'):
            return None
        
        content = result.content
        
        # Handle list of content blocks - collect ALL content, not just first
        if isinstance(content, list) and len(content) > 0:
            extracted_parts = []
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

    async def _execute_tool_call(self, tool_name: str, tool_args: dict):
        """Execute a tool call and return the result in a format suitable for Gemini."""
        try:
            result = await self.session.call_tool(tool_name, tool_args)
            extracted_result = self._extract_tool_result(result)
            
            # Debug: print raw result structure (can be removed later)
            # print(f"[DEBUG] Tool {tool_name} returned: {type(extracted_result)} = {extracted_result}")
            
            # If the result is a string that looks like JSON, try to parse it
            if isinstance(extracted_result, str):
                try:
                    parsed = json.loads(extracted_result)
                    return {"result": parsed}
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, return as string
                    return {"result": extracted_result}
            
            return {"result": extracted_result}
        except Exception as e:
            print(f"[Error executing tool {tool_name}: {e}]")
            return {"error": str(e), "result": None}

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
        
        # Add user message to conversation history
        self.conversation_history.append(user_prompt_content)

        # Send user input to Gemini AI and include available tools for function calling
        response = self.genai_client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=self.conversation_history,
            config=types.GenerateContentConfig(
                tools=self.function_declarations,
            ),
        )

        # Initialize variables to store final response text
        final_text = []
        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        # Process the response - handle multiple function calls and follow-up responses
        while iteration < max_iterations:
            iteration += 1
            function_calls_made = False
            
            # Process all candidates in the response
            for candidate in response.candidates:
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if isinstance(part, types.Part):
                            if part.function_call:
                                # Extract function call details
                                function_call_part = part
                                tool_name = function_call_part.function_call.name
                                tool_args = function_call_part.function_call.args

                                # Print debug info
                                print(f"\n[Gemini requested tool call: {tool_name} with args {tool_args}]")

                                # Execute the tool using the MCP server
                                function_response = await self._execute_tool_call(tool_name, tool_args)

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

                                # Add function call and response to conversation history
                                self.conversation_history.append(
                                    types.Content(role='model', parts=[function_call_part])
                                )
                                self.conversation_history.append(function_response_content)
                                
                                function_calls_made = True
                            else:
                                # Direct text response (no function call)
                                if hasattr(part, 'text') and part.text:
                                    final_text.append(part.text)
            
            # If no function calls were made, we're done
            if not function_calls_made:
                break
            
            # Get follow-up response from Gemini after tool execution
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=self.conversation_history,
                config=types.GenerateContentConfig(
                    tools=self.function_declarations,
                ),
            )

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

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []

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

    async def cleanup(self):
        """Clean up resources before exiting."""
        await self.exit_stack.aclose()

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

async def main():
    """Main function to start the MCP client."""
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        # Connect to the MCP server and start the chat loop
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        # Ensure resources are cleaned up
        await client.cleanup()

if __name__ == "__main__":
    # Run the main function within the asyncio event loop
    asyncio.run(main())