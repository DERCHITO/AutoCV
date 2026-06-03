"""API HTTP mínima para que n8n llame a Python desde Docker (host.docker.internal)."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.core.bridge import (
    health_payload,
    json_response,
    list_applications,
    setup_database,
)
from app.core.config import get_bridge_host, get_bridge_port, get_bridge_token


class BridgeHandler(BaseHTTPRequestHandler):
    def _check_auth(self) -> bool:
        token = get_bridge_token()
        if not token:
            return True
        return self.headers.get("X-Bridge-Token") == token

    def _send(self, status: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _unauthorized(self) -> None:
        status, body = json_response({"ok": False, "error": "Unauthorized"}, 401)
        self._send(status, body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        if not self._check_auth():
            return self._unauthorized()

        path = urlparse(self.path).path
        if path == "/health":
            status, body = json_response(health_payload())
            return self._send(status, body)
        if path == "/applications":
            qs = parse_qs(urlparse(self.path).query)
            limit = int(qs.get("limit", ["50"])[0])
            status, body = json_response({"ok": True, "items": list_applications(limit)})
            return self._send(status, body)

        status, body = json_response({"ok": False, "error": "Not found"}, 404)
        self._send(status, body)

    def do_POST(self) -> None:  # noqa: N802
        if not self._check_auth():
            return self._unauthorized()

        path = urlparse(self.path).path
        if path == "/db/init":
            try:
                result = setup_database()
                status, body = json_response(result)
            except Exception as exc:  # noqa: BLE001
                status, body = json_response({"ok": False, "error": str(exc)}, 500)
            return self._send(status, body)

        status, body = json_response({"ok": False, "error": "Not found"}, 404)
        self._send(status, body)


def run_server() -> None:
    host = get_bridge_host()
    port = get_bridge_port()
    server = ThreadingHTTPServer((host, port), BridgeHandler)
    print(f"AutoCV bridge escuchando en http://{host}:{port}")
    print("  GET  /health")
    print("  GET  /applications")
    print("  POST /db/init")
    print("Desde n8n (Docker): http://host.docker.internal:{port}/health")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
