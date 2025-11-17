import requests

from tests.integration.conftest import RemoteServer

headers = {"X-API-Key": "your_secret_api_key_here"}


def test_is_alive(remote_server: RemoteServer):
    response = requests.get(f"http://127.0.0.1:{remote_server.port}/is_alive", headers=remote_server.headers)
    assert response.json()["is_alive"]


def test_hello_world(remote_server: RemoteServer):
    assert (
        requests.get(f"http://127.0.0.1:{remote_server.port}/", headers=remote_server.headers).json()["message"]
        == "hello world"
    )
