"""
MCP Server via Remote ROCK Sandbox Demo

Test MCP server running inside remote ROCK sandbox with proxy forwarding.

Set environment variables before running:
    export ROCK_SANDBOX_AUTH=t-xxx
    export ROCK_SANDBOX_BASE_URL=http://xrl.alibaba-inc.com
"""

import asyncio
import os
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from rock.actions import CreateBashSessionRequest
from rock.sdk.sandbox.client import Sandbox
from rock.sdk.sandbox.config import SandboxConfig

# Get config from environment variables
BASE_URL = os.environ.get("ROCK_SANDBOX_BASE_URL", "http://xrl.alibaba-inc.com")
AUTH_TOKEN = os.environ.get("ROCK_SANDBOX_AUTH", "")

# Path to server.py in the same directory
SERVER_PY_PATH = Path(__file__).parent / "server.py"


async def main():
    print(f"Using ROCK service: {BASE_URL}")
    print(f"Auth token: {AUTH_TOKEN[:10]}..." if AUTH_TOKEN else "No auth token!")

    # 1. Start sandbox with python:3.11 base image
    print("\n" + "=" * 60)
    print("Step 1: Starting sandbox with python:3.11 image...")
    print("=" * 60)

    config = SandboxConfig(
        base_url=BASE_URL,
        image="python:3.11",
        memory="2g",
        cpus=0.5,
        startup_timeout=180,
        auto_clear_seconds=60 * 60,  # 1 hour in seconds
        xrl_authorization=AUTH_TOKEN,
        cluster="vpc-nt-b",
    )
    sandbox = Sandbox(config)

    try:
        await sandbox.start()
        sandbox_id = sandbox.sandbox_id
        print(f"Sandbox ID: {sandbox_id}")

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

        # Install mcp (use nohup for long running command)
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

        await asyncio.sleep(5)

        # Check MCP server log
        result = await sandbox.arun(cmd="cat /tmp/mcp.log", session="mcp")
        print(f"MCP server log:\n{result.output}")

        # 5. Test MCP via ROCK Proxy using MCP SDK
        print("\n" + "=" * 60)
        print("Step 5: Connecting to MCP via ROCK Proxy (using MCP SDK)...")
        print("=" * 60)

        proxy_url = f"{BASE_URL}/apis/envs/sandbox/v1/sandboxes/{sandbox_id}/proxy/mcp"
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
                result = await session.call_tool("hello", {"name": "Remote ROCK User"})
                print(f"  Result: {result.content[0].text}\n")

                # Call add tool
                print("=== Calling 'add' tool ===")
                result = await session.call_tool("add", {"a": 100, "b": 200})
                print(f"  Result: {result.content[0].text}\n")

        print("\n" + "=" * 60)
        print("SUCCESS! MCP SDK works via remote ROCK proxy!")
        print("=" * 60)

    finally:
        print(f"\nKeeping sandbox alive for 1 hour. Sandbox ID: {sandbox.sandbox_id}")
        print(f"Proxy URL: {BASE_URL}/apis/envs/sandbox/v1/sandboxes/{sandbox.sandbox_id}/proxy/mcp")


if __name__ == "__main__":
    asyncio.run(main())
