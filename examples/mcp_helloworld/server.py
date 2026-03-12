"""
FastMCP HelloWorld Server

A simple MCP server example using FastMCP framework.
Demonstrates basic tool and resource implementation.
"""

from mcp.server.fastmcp import FastMCP

# Create the MCP server instance with streamable-http settings
mcp = FastMCP("HelloWorld MCP Server", host="0.0.0.0", port=8080)


@mcp.tool()
def hello(name: str = "World") -> str:
    """
    Say hello to someone.

    Args:
        name: The name to greet (default: "World")

    Returns:
        A friendly greeting message
    """
    return f"Hello, {name}! Welcome to the MCP world! 🎉"


@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return a + b


@mcp.tool()
def get_server_info() -> dict:
    """
    Get information about this MCP server.

    Returns:
        A dictionary containing server information
    """
    return {
        "name": "HelloWorld MCP Server",
        "version": "1.0.0",
        "description": "A simple MCP server built with FastMCP",
        "capabilities": ["hello", "add", "get_server_info"],
    }


@mcp.resource("config://server")
def get_server_config() -> str:
    """
    Get the server configuration as a resource.

    Returns:
        Server configuration in JSON format
    """
    import json

    config = {"server_name": "HelloWorld MCP Server", "version": "1.0.0", "transport": "stdio"}
    return json.dumps(config, indent=2)


@mcp.prompt()
def greeting_prompt(name: str = "User") -> str:
    """
    Generate a greeting prompt template.

    Args:
        name: The name to include in the greeting

    Returns:
        A greeting prompt template
    """
    return f"Please greet {name} in a friendly and professional manner."


if __name__ == "__main__":
    # Run the server with streamable-http transport for network access
    mcp.run(transport="streamable-http")
