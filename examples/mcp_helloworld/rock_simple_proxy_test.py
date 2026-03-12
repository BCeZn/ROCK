"""
Simple FastAPI Server Proxy Test

Test ROCK proxy with a FastAPI server.
"""

import asyncio
import os

import httpx

from rock.actions import CreateBashSessionRequest
from rock.sdk.sandbox.client import Sandbox
from rock.sdk.sandbox.config import SandboxConfig

# Remote ROCK service
BASE_URL = os.environ.get("ROCK_SANDBOX_BASE_URL", "http://xrl.alibaba-inc.com")
AUTH_TOKEN = os.environ.get("ROCK_SANDBOX_AUTH", "")

print(f"Using ROCK service: {BASE_URL}")
print(f"Auth token: {AUTH_TOKEN[:12]}..." if AUTH_TOKEN else "No auth token!")

# FastAPI server code
FASTAPI_SERVER_CODE = """
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy", "message": "FastAPI server is running!"}

@app.post("/health")
def health_post():
    return {"status": "healthy", "method": "POST"}

@app.get("/")
def root():
    return {"message": "Hello from FastAPI!"}

@app.post("/echo")
def echo(data: dict):
    return {"echo": data}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""


async def main():
    config = SandboxConfig(
        base_url=BASE_URL,
        image="python:3.11",
        memory="1g",
        cpus=0.5,
        startup_timeout=120,
        auto_clear_seconds=60 * 60,
        xrl_authorization=AUTH_TOKEN,
        cluster="vpc-nt-b",
    )

    sandbox = Sandbox(config)

    try:
        await sandbox.start()
        sandbox_id = sandbox.sandbox_id
        print("=" * 60)
        print(f"Step 1: Sandbox created: {sandbox_id}")
        print("=" * 60)

        # Upload FastAPI server
        print("Step 2: Uploading FastAPI server...")
        result = await sandbox.write_file_by_path(FASTAPI_SERVER_CODE, "/app/server.py")
        print(f"Upload done: {result.message}")

        # Create session and install dependencies
        print("=" * 60)
        print("Step 3: Installing FastAPI + uvicorn...")
        print("=" * 60)
        await sandbox.create_session(CreateBashSessionRequest(session="server"))

        result = await sandbox.arun(
            cmd="/usr/local/bin/pip install fastapi uvicorn -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -q",
            session="server",
            mode="nohup",
            wait_timeout=120,
        )
        print(f"Install result: {result.output[-200:]}")

        # Start FastAPI server
        print("=" * 60)
        print("Step 4: Starting FastAPI server on port 8080...")
        print("=" * 60)
        result = await sandbox.arun(
            cmd="cd /app && nohup /usr/local/bin/python server.py > /tmp/server.log 2>&1 &", session="server"
        )
        print(f"Start result: {result.output}")

        # Wait for server to start
        await asyncio.sleep(5)

        # Check server log
        result = await sandbox.arun(cmd="cat /tmp/server.log", session="server")
        print(f"Server log:\n{result.output}")

        # Test internally first
        print("=" * 60)
        print("Step 5: Testing server inside container...")
        print("=" * 60)
        result = await sandbox.arun(
            cmd="/usr/local/bin/python -c \"import urllib.request; print(urllib.request.urlopen('http://localhost:8080/health').read().decode())\"",
            session="server",
        )
        print(f"Internal /health result: {result.output}")

        # Now test proxy with /health endpoint
        print("=" * 60)
        print("Step 6: Testing via ROCK Proxy...")
        print("=" * 60)
        proxy_url = f"{BASE_URL}/apis/envs/sandbox/v1/sandboxes/{sandbox_id}/proxy/health"
        print(f"Proxy URL: {proxy_url}")

        headers = {
            "XRL-Authorization": f"Bearer {AUTH_TOKEN}",
            "X-Cluster": "vpc-nt-b",
        }

        async with httpx.AsyncClient() as client:
            # Test GET /health
            print("\n--- Testing GET /health ---")
            try:
                resp = await client.get(proxy_url, headers=headers, timeout=30)
                print(f"Status: {resp.status_code}")
                print(f"Response: {resp.text}")
            except Exception as e:
                print(f"GET Error: {e}")

            # Test POST /health
            print("\n--- Testing POST /health ---")
            try:
                resp = await client.post(proxy_url, headers=headers, json={}, timeout=30)
                print(f"Status: {resp.status_code}")
                print(f"Response: {resp.text}")
            except Exception as e:
                print(f"POST Error: {e}")

        print("=" * 60)
        print(f"Sandbox ID: {sandbox_id}")
        print(f"Proxy URL: {proxy_url}")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print(f"\nKeeping sandbox alive. Sandbox ID: {sandbox.sandbox_id}")


if __name__ == "__main__":
    asyncio.run(main())
