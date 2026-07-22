# Idle Hacking — research, strategy and tooling workspace

Long-running analysis workspace for the browser game **Idle Hacking** (player: the player). Migrated from a ChatGPT Project on 2026-07-22; the raw handover is preserved in the initial git commit. Three kinds of work happen here: loadout/crafting strategy analysis, game-mechanics research, and development of the passive capture userscript.

## Source-of-truth order

1. A newly supplied schema-4 export or combat log.
2. `data/loadouts/current-loadout-and-candidates-2026-07-21-schema4.json` — latest complete baseline (8/8 equipped, 34 candidates, 32 crafting snapshots).
3. `docs/current-state.md` and `docs/decision-log.md`.
4. `docs/mechanics.md` and `docs/crafting.md`.
5. Older schema-3 snapshots and historical logs.

## File map

- `docs/mechanics.md` — combat-stat working model, equipment structure, evaluation method.
- `docs/crafting.md` — Stability/Compile economy, operation reference, decision protocol, candidate output contract.
- `docs/current-state.md` — latest reviewed loadout baseline and bottleneck model.
- `docs/candidate-status.md` — per-item project status and safe-decompile list.
- `docs/equipment-tests.md` — measured A/B trial evidence.
- `docs/decision-log.md` — append-only record of decisions.
- `docs/open-questions.md` — unknowns and planned tests; prevents working models becoming "facts".
- `docs/data-dictionary.md` — combat-log field meanings and analysis conventions.
- `docs/capture-tool.md` — userscript reference and safety boundary.
- `docs/game-client-internals.md` — how the game client stores state (bindings, item schema, WS protocol); basis for full-state capture. Game JS reference copies: `vendor/game-js/` (git-ignored).
- `data/` — structured exports and combat logs (see `data/README.md`); `data/incoming/` is the untriaged staging area fed by the capture hub.
- `tools/item-loadout-capture.user.js` — the passive Tampermonkey capture script (schema 4; version in the `@version` header).
- `scripts/capture-hub.py` — localhost:8123 hub (systemd user service `idle-hacking-capture-hub`): serves the userscript to Tampermonkey and receives in-game exports into `data/incoming/`.

## Working with the data

- When the user says they sent/exported new data, look in `data/incoming/` first; triage files into `data/loadouts|combat|crafting/` with dated names before analysis.
- The schema-4 loadout export is ~1.3 MB. **Never read it whole** — query it with `python3` or `jq` and extract only the items/snapshots needed.
- Combat logs in `data/combat/kernel-test/` include one `DUPLICATE-` file; it is the same fight as its sibling and must be counted once. Field semantics: `docs/data-dictionary.md`.
- New data files are dated, never overwritten. A one-slot export gives exact slot deltas but not whole-loadout state.

## Analysis rules

- Treat the newest structured export as the source of truth; ask for a fresh complete export when a decision depends on the current whole loadout.
- Separate verified facts, working models and unknowns. Never invent formulas or mechanics.
- Evaluate candidates as crafting bases and as parts of the whole loadout — never on Item Level alone. Follow the output contract in `docs/crafting.md` §10 (forced Augment side, Continue/Conditional/Abort outcomes, ordered tier targets, attempt caps, Stability floor, Compile timing, post-craft test).
- Long-streak loss analysis must separate accumulated attrition from final-matchup strength. Diagnose in order: attrition vs matchup → hit reliability → outgoing damage → incoming damage/burst → which one or two stats would change the result → cheapest slot to obtain them.
- Inspect start/max/end HP, streak, rounds, hits, miss events, crits, direct damage, `prg`, barrier, thorns/corruption and enemy stats.

## Empirical guardrails (current build)

- The build needs Defense, regeneration and fight tempo together; Max HP is a buffer, not a substitute for mitigation or recovery.
- A tested Kernel trade of +11 Regeneration and +5.53% Max HP for −7.46% Defense, −1.57% Accuracy and −2.09% Attack Speed was unfavourable.
- Do not assume listed Regeneration equals realised combat-log `prg`.
- Firewall/Router/Kernel replacements must preserve the function of the current sustain anchors, not merely improve item level.

## Userscript safety (non-negotiable)

The capture tool must remain passive/read-only: passive DOM observation, user-click origin classification, localStorage, copy/download, and user-click-initiated POSTs of captured data to the local capture hub only. Never automate equip, enhance, decompile, purchase, combat selection, repeated clicks, or any API/WebSocket/server request against the game or a remote host. Preserve equipped-vs-inventory-candidate classification. Bump the script's `@version` on every change (Tampermonkey won't update otherwise).

## Maintenance conventions

- Append to `docs/decision-log.md` whenever equipment changes, a scarce resource is spent or a mechanic is confirmed.
- When a mechanic is confirmed, move it from `docs/open-questions.md` into `docs/mechanics.md` or `docs/crafting.md`.
- `docs/current-state.md` always represents the latest reviewed baseline; avoid accumulating contradictory "current state" prose.
- Lead with the key decision; be explicit about uncertainty and confidence level (directional vs formula-level).
