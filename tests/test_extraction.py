"""Day-1 extraction tests against the local mock server (no Bright Data)."""

import threading
import time

import pytest

from mock_server.server import make_server
from nodes.extraction import extraction_node

PORT = 8080
BASE = f"http://localhost:{PORT}"


@pytest.fixture(scope="module")
def server():
    httpd = make_server(PORT)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)  # let the listener bind
    try:
        yield BASE
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_extraction_success(server):
    state = {"url": f"{server}/paste/001"}
    extraction_node(state)
    assert state["raw_content"]                    # non-empty
    assert "acme.com" in state["raw_content"]
    assert state.get("error") is None


def test_extraction_404(server):
    state = {"url": f"{server}/paste/404"}
    extraction_node(state)
    assert state.get("error") is not None
    assert state["raw_content"] is None
