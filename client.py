"""
MCP Client Implementation
A client that connects to MCP servers and enables LLMs to use tools via function calling.

This implementation uses Google Gemini as the LLM provider and communicates with
MCP servers through stdio (standard input/output).
"""

# Standard library imports
import asyncio
import os
import sys
import json

# MCP SDK imports
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Google Gemini AI imports
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration
from google.genai.types import GenerateContentConfig

# Environment management
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    """
    MCP Client that bridges LLMs with MCP servers for tool execution.
    
    This client:
    - Connects to MCP servers via stdio
    - Processes user queries through Gemini AI
    - Executes tool calls requested by the LLM
    - Maintains conversation history for context
    """
    
    def __init__(self):
        """Initialize the MCP client with Gemini AI configuration."""
        # MCP session management
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Conversation state
        self.conversation_history = []
        
        # Load and validate API key
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")

        # Initialize Gemini client
        self.genai_client = genai.Client(api_key=gemini_api_key)

    async def connect_to_server(self, server_script_path: str):
        """
        Establish connection to an MCP server and discover available tools.
        
        Supports Python servers (with or without uv) and Node.js servers.
        Uses stdio for bidirectional communication with the server subprocess.
        """
        # Determine command based on server type
        if server_script_path.endswith('.py'):
            server_dir = os.path.dirname(os.path.abspath(server_script_path))
            script_name = os.path.basename(server_script_path)
            
            # Use uv if the server has uv project files for dependency isolation
            if os.path.exists(os.path.join(server_dir, 'uv.lock')) or os.path.exists(os.path.join(server_dir, 'pyproject.toml')):
                command = "uv"
                args = ["run", "--directory", server_dir, "python", script_name]
            else:
                command = "python"
                args = [server_script_path]
        else:
            # Assume Node.js for non-Python files
            command = "node"
            args = [server_script_path]

        # Configure server subprocess parameters
        server_params = StdioServerParameters(command=command, args=args)

        # Start server and establish stdio communication
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport

        # Create MCP session for high-level server interaction
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        # Initialize MCP protocol handshake
        await self.session.initialize()

        # Discover available tools from server
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

        # Convert MCP tool format to Gemini's function calling format
        self.function_declarations = convert_mcp_tools_to_gemini(tools)

    def _extract_tool_result(self, result):
        """
        Extract and normalize content from MCP tool results.
        
        MCP servers can return data in various formats:
        - TextContent objects with .text attribute
        - Dictionaries with 'text' key
        - Raw strings (possibly JSON-encoded)
        - Lists of content blocks
        
        This method handles all formats and attempts JSON parsing where applicable.
        """
        if not result or not hasattr(result, 'content'):
            return None
        
        content = result.content
        
        # Case 1: List of content blocks
        if isinstance(content, list) and len(content) > 0:
            extracted_parts = []
            
            for content_block in content:
                # TextContent object with .text attribute
                if hasattr(content_block, 'text'):
                    text = content_block.text
                    try:
                        extracted_parts.append(json.loads(text))
                    except (json.JSONDecodeError, TypeError):
                        extracted_parts.append(text)
                
                # Dictionary with 'text' key
                elif isinstance(content_block, dict):
                    if 'text' in content_block:
                        text = content_block['text']
                        try:
                            extracted_parts.append(json.loads(text))
                        except (json.JSONDecodeError, TypeError):
                            extracted_parts.append(text)
                    else:
                        extracted_parts.append(content_block)
                
                # Plain string
                elif isinstance(content_block, str):
                    try:
                        extracted_parts.append(json.loads(content_block))
                    except (json.JSONDecodeError, TypeError):
                        extracted_parts.append(content_block)
                
                # Fallback: convert to string
                else:
                    extracted_parts.append(str(content_block))
            
            # Return single item unwrapped, or combine multiple parts
            if len(extracted_parts) == 1:
                return extracted_parts[0]
            elif all(isinstance(p, list) for p in extracted_parts):
                # Flatten if all parts are lists
                flattened = []
                for p in extracted_parts:
                    flattened.extend(p)
                return flattened
            else:
                return extracted_parts
        
        # Case 2: Direct string content
        elif isinstance(content, str):
            try:
                return json.loads(content)
            except (json.JSONDecodeError, TypeError):
                return content
        
        # Case 3: Direct dict content
        elif isinstance(content, dict):
            return content
        
        # Case 4: Fallback for unknown types
        else:
            return str(content) if content else None

    async def _execute_tool_call(self, tool_name: str, tool_args: dict):
        """
        Execute a tool via the MCP server and format the result for Gemini.
        
        Returns a dict with 'result' key (or 'error' on failure) as expected by Gemini's
        function calling protocol.
        """
        try:
            # Call the tool through MCP session
            result = await self.session.call_tool(tool_name, tool_args)
            extracted_result = self._extract_tool_result(result)
            
            # Additional JSON parsing attempt for string results
            if isinstance(extracted_result, str):
                try:
                    parsed = json.loads(extracted_result)
                    return {"result": parsed}
                except (json.JSONDecodeError, TypeError):
                    return {"result": extracted_result}
            
            return {"result": extracted_result}
        except Exception as e:
            print(f"[Error executing tool {tool_name}: {e}]")
            return {"error": str(e), "result": None}

    async def process_query(self, query: str) -> str:
        """
        Process user query through Gemini with automatic tool execution.
        
        Flow:
        1. Send query + conversation history to Gemini
        2. If Gemini requests tool calls, execute them via MCP
        3. Send tool results back to Gemini
        4. Repeat until Gemini returns a text response
        5. Return final response to user
        
        This implements the "agentic loop" where the LLM can chain multiple
        tool calls autonomously to accomplish complex tasks.
        """
        # Format and store user message
        user_prompt_content = types.Content(
            role='user',
            parts=[types.Part.from_text(text=query)]
        )
        self.conversation_history.append(user_prompt_content)

        # Initial LLM call with full context
        response = self.genai_client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=self.conversation_history,
            config=types.GenerateContentConfig(
                tools=self.function_declarations,
            ),
        )

        final_text = []
        max_iterations = 10
        iteration = 0

        # Agentic loop: handle tool calls until we get a final text response
        while iteration < max_iterations:
            iteration += 1
            function_calls_made = False
            
            # Parse response for function calls or text
            for candidate in response.candidates:
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if isinstance(part, types.Part):
                            if part.function_call:
                                # LLM requested a tool call
                                function_call_part = part
                                tool_name = function_call_part.function_call.name
                                tool_args = function_call_part.function_call.args

                                print(f"\n[Gemini requested tool call: {tool_name} with args {tool_args}]")

                                # Execute tool via MCP
                                function_response = await self._execute_tool_call(tool_name, tool_args)

                                # Format tool result for Gemini
                                function_response_part = types.Part.from_function_response(
                                    name=tool_name,
                                    response=function_response
                                )
                                function_response_content = types.Content(
                                    role='tool',
                                    parts=[function_response_part]
                                )

                                # Update conversation history with call + result
                                self.conversation_history.append(
                                    types.Content(role='model', parts=[function_call_part])
                                )
                                self.conversation_history.append(function_response_content)
                                
                                function_calls_made = True
                            else:
                                # LLM returned text (final response)
                                if hasattr(part, 'text') and part.text:
                                    final_text.append(part.text)
            
            # Exit loop if no tools were called
            if not function_calls_made:
                break
            
            # Get next response from Gemini with updated context
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=self.conversation_history,
                config=types.GenerateContentConfig(
                    tools=self.function_declarations,
                ),
            )

        # Store final response in history
        if final_text:
            response_text = "\n".join(final_text)
            self.conversation_history.append(
                types.Content(
                    role='model',
                    parts=[types.Part.from_text(text=response_text)]
                )
            )

        return "\n".join(final_text) if final_text else "No response generated."

    def clear_history(self):
        """Reset conversation history for a fresh context."""
        self.conversation_history = []

    async def chat_loop(self):
        """
        Interactive CLI for the MCP client.
        
        Commands:
        - 'quit': Exit the client
        - 'clear': Clear conversation history
        - Any other input: Process as a query
        """
        print("\nMCP Client Started! Type 'quit' to exit, 'clear' to clear history.")
        while True:
            query = input("\nQuery: ").strip()
            
            if query.lower() == 'quit':
                break
            
            if query.lower() == 'clear':
                self.clear_history()
                print("Conversation history cleared.")
                continue
            
            response = await self.process_query(query)
            print("\n" + response)

    async def cleanup(self):
        """Close MCP session and clean up async resources."""
        await self.exit_stack.aclose()

def clean_schema(schema):
    """
    Remove 'title' fields from JSON Schema recursively.
    
    Some LLM providers have issues with 'title' fields in JSON Schema.
    This function removes them while preserving all other schema properties.
    """
    if isinstance(schema, dict):
        schema.pop("title", None)
        
        # Recursively clean nested properties
        if "properties" in schema and isinstance(schema["properties"], dict):
            for key in schema["properties"]:
                schema["properties"][key] = clean_schema(schema["properties"][key])
    
    return schema

def convert_mcp_tools_to_gemini(mcp_tools):
    """
    Convert MCP tool definitions to Gemini's function calling format.
    
    MCP uses JSON Schema for tool parameters. Gemini requires FunctionDeclaration
    objects wrapped in Tool objects. This function bridges the two formats.
    
    Args:
        mcp_tools: List of MCP tool objects (name, description, inputSchema)
    
    Returns:
        List of Gemini Tool objects ready for function calling
    """
    gemini_tools = []
    
    for tool in mcp_tools:
        # Copy and clean the JSON Schema
        parameters = clean_schema(
            tool.inputSchema.copy() if hasattr(tool.inputSchema, 'copy') else tool.inputSchema
        )

        # Create Gemini function declaration
        function_declaration = FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=parameters
        )

        # Wrap in Tool object (Gemini's required format)
        gemini_tool = Tool(function_declarations=[function_declaration])
        gemini_tools.append(gemini_tool)

    return gemini_tools

async def main():
    """
    Main entry point for the MCP client.
    
    Usage: python client.py <path_to_server_script>
    
    Example: python client.py ../my-server/server.py
    """
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())