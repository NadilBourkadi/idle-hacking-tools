# Idle Hacking Capture Tool — Technical Reference

**Current source:** `tools/item-loadout-capture.user.js` (v0.6.1)
**Export schema:** 4

The v0.6.1 source was recovered from the installed Tampermonkey script on 22 July 2026, after the original ChatGPT handover was built (that dump could only archive v0.5 and flagged v0.6.1 as missing). Version history is tracked by git from here on; bump `@version` in the script header on any change.

## Purpose and safety boundary

The userscript passively captures opened item tooltips, the equipped loadout and crafting-panel snapshots. It must remain read-only with respect to gameplay.

Allowed:

- observe DOM changes;
- classify the user's own clicks;
- parse visible text;
- use localStorage;
- copy/download exports.

Forbidden:

- automatic game clicks;
- equipping, enhancing, compiling, pruning or decompiling;
- purchasing or combat selection;
- direct API/WebSocket/server actions.

## Validated click origins

- Equipped: `#equipped-software-panel .equipment-slot`
- Inventory: `#inventory-grid [data-item-id]`
- The v0.5 `Alt+E` fallback hotkey no longer exists in v0.6.1.

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
