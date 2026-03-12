"""
MCP Server via ROCK Sandbox Demo

Test MCP server running inside ROCK sandbox with proxy forwarding.
Uses MCP SDK (streamablehttp_client) to connect through ROCK proxy.

This demo uses python:3.11 base image and dynamically uploads server code
and installs dependencies, no pre-built MCP image required.

Prerequisites:
1. Start Redis: docker run -d -p 6379:6379 redis/redis-stack-server:latest
2. Start Admin: rock admin start --env local-proxy --role admin --port 9000
3. Start Proxy: rock admin start --env local-proxy --role proxy --port 9001
"""

import asyncio
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from rock.actions import CreateBashSessionRequest
from rock.sdk.sandbox.client import Sandbox
from rock.sdk.sandbox.config import SandboxConfig

ADMIN_URL = "http://127.0.0.1:9000"
PROXY_URL = "http://127.0.0.1:9001"

# Path to server.py in the same directory
SERVER_PY_PATH = Path(__file__).parent / "server.py"


async def main():
    # 1. Start sandbox with python:3.11 base image
    print("=" * 60)
    print("Step 1: Starting sandbox with python:3.11 image...")
    print("=" * 60)

    config = SandboxConfig(
        base_url=ADMIN_URL,
        image="python:3.11",
        memory="2g",
        cpus=0.5,
        startup_timeout=120,
    )
    sandbox = Sandbox(config)

    try:
        await sandbox.start()
        sandbox_id = sandbox.sandbox_id
        print(f"Sandbox ID: {sandbox_id}")

        # Switch to proxy URL for runtime operations
        sandbox._url = f"{PROXY_URL}/apis/envs/sandbox/v1"

        # 2. Upload server.py to sandbox
        print("\n" + "=" * 60)
        print("Step 2: Uploading MCP server code...")
        print("=" * 60)

        result = await sandbox.upload_by_path(str(SERVER_PY_PATH), "/app/server.py")
        print(f"Upload result: {result.message}")

        # 3. Install MCP dependencies
        print("\n" + "=" * 60)
        print("Step 3: Installing MCP dependencies...")
        print("=" * 60)

        await sandbox.create_session(CreateBashSessionRequest(session="mcp"))

        # Install mcp with Aliyun mirror for faster download (use nohup for long running command)
        # Note: Use absolute path because ROCK rocklet modifies PATH
        result = await sandbox.arun(
            cmd="/usr/local/bin/pip install 'mcp[cli]' -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com",
            session="mcp",
            mode="nohup",
            wait_timeout=300,
        )
        print(f"Install output (last 500 chars):\n...{result.output[-500:]}")

        # 4. Start MCP server
        print("\n" + "=" * 60)
        print("Step 4: Starting MCP server inside sandbox...")
        print("=" * 60)

        result = await sandbox.arun(
            cmd="cd /app && nohup /usr/local/bin/python server.py > /tmp/mcp.log 2>&1 &", session="mcp"
        )
        print(f"Start command: {result.output}")

        await asyncio.sleep(3)

        # Check MCP server log
        result = await sandbox.arun(cmd="cat /tmp/mcp.log", session="mcp")
        print(f"MCP server log:\n{result.output}")

        # 5. Test MCP via ROCK Proxy using MCP SDK
        print("\n" + "=" * 60)
        print("Step 5: Connecting to MCP via ROCK Proxy (using MCP SDK)...")
        print("=" * 60)

        proxy_url = f"{PROXY_URL}/apis/envs/sandbox/v1/sandboxes/{sandbox_id}/proxy/mcp"
        print(f"Proxy URL: {proxy_url}")

        async with streamablehttp_client(proxy_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize
                await session.initialize()
                print("Connected successfully via ROCK proxy!\n")

                # List available tools
                print("=== Available Tools ===")
                tools = await session.list_tools()
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                print()

                # Call hello tool
                print("=== Calling 'hello' tool ===")
                result = await session.call_tool("hello", {"name": "ROCK User"})
                print(f"  Result: {result.content[0].text}\n")

                # Call add tool
                print("=== Calling 'add' tool ===")
                result = await session.call_tool("add", {"a": 100, "b": 200})
                print(f"  Result: {result.content[0].text}\n")

                # Call get_server_info tool
                print("=== Calling 'get_server_info' tool ===")
                result = await session.call_tool("get_server_info", {})
                print(f"  Result: {result.content[0].text}\n")

                # List prompts
                print("=== Available Prompts ===")
                prompts = await session.list_prompts()
                for prompt in prompts.prompts:
                    print(f"  - {prompt.name}: {prompt.description}")
                print()

                # List resources
                print("=== Available Resources ===")
                resources = await session.list_resources()
                for resource in resources.resources:
                    print(f"  - {resource.uri}: {resource.name}")

        print("\n" + "=" * 60)
        print("SUCCESS! MCP SDK works via ROCK proxy!")
        print("=" * 60)

    finally:
        # Keep sandbox running for debugging - comment out stop()
        sandbox._url = f"{ADMIN_URL}/apis/envs/sandbox/v1"
        print(f"\nKeeping sandbox alive for debugging. Sandbox ID: {sandbox.sandbox_id}")
        print("To stop manually: docker stop <sandbox_id>")
        # await sandbox.stop()
        # print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
