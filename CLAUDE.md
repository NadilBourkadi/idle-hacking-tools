# Idle Hacking — research, strategy and tooling workspace

Long-running analysis workspace for the browser game **Idle Hacking** (player: the player). Migrated from a ChatGPT Project on 2026-07-22; the raw handover is preserved in the initial git commit. Three kinds of work happen here: loadout/crafting strategy analysis, game-mechanics research, and development of the passive capture userscript.

## Source-of-truth order

1. The latest capture in `data/captures/` (query via `scripts/ih.py`).
2. `docs/current-state.md` (interpretation) and `docs/decision-log.md`.
3. `docs/mechanics.md`, `docs/crafting.md`, `docs/static-analysis-2026-07-22.md`.
4. Older schema-4/3 exports (`data/loadouts/`) and historical combat logs (`data/combat/`).

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
- `data/captures/` — full-state captures (authoritative, auto-routed by the hub); `data/combat-stream/` — daily JSONL ledger of deduped fights/deaths/stat-changes from the userscript auto-stream (hub-extracted, raw stream not stored); `data/incoming/` — non-capture staging; legacy exports in `data/loadouts/` and `data/combat/` (see `data/README.md`).
- `scripts/ih.py` + `scripts/ihlib.py` — capture query CLI and analysis library (slot map, scaling law, cost model as code).
- `tools/item-loadout-capture.user.js` — the read-only Tampermonkey capture script (version in the `@version` header; bump on every change).
- `scripts/capture-hub.py` — localhost:8123 hub (systemd user service `idle-hacking-capture-hub`): serves the userscript to Tampermonkey and routes incoming exports by schema.

## Working with the data — query-first

**Use `python3 scripts/ih.py <cmd>` for all capture queries; never parse capture JSON ad hoc.** Full-state captures land in `data/captures/` automatically (hub routes by schema); latest = lexicographically last. Commands: `audit`, `captures`, `loadout`, `item <query>`, `candidates [--slot s]`, `compare <a> <b>`, `diff [old new]`, `stats`, `history <query>`, `potential [--slot s] [--cap N]`, `homelab`, `hardware`, `ab`. For bespoke analysis, import `scripts/ihlib.py` — it encodes the slot mapping, scaling law, cost model, stat-composition families, hardware cost curve/planner and empirical tier ladders so they are never re-derived.

**Run `ih.py audit` first, every time, before any optimization.** It sweeps for things silently costing progress — idle build slots and empty queue places, hardware tracks whose multiplicand is zero, unspent or shop-locked chips/hackcoin, finished crafts still unequipped, and stale lazy panels. Every check exists because a real instance was missed by going straight to modelling. The biggest wins of 27 Jul 2026 all came from reading neglected fields, not from better models.

- `ih.py potential` plans as deep as the Stability budget allows (to T1, the game max). It used to stop at T3, which excluded the two best purchases on the ladder — gain per expected Stability point *rises* all the way down and peaks at T3→T2. Pass `--cap 3` only to reproduce pre-27-Jul-2026 numbers.
- Reusable primitives in `ihlib`, verified against live captures: `stat_total` (reproduces every stat exactly; use it for "what if I add X pool/flat" instead of hand arithmetic), `hardware_cost_curve` / `hardware_cumulative` / `hardware_plan` (chip cost law and equal-marginal-value allocation; the curve self-validates to ~1.5% against the game's own reset refund), `panel_freshness` / `stale_panels`.

**Candidate judgements use post-craft ceilings, never current rolls.** Equipped items are at 0 Stability (final); inventory items carry 25–30 Stability of Version-Upgrade headroom, so `compare`/`candidates` output systematically understates them. `ih.py potential` projects realistic ceilings (empirical tier ladders, budget-limited tier depth, Compile floor); its score is an *optimal-plan* heuristic that a §10.1 contract will land ~5 points below (`ihlib.CRAFT_WEIGHTS_*`), so confirm any craft with the `docs/crafting.md` §10 contract before spending.

- Captures are ~1 MB each. **Never read one whole** — `ih.py` or targeted `ihlib` scripts only.
- `statsBreakdown`/`extendedStats`/`combatLog`/`recentLossStreaks`/`homelabInfo` are lazy — captured only if the corresponding game panel was opened that session (`ih.py captures` shows what each capture contains).
- Anything in `data/incoming/` is non-capture output needing manual triage. Legacy schema-4/3 exports and combat logs live in `data/loadouts/` and `data/combat/` (one `DUPLICATE-` file there counts once; field semantics: `docs/data-dictionary.md`).
- Data files are immutable once written; new capture > editing an old one.

## Analysis rules

- **Every recommendation resolves to a specific action.** Never write a bare imperative with no object — "refill the homelab", "spend the chips", "buy some upgrades". Name the upgrade/item, target level, cost, duration and where it lives in the UI. `ih.py audit` and `ih.py homelab` print a FILL NOW block naming the exact jobs (`ihlib.homelab_fill_suggestions`); for unattended slots it ranks by **total progress points, not points per slot-hour**, because a slot idling after a short job loses more than the better rate gains.
- **Progression first; measurement second.** The point of this workspace is to make the player progress faster, not to run clean experiments. Recommend every worthwhile action in the same session; never stagger independently-good actions to keep their effects attributable, never gate progress behind collecting a baseline, and never freeze a queue to protect a test. Sequence two actions only when one changes the *correct choice* for the other. Confounded windows are acceptable — state that the period measures a bundle and move on. A/B discipline still governs how a test is *read* (see `docs/crafting.md` §14), never whether progress waits for one.
- **Audit before you model.** Anomalies in neglected fields beat optimization of well-trodden ones. Run `ih.py audit`, then read what it flags, then optimize. If you find an anomaly the audit missed, add the check — that is how the sweep stays useful.
- **Before an irreversible or once-a-month action, enumerate the state it touches and check every field it will write, not just the ones it reads.** A field that is empty now may be a post-condition field. `locked_resources` read as all-zero before the 27 Jul hardware reset, so it was treated as inert; the reset filled it, and the refunded hackcoin turned out to be permanently shop-bound — invalidating a claim already given to the player. When a field's meaning under the action is unclear, say so before recommending it.
- **Check accessibility before recommending any game system.** Homelab installs/upgrades, zones and crafting operations carry gates in the capture (`unlock_level` vs current homelab level, required install present/absent, zone `min_level`). Anything not currently reachable must be labelled with its gate ("unlocks at homelab 9"); gated upgrades may be entirely invisible in the game UI, so never assume the player has seen them. Always use display `name` fields from the capture's definitions, not internal slugs.
- **Credits are the effective crafting currency.** Basic resources (Cycles, Hashes, etc.) are purchasable on the marketplace at ~2 credits/unit (observed 22 Jul 2026: 5M cycles = 10.2M credits). Convert resource costs to credits when judging affordability; low on-hand gathering resources are never a schedule gate while credits are plentiful.

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

The capture tool must remain passive/read-only: it reads game state bindings from page scope (values only — never calling game functions, not even getters), and delivers data only to a download or the local capture hub — via user-click-initiated full captures or the opt-in auto-stream timer (combat-only payload; boundary amended 23 Jul 2026 at the player's request, still zero game interaction). Never simulate input, automate equip/enhance/decompile/purchase/combat selection, or make any API/WebSocket/server request against the game or a remote host. Bump the script's `@version` on every change (Tampermonkey won't update otherwise).

## Maintenance conventions

- Append to `docs/decision-log.md` whenever equipment changes, a scarce resource is spent or a mechanic is confirmed.
- When a mechanic is confirmed, move it from `docs/open-questions.md` into `docs/mechanics.md` or `docs/crafting.md`.
- `docs/current-state.md` always represents the latest reviewed baseline; avoid accumulating contradictory "current state" prose.
- Lead with the key decision; be explicit about uncertainty and confidence level (directional vs formula-level).
