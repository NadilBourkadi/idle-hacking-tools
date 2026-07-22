# Idle Hacking Capture Tool — Technical Handover

**Latest observed runtime:** 0.6.1  
**Latest archived source available:** 0.5.0  
**Latest observed export schema:** 4

## Purpose and safety boundary

The userscript passively captures opened item tooltips, the equipped loadout and—in the 0.6.1 runtime—crafting-panel snapshots. It must remain read-only with respect to gameplay.

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
- `Alt+E` is fallback-only in the archived v0.5 source.

## Observed schema-4 additions

The 0.6.1 export contains:

- top-level `sourceVersion`;
- item `domItemId` where available;
- `crafting.capturedSnapshotCount`;
- `crafting.snapshots` with affix ranges, current roll positions, operation controls, costs and affordability;
- `itemRevisions` for tracking item changes across crafting actions.

The complete fixture in `data/loadouts/current-loadout-and-candidates-2026-07-21-schema4.json` is the authoritative schema example.

## Source provenance warning

The actual v0.6.1 `.user.js` source was not available in the Project filesystem or connected Drive when this archive was built. Do not rename the v0.5 source and present it as v0.6.1. The archive therefore includes:

- `tools/archive/idle-hacking-item-loadout-capture-v0.5.user.js` — last source actually available;
- `tools/LATEST_TOOL_STATUS.md` — missing-source record and recovery instructions;
- the schema-4 fixture — evidence of the newer runtime's output.

## Recovery of the real latest source

Open Tampermonkey, edit the installed Idle Hacking script, copy the complete source, and save it as:

`tools/idle-hacking-item-loadout-capture-v0.6.1.user.js`

Then update this handover and checksums. No game action is required.
