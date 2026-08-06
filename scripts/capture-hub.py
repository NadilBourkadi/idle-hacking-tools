#!/usr/bin/env python3
"""Local capture hub for the Idle Hacking workspace.

Serves two roles on 127.0.0.1:8123 (reachable from the Windows browser
via WSL2 localhost forwarding):

  GET /item-loadout-capture.user.js
      Serves the userscript from tools/. Tampermonkey installs the
      script from this URL; the published script no longer carries
      @updateURL/@downloadURL (see the userscript header), so updates
      are a manual re-install from here.

  POST /export
      Receives a JSON export from the userscript and routes it by its
      top-level "schema" field: full-state captures go straight to
      data/captures/ (no triage needed — they are always complete
      snapshots); anything else goes to data/incoming/ for triage.
      The optional X-Export-Name header suggests a filename; it is
      sanitised and never allowed to escape the target directory or
      overwrite an existing file. POSTs must be application/json, and
      when IH_HUB_SECRET is set in the hub's environment they must also
      carry a matching X-Hub-Secret header.

Stdlib only. Run directly or via the systemd user unit in scripts/.
"""

import hmac
import json
import os
import re
import sys
import threading
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ihlib  # noqa: E402  (fight_key + STREAM_DIR shared with the ledger)

HOST = "127.0.0.1"
PORT = 8123
MAX_BODY_BYTES = 32 * 1024 * 1024

# Optional shared secret, read once at startup. When IH_HUB_SECRET is set,
# every POST must carry a matching X-Hub-Secret header or is refused with
# 403. The other half is the HUB_SECRET constant in the userscript — set
# both or neither.
HUB_SECRET = os.environ.get("IH_HUB_SECRET", "")

ROOT = Path(__file__).resolve().parent.parent
USERSCRIPT = ROOT / "tools" / "item-loadout-capture.user.js"
INCOMING = ROOT / "data" / "incoming"
CAPTURES = ROOT / "data" / "captures"

SCHEMA_ROUTES = {
    "idle-hacking-state-capture-v1": CAPTURES,
}

# The capture response used to run `ih.py ab --brief` synchronously and
# return its summary for the userscript panel. REMOVED 31 Jul 2026: the
# subprocess's runtime grows with the stream ledger (3.4s morning -> 6.3s
# evening against 194MB), it crossed the userscript's 8s POST timeout — every
# capture was saved but every response died with BrokenPipeError, and the
# panel showed "hub unreachable" — and the player confirmed the in-panel
# summary was unused. The hub is now pure save-and-ledger: no subprocesses,
# response time independent of ledger size. A/B status lives in
# `ih.py ab` / `ih.py brief`.


# ---- Combat stream ledger --------------------------------------------------
# Auto-stream payloads (schema below) are NOT stored raw: fights and deaths
# are extracted, deduped (fights by ihlib.fight_key — ids are per-session —
# and deaths by ended_at_ms), and appended to a daily JSONL ledger that
# ihlib.experiment_status reads alongside full captures.

STREAM_SCHEMA = "idle-hacking-combat-stream-v1"
_stream_lock = threading.Lock()
_seen_fights = set()
_seen_deaths = set()
_last_stats = None
_seen_loaded_for = None


def _ledger_path(now):
    return ihlib.STREAM_DIR / f"{now:%Y-%m-%d}.jsonl"


def _load_seen(now):
    # Day-scoped seeding is DELIBERATE here, unlike the sim ledger below
    # (archive-scoped since the 1-3 Aug 2026 duplicate-ingestion fix in
    # _load_seen_sims): the client only ever re-sends its bounded ~50-fight
    # combat-log window, so a fight cannot resurface days later the way the
    # profiler's last-10 results do, and downstream analysis re-dedupes by
    # fight_key archive-wide anyway. Worst case at a day boundary is a
    # duplicate ledger line the analysis side already discards.
    global _seen_loaded_for, _last_stats
    day = f"{now:%Y-%m-%d}"
    if _seen_loaded_for == day:
        return
    _seen_fights.clear()
    _seen_deaths.clear()
    _last_stats = None
    path = _ledger_path(now)
    if path.exists():
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                # A truncated tail line (crash mid-append) must not poison
                # every subsequent stream POST — skip it and note where.
                print(f"WARNING: skipping unparseable ledger line "
                      f"{path.name}:{number}", file=sys.stderr)
                continue
            if record.get("kind") == "fight":
                _seen_fights.add(tuple(record.get("key") or ()))
            elif record.get("kind") == "death":
                _seen_deaths.add((record.get("death") or {}).get("ended_at_ms"))
            elif record.get("kind") == "stats":
                _last_stats = (record.get("player") or {}).get("combat_stats")
    _seen_loaded_for = day


def absorb_stream(payload):
    """Append new fights/deaths from a stream payload; return summary text."""
    state = payload.get("state") or {}
    now = datetime.now(timezone.utc)
    seen_ms = int(now.timestamp() * 1000)
    with _stream_lock:
        _load_seen(now)
        new_records = []
        detailed = 0
        for f in state.get("combatLog") or []:
            key = ihlib.fight_key(f)
            if key in _seen_fights:
                continue
            _seen_fights.add(key)
            if f.get("combat_log"):
                detailed += 1
            new_records.append({"kind": "fight", "seen_ms": seen_ms,
                                "key": list(key), "fight": f})
        for entry in state.get("recentLossStreaks") or []:
            ms = entry.get("ended_at_ms")
            if not ms or ms in _seen_deaths:
                continue
            _seen_deaths.add(ms)
            new_records.append({"kind": "death", "seen_ms": seen_ms,
                                "death": entry})
        # Combat-stat change records timestamp gear/homelab/hardware effects
        # landing — automatic segmentation boundaries for A/B analysis.
        global _last_stats
        player = state.get("playerLite") or {}
        stats = player.get("combat_stats")
        if stats and stats != _last_stats:
            new_records.append({"kind": "stats", "seen_ms": seen_ms,
                                "player": player,
                                "changed_from": _last_stats})
            _last_stats = stats
        if new_records:
            ihlib.STREAM_DIR.mkdir(parents=True, exist_ok=True)
            with _ledger_path(now).open("a") as ledger:
                for record in new_records:
                    ledger.write(json.dumps(record) + "\n")
    fights = sum(1 for r in new_records if r["kind"] == "fight")
    deaths = sum(1 for r in new_records if r["kind"] == "death")
    return (f"stream: +{fights} fights ({detailed} detailed), "
            f"+{deaths} deaths banked")


# ---- Hacking Simulator ledger ----------------------------------------------
# Simulator payloads are appended to a daily JSONL ledger, deduped by a hash
# of the result body: the userscript re-sends the same live binding until the
# player runs again, and the IndexedDB backfill overlaps what live polling
# already banked. Hashing the result makes both harmless.

SIM_SCHEMA = "idle-hacking-sim-runs-v1"
_sim_lock = threading.Lock()
_seen_sims = set()
_seen_sims_loaded = False


def _sim_ledger_path(now):
    return ihlib.SIM_DIR / f"{now:%Y-%m-%d}.jsonl"


def _load_seen_sims():
    # Seed from EVERY ledger file, not just today's: the profiler panel
    # re-serves its last-10 results indefinitely, so a day-scoped seen-set
    # re-ingests them as "new" on the first capture of each day (this put 20
    # duplicate rows in the ledger over 1-3 Aug 2026). The hub is the only
    # writer, so after the one-time seed the in-memory set stays complete.
    global _seen_sims_loaded
    if _seen_sims_loaded:
        return
    for path in sorted(ihlib.SIM_DIR.glob("*.jsonl")):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                # Same tolerance as _load_seen: a truncated line must not
                # 500 every subsequent sim POST forever.
                print(f"WARNING: skipping unparseable ledger line "
                      f"{path.name}:{number}", file=sys.stderr)
                continue
            _seen_sims.add(record.get("key"))
    _seen_sims_loaded = True


def absorb_sims(payload):
    """Append new simulator runs; return summary text."""
    state = payload.get("state") or {}
    now = datetime.now(timezone.utc)
    seen_ms = int(now.timestamp() * 1000)
    with _sim_lock:
        _load_seen_sims()
        new_records = []
        for run in state.get("runs") or []:
            if not isinstance(run, dict) or not isinstance(run.get("result"), dict):
                continue
            key = ihlib.sim_key(run)
            if key in _seen_sims:
                continue
            _seen_sims.add(key)
            new_records.append({
                "kind": "sim",
                "seen_ms": seen_ms,
                "key": key,
                "mode": run.get("mode"),
                "source": run.get("source"),
                "recorded_at_ms": run.get("recorded_at_ms"),
                "form": state.get("form"),
                "context": state.get("context"),
                "result": run["result"],
            })
        if new_records:
            ihlib.SIM_DIR.mkdir(parents=True, exist_ok=True)
            with _sim_ledger_path(now).open("a") as ledger:
                for record in new_records:
                    ledger.write(json.dumps(record) + "\n")
    if not new_records:
        return "sim: no new runs"
    parts = []
    for record in new_records:
        result = record["result"]
        level = result.get("requested_enemy_level") or "?"
        rate = result.get("win_rate")
        rate_text = f"{rate * 100:.0f}%" if isinstance(rate, (int, float)) else "?"
        parts.append(f"lvl {level} {rate_text}")
    return f"sim: +{len(new_records)} run(s) banked ({', '.join(parts[:4])})"


def sanitise_name(raw):
    name = re.sub(r"[^A-Za-z0-9._-]", "-", Path(raw or "").name).lstrip(".")[:120]
    if not name.endswith(".json"):
        name += ".json"
    if name == ".json":
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        name = f"idle-hacking-capture-{stamp}.json"
    return name


def write_unique(directory, name, body):
    # "xb" (O_CREAT|O_EXCL) makes claim-and-write atomic: the old
    # exists()-then-write pair left a window in which a concurrent request
    # — or a planted symlink — could take the name between the check and
    # the write. O_EXCL also refuses to follow a symlink at the path.
    path = directory / name
    stem, counter = path.stem, 1
    while True:
        try:
            with open(path, "xb") as handle:
                handle.write(body)
        except FileExistsError:
            path = directory / f"{stem}-{counter}.json"
            counter += 1
        else:
            return path


class Handler(BaseHTTPRequestHandler):
    # Slowloris guard: a client that stops sending mid-request is dropped
    # after 30s instead of holding a handler thread open forever.
    timeout = 30
    # Terse Server header — no Python/BaseHTTP version advertising.
    server_version = "capture-hub"
    sys_version = ""

    def _send(self, code, body, content_type="text/plain; charset=utf-8"):
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _reject(self, code, body):
        # A rejection may leave an unread request body on the socket, so
        # never reuse the connection for a further request.
        self.close_connection = True
        self._send(code, body)

    def do_GET(self):
        if self.path.split("?")[0] == "/item-loadout-capture.user.js":
            try:
                source = USERSCRIPT.read_text(encoding="utf-8")
            except OSError as error:
                # Details (paths) go to the log, never to the client.
                print(f"ERROR: cannot read userscript: {error}",
                      file=sys.stderr)
                self._send(500, "Cannot read userscript\n")
                return
            self._send(200, source, "text/javascript; charset=utf-8")
            return

        if self.path.split("?")[0] in ("/", "/health"):
            self._send(200, "idle-hacking capture hub OK\n")
            return

        self._send(404, "Not found\n")

    def do_POST(self):
        if self.path.split("?")[0] != "/export":
            self._reject(404, "Not found\n")
            return

        if HUB_SECRET and not hmac.compare_digest(
            self.headers.get("X-Hub-Secret") or "", HUB_SECRET
        ):
            self._reject(403, "Bad or missing X-Hub-Secret\n")
            return

        # Require application/json (parameters like "; charset=utf-8" are
        # fine — self.headers is an email Message, so get_content_type()
        # parses the media type properly). This closes the drive-by vector:
        # a cross-origin text/plain POST is a CORS "simple request" that
        # reaches localhost from any web page, but application/json forces
        # a preflight, which fails because the hub sends no CORS headers —
        # so no browser page can deliver one. The real userscript is
        # unaffected: GM_xmlhttpRequest bypasses CORS and already sends
        # application/json on all three POST paths.
        if self.headers.get_content_type() != "application/json":
            self._reject(415, "Content-Type must be application/json\n")
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._reject(400, "Bad Content-Length\n")
            return
        if length <= 0:
            self._reject(400, "Body required\n")
            return
        if length > MAX_BODY_BYTES:
            self._reject(413, "Body too large\n")
            return

        try:
            body = self.rfile.read(length)
        except TimeoutError:
            # Sender stalled mid-body and hit the socket timeout.
            self._reject(408, "Request body timed out\n")
            return
        try:
            payload = json.loads(body)
        except ValueError:
            self._reject(400, "Body is not valid JSON\n")
            return

        schema = payload.get("schema") if isinstance(payload, dict) else None
        if schema == STREAM_SCHEMA:
            try:
                self._send(200, absorb_stream(payload) + "\n")
            except Exception:
                # Full traceback to the log; a generic line to the client.
                traceback.print_exc()
                self._send(500, "stream absorb failed\n")
            return
        if schema == SIM_SCHEMA:
            try:
                self._send(200, absorb_sims(payload) + "\n")
            except Exception:
                traceback.print_exc()
                self._send(500, "sim absorb failed\n")
            return
        directory = SCHEMA_ROUTES.get(schema, INCOMING)
        directory.mkdir(parents=True, exist_ok=True)
        path = write_unique(
            directory, sanitise_name(self.headers.get("X-Export-Name")), body
        )
        self._send(200, f"Saved {path.relative_to(ROOT)}\n")

    def log_message(self, format, *args):
        sys.stdout.write(
            f"[{self.log_date_time_string()}] {format % args}\n"
        )
        sys.stdout.flush()


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Capture hub listening on http://{HOST}:{PORT} (root: {ROOT})")
    server.serve_forever()


if __name__ == "__main__":
    main()
