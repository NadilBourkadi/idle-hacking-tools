# Idle Hacking Capture Tool — Technical Reference

**Current source:** `tools/item-loadout-capture.user.js` (v1.2.0)
**Export schema:** `idle-hacking-state-capture-v1`

Version history is tracked by git. Bump `@version` in the script header on **every** change — Tampermonkey refuses to update to a same-version script.

## What it does (v1.0.0)

One-click, read-only capture of the full game state. The panel has two buttons:

- **Capture all (full state)** — reads the game's top-level state bindings (`currentPlayer`, `equipmentData`, `inventoryData`, `statsBreakdown`, `extendedStats`, `recentLossStreaks`, `combatLog`, `lastCombatStatusPayload`, `hackingState`, `hackingZones`, `multiplierData`, `homelabInfo`) via a page-scope snippet and POSTs the JSON to the local capture hub, which auto-routes it to `data/captures/`.
- **Download instead** — same payload as a browser download, for when the hub is offline.

Because lexical bindings are invisible to the Tampermonkey sandbox, the reader snippet is evaluated in page scope with three CSP-fallback strategies: page `Function` constructor → inline `<script>` → `GM_addElement`. The payload records which strategy ran (`readMethod`). The snippet only reads the named bindings — it calls no game functions.

Lazy bindings: `statsBreakdown`/`extendedStats`/`recentLossStreaks` are null/empty until the stats panel or loss-history screen has been opened that session. Item data is always present. Internal slot names (`main_hand`…) map to display slots per `game-client-internals.md`.

## Purpose and safety boundary

The tool must remain read-only with respect to gameplay.

Allowed:

- reading game state bindings from page scope (values only, never calling game functions);
- copy/download of captures;
- POSTing captures to the user's own localhost capture hub (user-click-initiated only).

Forbidden:

- synthetic clicks or any simulated input;
- equipping, enhancing, compiling, pruning, decompiling, purchasing, combat selection;
- calling game functions (including read-only-looking getters);
- API/WebSocket/server requests against the game or any remote host.

## Local capture hub

`scripts/capture-hub.py` runs on `127.0.0.1:8123` inside WSL (reachable from the Windows browser via localhost forwarding) as the systemd user service `idle-hacking-capture-hub`:

```bash
systemctl --user status idle-hacking-capture-hub    # check
systemctl --user restart idle-hacking-capture-hub   # after editing the hub script
journalctl --user -u idle-hacking-capture-hub -n 20 # logs
```

Unit file: `scripts/idle-hacking-capture-hub.service` (installed copy in `~/.config/systemd/user/`).

**Install/update the userscript:** open `http://localhost:8123/item-loadout-capture.user.js` in the browser — Tampermonkey shows its install/update page. Subsequent updates arrive via Tampermonkey's "Check for userscript updates" (the script's `@updateURL`/`@downloadURL` point at the hub).

**Export flow:** Capture all → hub routes by schema: state captures → `data/captures/` (immediately queryable via `scripts/ih.py`), everything else → `data/incoming/` for triage. Never overwrites; filenames sanitised.

## Version history

- v0.5 — legacy DOM click-scraper; last source archived in the original ChatGPT handover.
- v0.6.1 — recovered from Tampermonkey 22 July 2026 after the handover flagged it missing; crafting snapshots, schema 4.
- v0.7.0 — capture-hub integration ("Send to workspace"); `@grant none` → `GM_xmlhttpRequest` (sandboxed).
- v0.8.0–v0.8.1 — read-only data-source probe (storage/IndexedDB/globals/frameworks recon; structure only, values never captured).
- v0.9.0–v0.9.1 — "Capture all (full state)" from game bindings; probe findings in `game-client-internals.md`.
- v1.0.0 — legacy click-scraping UI and DOM machinery removed (~3,000 → ~390 lines). Full-state capture + download fallback only. Schema-4 exports remain readable in `data/loadouts/` history; the legacy tool lives in git history if ever needed.
- v1.1.0–v1.2.0 — capture set expanded with combat and homelab bindings: `combatLog` (rolling fight list incl. wins and drops), `lastCombatStatusPayload`, `hackingState`, `hackingZones` (zone catalog), `multiplierData`, `homelabInfo` (upgrade levels — Snapshot Backup). Hub now auto-routes state captures to `data/captures/`.

## Leftovers from the legacy tool

The old versions cached scraped data in localStorage keys `idle-hacking-item-capture:v2`–`:v4` and `idle-hacking-captured-items-v1` (~150 KB total). v1.0.0 neither reads nor writes them; they can be deleted manually via DevTools if desired.
