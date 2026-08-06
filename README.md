# idle-hacking-tools

A measurement-driven research toolkit for the browser game
[Idle Hacking](https://www.idlehacking.com/): passive state capture, a
provenance-tracked analysis library, and a Monte-Carlo craft planner —
plus the complete research log of the campaign that built it.

Zero runtime dependencies. Everything runs on the Python standard library.

## What makes this interesting

This started as "which item should I equip" and became an exercise in doing
empiricism properly against a system whose rules you don't get to read:

- **An assumptions register with provenance.** Every tunable constant in the
  model is registered as `measured` / `asserted` / `inherited` / `supplied`,
  with the evidence, the date it was last validated, and — where possible — a
  live self-check against current data (`ih.py assumptions`). The register
  exists because every analysis defect this project ever shipped traced back
  to a number somebody asserted and nobody re-tested.
- **Pre-registered experiments.** Equipment changes get declared A/B gates
  *before* the change is made — keep/revert thresholds, contamination checks,
  and falsifiable mechanism predictions, written down in code
  (`experiments.py`) where they can't be quietly reinterpreted after the
  readout.
- **Simulation-first decisions, live confirmation.** The game's own in-client
  simulators are treated as instruments: validated for variance realism and
  absolute bias against the live ledger, then used for paired gear readouts
  that resolve in minutes what live data resolves in days. Craft plans are
  approved on a simulated outcome distribution (`ih.py contract`), never on a
  point estimate.
- **A defect-driven audit sweep.** `ih.py audit` checks for every way this
  project has ever silently lost progress — each check exists because the
  thing it catches actually happened once.
- **The research log is part of the repo.** `docs/decision-log.md` and
  `docs/open-questions.md` record what was believed, when, why, and what
  overturned it — including the mistakes, which are the instructive part.

## Repository layout

| Path | What it is |
|---|---|
| `scripts/ihlib.py` | The analysis library: capture parsing, stat composition, fitted combat laws, craft simulation, hardware/homelab planners, the assumptions register |
| `scripts/experiments.py` | The campaign record: pre-registered A/B declarations (data, quarantined from the library logic) |
| `scripts/ih.py` | The CLI: `audit`, `brief`, `potential`, `contract`, `assumptions`, `ab`, `sims`, and friends |
| `scripts/capture-hub.py` | Localhost hub: serves the userscript, receives and routes its exports |
| `tools/item-loadout-capture.user.js` | Tampermonkey capture script — strictly read-only against the game (see below) |
| `docs/` | The research log: mechanics working models, crafting economy, experiment results, decision log, open questions |
| `data/` | **Local-only, git-ignored.** Your captures, combat ledger, and sim runs live here; the public repo ships none |

## Quickstart (fresh save, fresh clone)

1. Install [Tampermonkey](https://www.tampermonkey.net/) and add
   `tools/item-loadout-capture.user.js`.
2. Run the hub: `python3 scripts/capture-hub.py` (or install
   `scripts/idle-hacking-capture-hub.service` as a systemd user service).
3. Open the game; use the capture panel to take a full-state capture — it
   lands in `data/captures/` automatically. Optionally enable the combat
   auto-stream to build the fight ledger passively.
4. Ask questions: `python3 scripts/ih.py audit`, then `brief`, then anything
   else. Every command degrades gracefully while your `data/` is still thin —
   the fitted constants in the library came from one campaign's data and are
   clearly marked with their provenance, so re-validate them against your own
   ledger before trusting them deeply (`ih.py assumptions` shows which ones
   self-check).

## Safety contract (the userscript)

The capture tool is **passive and read-only** by design: it reads game-state
bindings from page scope (plain data values; the game's state objects are
deserialized WebSocket payloads, and the tool's guarantees rest on that
documented assumption), never calls game functions, never simulates input,
and never talks to any server — its only network destination is the
localhost hub. It cannot play the game for you; it only remembers what the
game already showed you. The full boundary and its history are in
`docs/capture-tool.md`.

## Development

```sh
python3 -m unittest discover tests   # zero-dependency test suite
ruff check scripts tests             # lint (optional, config in pyproject.toml)
```

CI runs both on every push.

## License

MIT — see `LICENSE`. The `docs/` research log is part of the repository and
shares the license. Idle Hacking itself belongs to its developers; this
project is an unaffiliated fan-made analysis toolkit.
