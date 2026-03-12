"""
MCP Client Example

Connect to the HelloWorld MCP server via streamable-http transport.
"""

import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    server_url = "http://localhost:18080/mcp"
    print(f"Connecting to MCP server at {server_url}...")

    async with streamablehttp_client(server_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            print("Connected successfully!\n")

            # List available tools
            print("=== Available Tools ===")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # Call the hello tool
            print("=== Calling 'hello' tool ===")
            result = await session.call_tool("hello", {"name": "MCP User"})
            print(f"  Result: {result.content[0].text}\n")

            # Call the add tool
            print("=== Calling 'add' tool ===")
            result = await session.call_tool("add", {"a": 10, "b": 20})
            print(f"  Result: {result.content[0].text}\n")

            # Call the get_server_info tool
            print("=== Calling 'get_server_info' tool ===")
            result = await session.call_tool("get_server_info", {})
            print(f"  Result: {result.content[0].text}\n")

            # List available prompts
            print("=== Available Prompts ===")
            prompts = await session.list_prompts()
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}: {prompt.description}")
            print()

            # List available resources
            print("=== Available Resources ===")
            resources = await session.list_resources()
            for resource in resources.resources:
                print(f"  - {resource.uri}: {resource.name}")


if __name__ == "__main__":
    asyncio.run(main())
