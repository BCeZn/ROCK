import requests

from tests.integration.conftest import RemoteServer


def test_is_alive(rocklet_remote_server: RemoteServer):
    response = requests.get(f"{rocklet_remote_server.endpoint}:{rocklet_remote_server.port}/is_alive")
    assert response.json()["is_alive"]


def test_hello_world(rocklet_remote_server: RemoteServer):
    assert (
        requests.get(f"{rocklet_remote_server.endpoint}:{rocklet_remote_server.port}/").json()["message"]
        == "hello world"
    )
