# Idle Hacking Capture Tool — Technical Reference

**Current source:** `tools/item-loadout-capture.user.js` (v0.8.1)
**Export schema:** 4

Version history is tracked by git. Bump `@version` in the script header on **every** change — Tampermonkey refuses to update to a same-version script.

- v0.5 — last source archived in the original ChatGPT handover.
- v0.6.1 — recovered from Tampermonkey on 22 July 2026 after the handover flagged it missing; added crafting snapshots and schema 4.
- v0.7.0 — capture-hub integration: served to Tampermonkey from `http://localhost:8123`, "Send to workspace" button POSTs exports into `data/incoming/`. Switched `@grant none` → `GM_xmlhttpRequest` (script now runs in Tampermonkey's sandbox).
- v0.9.0 — "Capture all (full state)" button: reads the game's top-level state bindings (`currentPlayer`, `equipmentData`, `inventoryData`, `statsBreakdown`, `recentLossStreaks`) via a page-scope snippet (three CSP-fallback strategies: page `Function` constructor → inline script → `GM_addElement`) and sends everything to the hub as schema `idle-hacking-state-capture-v1`. Replaces per-item tooltip clicking and enhance-panel visits entirely; the snippet only reads bindings — it never calls game functions. See `game-client-internals.md`.
- v0.8.0–v0.8.1 — "Probe data sources" button: one-shot read-only inventory of where the game keeps client-side state (localStorage/sessionStorage key names+sizes+JSON shapes, IndexedDB layout+counts+sample field names, non-standard page globals via `unsafeWindow`, framework fingerprints). Structure only — stored values are never captured, so tokens cannot leak. Groundwork for bulk passive capture to replace per-item click-scraping; no synthetic clicks, nothing sent to any server.

## Local capture hub

`scripts/capture-hub.py` runs on `127.0.0.1:8123` inside WSL (reachable from the Windows browser via localhost forwarding) as the systemd user service `idle-hacking-capture-hub`:

```bash
systemctl --user status idle-hacking-capture-hub    # check
systemctl --user restart idle-hacking-capture-hub   # after editing the hub script
journalctl --user -u idle-hacking-capture-hub -n 20 # logs
```

Unit file: `scripts/idle-hacking-capture-hub.service` (installed copy in `~/.config/systemd/user/`).

**Install/update the userscript:** open `http://localhost:8123/item-loadout-capture.user.js` in the browser — Tampermonkey shows its install/update page. Subsequent updates also arrive via Tampermonkey's "Check for userscript updates" (the script's `@updateURL`/`@downloadURL` point at the hub).

**Export flow:** click **Send to workspace** in the in-game panel → the hub writes the JSON to `data/incoming/` (never overwriting; suggested filenames are sanitised). Triage per `data/incoming/README.md`. The Copy/Download buttons remain as fallbacks.

## Purpose and safety boundary

The userscript passively captures opened item tooltips, the equipped loadout and crafting-panel snapshots. It must remain read-only with respect to gameplay.

Allowed:

- observe DOM changes;
- classify the user's own clicks;
- parse visible text;
- use localStorage;
- copy/download exports;
- POST captured exports to the user's own localhost capture hub (user-click-initiated only).

Forbidden:

- automatic game clicks;
- equipping, enhancing, compiling, pruning or decompiling;
- purchasing or combat selection;
- direct API/WebSocket/server actions against the game or any remote host.

## Validated click origins

- Equipped: `#equipped-software-panel .equipment-slot`
- Inventory: `#inventory-grid [data-item-id]`
- The v0.5 `Alt+E` fallback hotkey no longer exists since v0.6.1.

## Schema-4 export contents

- top-level `sourceVersion`;
- item `domItemId` where available;
- `crafting.capturedSnapshotCount`;
- `crafting.snapshots` with affix ranges, current roll positions, operation controls, costs and affordability;
- `itemRevisions` for tracking item changes across crafting actions.

The complete fixture in `data/loadouts/current-loadout-and-candidates-2026-07-21-schema4.json` is the authoritative schema example.

## Storage

- Current localStorage key: `idle-hacking-item-capture:v4`
- Legacy key migrated from: `idle-hacking-item-capture:v3`
