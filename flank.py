"""
Project MUSUBI — flank.py
Lightweight HTTP server to keep the bot alive on Render free tier.
Run alongside the bot via threading.
"""

from __future__ import annotations

import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

log = logging.getLogger("musubi.keepalive")

HOST = "0.0.0.0"
PORT = 8080


class _Handler(BaseHTTPRequestHandler):

    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Musubi is alive.")

    def log_message(self, format: str, *args: object) -> None:
        pass  # Silence default HTTP request logs


def start() -> None:
    server = HTTPServer((HOST, PORT), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log.info("Keep-alive server running on port %d.", PORT)