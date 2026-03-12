"""
Simplified MCP via ROCK test
"""

import asyncio

from rock.actions import CreateBashSessionRequest
from rock.sdk.sandbox.client import Sandbox
from rock.sdk.sandbox.config import SandboxConfig


async def main():
    config = SandboxConfig(
        base_url="http://127.0.0.1:8080",
        image="mcp-helloworld:latest",
        memory="2g",
        cpus=0.5,
        startup_timeout=120,
    )
    sandbox = Sandbox(config)

    print("Starting sandbox...")
    await sandbox.start()
    sandbox_id = sandbox.sandbox_id
    print(f"Sandbox ID: {sandbox_id}")

    print("\nCreating session...")
    await sandbox.create_session(CreateBashSessionRequest(session="mcp"))

    print("\nStarting MCP server...")
    result = await sandbox.arun(cmd="cd /app && nohup python server.py > /tmp/mcp.log 2>&1 &", session="mcp")
    print(f"Result: {result.output}")

    await asyncio.sleep(3)

    print("\nChecking MCP server log...")
    result = await sandbox.arun(cmd="cat /tmp/mcp.log", session="mcp")
    print(f"Log:\n{result.output}")

    print("\nChecking process...")
    result = await sandbox.arun(cmd="ps aux | grep python", session="mcp")
    print(f"Processes:\n{result.output}")

    # Test proxy
    print(f"\n{'=' * 60}")
    print("Testing MCP via ROCK proxy...")
    print(f"{'=' * 60}")

    import httpx

    proxy_url = f"http://127.0.0.1:8080/apis/envs/sandbox/v1/sandboxes/{sandbox_id}/proxy/mcp"
    print(f"Proxy URL: {proxy_url}")

    async with httpx.AsyncClient(timeout=30) as client:
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
        print(f"\nResponse status: {response.status_code}")
        print(f"Response: {response.text[:500]}")

    print("\nStopping sandbox...")
    await sandbox.stop()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
