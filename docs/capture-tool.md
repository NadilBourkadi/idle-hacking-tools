# Idle Hacking Capture Tool — Technical Reference

**Current source:** `tools/item-loadout-capture.user.js` (v1.5.0)
**Export schema:** `idle-hacking-state-capture-v1`

Version history is tracked by git. Bump `@version` in the script header on **every** change — Tampermonkey refuses to update to a same-version script.

## What it does (v1.0.0)

One-click, read-only capture of the full game state. The panel has two buttons:

- **Capture all (full state)** — reads the game's top-level state bindings (`currentPlayer`, `equipmentData`, `inventoryData`, `statsBreakdown`, `extendedStats`, `recentLossStreaks`, `combatLog`, `lastCombatStatusPayload`, `hackingState`, `hackingZones`, `multiplierData`, `homelabInfo`, `hardwareInfo`) via a page-scope snippet and POSTs the JSON to the local capture hub, which auto-routes it to `data/captures/`.
- **Download instead** — same payload as a browser download, for when the hub is offline.

Because lexical bindings are invisible to the Tampermonkey sandbox, the reader snippet is evaluated in page scope with three CSP-fallback strategies: page `Function` constructor → inline `<script>` → `GM_addElement`. The payload records which strategy ran (`readMethod`). The snippet only reads the named bindings — it calls no game functions.

Lazy bindings: `statsBreakdown`/`extendedStats`/`recentLossStreaks` are null/empty until the stats panel or loss-history screen has been opened that session; `hardwareInfo` is null until the Hardware Shop tab has been opened (its absence is noted in the capture summary but does not mark a capture THIN). Item data is always present. Internal slot names (`main_hand`…) map to display slots per `game-client-internals.md`.

## Purpose and safety boundary

The tool must remain read-only with respect to gameplay.

Allowed:

- reading game state bindings from page scope (values only, never calling game functions);
- copy/download of captures;
- POSTing captures to the user's own localhost capture hub (user-click-initiated);
- the opt-in **auto-stream** (since v1.5.0, boundary amended 23 Jul 2026 at the player's request): a timer POSTing a lightweight combat-only payload (`combatLog`, `recentLossStreaks`, `hackingState`, plus a small `playerLite` scalar slice) to the localhost hub every 150 s while the panel toggle is ON. Still zero game interaction; localhost only.

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

**Stream flow:** auto-stream payloads (`idle-hacking-combat-stream-v1`) are **not stored raw** — the hub extracts fights (deduped by `ihlib.fight_key`; fight ids are per-session), deaths (by `ended_at_ms`) and combat-stat changes (segmentation boundaries, e.g. a homelab upgrade landing), appending only new records to `data/combat-stream/YYYY-MM-DD.jsonl`. `ihlib.experiment_status` reads captures + ledger together, so `ih.py ab` sees everything. Full captures remain the source for crafting/loadout state — the stream only exists because the combat windows are lossy (50 fights ≈ 5 min at observed tempo, 10 deaths ≈ 90 min).

## Version history

- v0.5 — legacy DOM click-scraper; last source archived in the original ChatGPT handover.
- v0.6.1 — recovered from Tampermonkey 22 July 2026 after the handover flagged it missing; crafting snapshots, schema 4.
- v0.7.0 — capture-hub integration ("Send to workspace"); `@grant none` → `GM_xmlhttpRequest` (sandboxed).
- v0.8.0–v0.8.1 — read-only data-source probe (storage/IndexedDB/globals/frameworks recon; structure only, values never captured).
- v0.9.0–v0.9.1 — "Capture all (full state)" from game bindings; probe findings in `game-client-internals.md`.
- v1.0.0 — legacy click-scraping UI and DOM machinery removed (~3,000 → ~390 lines). Full-state capture + download fallback only. Schema-4 exports remain readable in `data/loadouts/` history; the legacy tool lives in git history if ever needed.
- v1.1.0–v1.2.0 — capture set expanded with combat and homelab bindings: `combatLog` (rolling fight list incl. wins and drops), `lastCombatStatusPayload`, `hackingState`, `hackingZones` (zone catalog), `multiplierData`, `homelabInfo` (upgrade levels — Snapshot Backup). Hub now auto-routes state captures to `data/captures/`.
- v1.3.0 — added `hardwareInfo` (Hardware Shop catalog; lazy, open the Hardware Shop tab once per session) and an `hw` entry in the readiness indicator.
- v1.4.0 — feedback-loop release: readiness shows `rounds N/M` (fights with round detail — detail only records while the combat-log modal is open) with an explicit ⚠ hint when zero, and `losses N (Xm ago)` freshness; the hub now runs `ih.py ab --brief` on every state capture and returns the A/B verdict in the POST response, which the panel displays. Capture cadence guidance: once per climb banks the death tail; deaths persist ~10 entries (~80–100 min), fights only ~50 (<1 climb).
- v1.4.1 — round-detail readiness distinguishes LIVE (newest fight has detail) from STALE (detail exists but recording stopped), with an explicit warning; the green state requires LIVE. Total count alone could show comfortable numbers hours after recording stopped.
- v1.4.2 — round-detail guidance corrected: the real switch is the **"Detailed Logs" checkbox in the Hacking panel** (records regardless of visible screen), not the combat-log modal; warnings now say so. Companion fix in `ihlib.experiment_status`: fight ids are per-session (counter resets on reload), so cross-capture aggregation dedupes by content key and classifies pre/post per capture instead of by global id.
- v1.5.0 — opt-in auto-stream (panel toggle, persisted): combat-only payload every 150 s → hub dedupes into the `data/combat-stream/` ledger. Includes `playerLite` (combat stats + currency scalars) so the hub logs stat-change segmentation records. Full state deliberately NOT streamed: it is lossless in any single click-capture and ~1 MB/push (~500 MB/day) of near-duplicates.

## Leftovers from the legacy tool

The old versions cached scraped data in localStorage keys `idle-hacking-item-capture:v2`–`:v4` and `idle-hacking-captured-items-v1` (~150 KB total). v1.0.0 neither reads nor writes them; they can be deleted manually via DevTools if desired.
