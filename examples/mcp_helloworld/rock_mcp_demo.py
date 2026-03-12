"""
MCP Server via ROCK Sandbox Demo

Demonstrates running an MCP server inside a ROCK sandbox and
accessing it through the ROCK proxy.
"""

import asyncio

from rock.actions import CreateBashSessionRequest
from rock.sdk.sandbox.client import Sandbox
from rock.sdk.sandbox.config import SandboxConfig


async def main():
    # 1. Create sandbox with MCP server image
    print("=" * 60)
    print("Step 1: Starting sandbox with MCP server image...")
    print("=" * 60)

    config = SandboxConfig(
        base_url="http://127.0.0.1:8080",
        image="mcp-helloworld:latest",
        memory="2g",
        cpus=0.5,
        startup_timeout=120,  # Increase timeout
    )
    sandbox = Sandbox(config)

    try:
        await sandbox.start()
        sandbox_id = sandbox.sandbox_id
        print(f"Sandbox started: {sandbox_id}")
        print(f"Host IP: {sandbox._host_ip}")

        # 2. Create a bash session and start MCP server
        print("\n" + "=" * 60)
        print("Step 2: Starting MCP server inside sandbox...")
        print("=" * 60)

        await sandbox.create_session(CreateBashSessionRequest(session="mcp"))

        # Start MCP server in background (it listens on port 8080)
        result = await sandbox.arun(cmd="cd /app && nohup python server.py > /tmp/mcp.log 2>&1 &", session="mcp")
        print(f"Start command result: {result.output}")

        # Wait for server to start
        await asyncio.sleep(3)

        # Check if server is running
        result = await sandbox.arun(cmd="cat /tmp/mcp.log", session="mcp")
        print(f"MCP server log:\n{result.output}")

        # 3. Test MCP connection via ROCK proxy
        print("\n" + "=" * 60)
        print("Step 3: Testing MCP connection via ROCK proxy...")
        print("=" * 60)

        import httpx

        proxy_url = f"http://127.0.0.1:8080/apis/envs/sandbox/v1/sandboxes/{sandbox_id}/proxy/mcp"
        print(f"Proxy URL: {proxy_url}")

        async with httpx.AsyncClient(timeout=30) as client:
            # Send MCP initialize request
            response = await client.post(
                proxy_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "rock-test", "version": "1.0"},
                    },
                },
                headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            )

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response body: {response.text}")

        # 4. Test calling a tool via proxy
        print("\n" + "=" * 60)
        print("Step 4: Calling MCP tool via proxy...")
        print("=" * 60)

        async with httpx.AsyncClient(timeout=30) as client:
            # First we need to call tools/call
            response = await client.post(
                proxy_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "hello", "arguments": {"name": "ROCK User"}},
                },
                headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            )

            print(f"Tool call response: {response.text}")

        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)

    finally:
        # Cleanup
        print("\nStopping sandbox...")
        await sandbox.stop()
        print("Sandbox stopped.")


if __name__ == "__main__":
    asyncio.run(main())
