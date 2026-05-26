"""Local mock paste server for safe Day-1 testing (no Bright Data, no credits).

Routes:
  GET /paste/001  -> pastes/mock-paste-001.html  (verified-leak decoy)
  GET /paste/002  -> pastes/mock-paste-002.html  (tutorial false-positive decoy)
  anything else   -> 404

Run:  python mock_server/server.py   ->   http://localhost:8080/paste/001
"""

from __future__ import annotations

import http.server
import socketserver
from pathlib import Path

PORT = 8080
PASTES_DIR = Path(__file__).resolve().parent / "pastes"
ROUTES = {
    "/paste/001": "mock-paste-001.html",
    "/paste/002": "mock-paste-002.html",
}


class PasteHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        filename = ROUTES.get(self.path)
        if filename is None:
            self.send_error(404, "paste not found")
            return
        body = (PASTES_DIR / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:  # silence default request logging
        pass


class _ReusableServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True  # avoid "address already in use" on quick restarts


def make_server(port: int = PORT) -> _ReusableServer:
    """Create (but don't start) a server instance — used by the test fixture too."""
    return _ReusableServer(("", port), PasteHandler)


def serve(port: int = PORT) -> None:
    with make_server(port) as httpd:
        print(f"Mock paste server on http://localhost:{port}  (routes: {', '.join(ROUTES)})")
        httpd.serve_forever()


if __name__ == "__main__":
    serve()
