#!/usr/bin/env python3
"""Local capture hub for the Idle Hacking workspace.

Serves two roles on 127.0.0.1:8123 (reachable from the Windows browser
via WSL2 localhost forwarding):

  GET /item-loadout-capture.user.js
      Serves the userscript from tools/. Tampermonkey installs and
      updates the script from this URL (@updateURL/@downloadURL).

  POST /export
      Receives a JSON export from the userscript and routes it by its
      top-level "schema" field: full-state captures go straight to
      data/captures/ (no triage needed — they are always complete
      snapshots); anything else goes to data/incoming/ for triage.
      The optional X-Export-Name header suggests a filename; it is
      sanitised and never allowed to escape the target directory or
      overwrite an existing file.

Stdlib only. Run directly or via the systemd user unit in scripts/.
"""

import json
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8123
MAX_BODY_BYTES = 32 * 1024 * 1024

ROOT = Path(__file__).resolve().parent.parent
USERSCRIPT = ROOT / "tools" / "item-loadout-capture.user.js"
INCOMING = ROOT / "data" / "incoming"
CAPTURES = ROOT / "data" / "captures"

SCHEMA_ROUTES = {
    "idle-hacking-state-capture-v1": CAPTURES,
}


def sanitise_name(raw):
    name = re.sub(r"[^A-Za-z0-9._-]", "-", Path(raw or "").name).lstrip(".")[:120]
    if not name.endswith(".json"):
        name += ".json"
    if name == ".json":
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        name = f"idle-hacking-capture-{stamp}.json"
    return name


def unique_path(directory, name):
    path = directory / name
    stem, counter = path.stem, 1
    while path.exists():
        path = directory / f"{stem}-{counter}.json"
        counter += 1
    return path


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="text/plain; charset=utf-8"):
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path.split("?")[0] == "/item-loadout-capture.user.js":
            try:
                source = USERSCRIPT.read_text(encoding="utf-8")
            except OSError as error:
                self._send(500, f"Cannot read userscript: {error}\n")
                return
            self._send(200, source, "text/javascript; charset=utf-8")
            return

        if self.path.split("?")[0] in ("/", "/health"):
            self._send(200, "idle-hacking capture hub OK\n")
            return

        self._send(404, "Not found\n")

    def do_POST(self):
        if self.path.split("?")[0] != "/export":
            self._send(404, "Not found\n")
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send(413, "Body missing or too large\n")
            return

        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except ValueError:
            self._send(400, "Body is not valid JSON\n")
            return

        schema = payload.get("schema") if isinstance(payload, dict) else None
        directory = SCHEMA_ROUTES.get(schema, INCOMING)
        directory.mkdir(parents=True, exist_ok=True)
        path = unique_path(
            directory, sanitise_name(self.headers.get("X-Export-Name"))
        )
        path.write_bytes(body)
        self._send(200, f"Saved {path.relative_to(ROOT)}\n")

    def log_message(self, format, *args):
        sys.stdout.write(
            "[%s] %s\n" % (self.log_date_time_string(), format % args)
        )
        sys.stdout.flush()


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Capture hub listening on http://{HOST}:{PORT} (root: {ROOT})")
    server.serve_forever()


if __name__ == "__main__":
    main()
