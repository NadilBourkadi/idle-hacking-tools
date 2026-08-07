---
name: advise
description: Standing Idle Hacking progression advisory — craft verdicts, homelab queue, hardware buys, open tests — from the latest capture, in a fixed format. Use when the player asks "what should I do next", for spending advice (Stability/credits/hackcoin/chips), or after a fresh capture lands.
---

# /advise — standing progression advisory

Produce one advisory from the **latest capture** using the query-first tooling.
Never parse capture JSON ad hoc; never read a capture file whole.

## Gather

0. `python3 scripts/ih.py brief` — **the whole gather in one command.** It
   emits, in priority order: audit flags (they outrank everything below —
   progress already being lost), freshness, stats, the suspect rows of the
   assumptions register (asserted/supplied + any DRIFTing live check),
   current-era calibration, the best band-clearing craft candidate per slot
   with its `from:`/`!!` lines, homelab state and queue suggestions, top
   hardware tracks, **the lock/unlock action list**, A/B status with the
   mechanism table, and the diff vs the previous capture. The digest only suppresses what it can **count**, and
   marks every elision inline with the command that expands it.
1. **The digest is a triage layer — drill down on judgement, not by
   default.** Run the full command whenever anything is flagged, close,
   novel, or surprising; never conclude from absence in `brief`:
   - a craft verdict is close or heading for approval →
     `ih.py potential --slot S` (all candidates, plans, econ), then
     `ih.py contract <item> --deepen --order`
   - a verdict leans on any weight → `ih.py assumptions` for the full
     provenance text before quoting it
   - an A/B is being graded or closed → `ih.py ab` (full keep rule,
     pre-registered predictions, raw death arrays)
   - the lock list is short by construction (deltas only); if it is long,
     something drifted — say so rather than just listing it
   - anything flagged STALE must be re-read in game, not reasoned around
   - if you find an anomaly `audit` missed, add the check to `cmd_audit`
     in the same session
2. **Short path:** if `brief` shows zero audit flags, an empty diff, no new
   band-clearing candidate, and no A/B at its target n, write the advisory
   from the digest alone and say so. The fix-on-discovery rule below is
   unchanged on either path.
3. `docs/current-state.md` (bottleneck model), `docs/candidate-status.md`
   (holds/locks), `docs/equipment-tests.md` + recent `docs/decision-log.md`
   (open A/B tests, pending log entries).

## Fix-on-discovery (precedes even the priority order)

If anything is found to be wrong during the gather — a weight contradicted by
the ledger, a stale doc line, a mis-scoped filter, a broken accessor — **fix it
in this session, before writing the advisory**, then re-run whatever it
invalidates. Do not write "worth revisiting", "belongs in its own change" or
"resolve it next session". Those phrases have preceded every silent-corruption
bug this workspace has had; see the anti-deferral rule at the top of
`CLAUDE.md`. A deferral is legitimate only when blocked on data that does not
exist yet, and then it goes in `ihlib.PENDING_REFITS` with a named unblock
condition. `ih.py audit` lists any such rows first and `potential`/`contract`
banner them, so a known-wrong constant can never quietly produce clean numbers.

## Priority order (overrides everything below)

**In-game progression first; clean measurement second.** The player has limited
time and patience — a staged, purity-preserving plan is a real cost, imperfect
attribution is a cheap one.

- Recommend **everything worth doing in one session**. Never stagger
  independently-good actions across hours or days so each gets a clean window.
- Never insert a "bank N deaths for a baseline first" step, freeze the homelab
  or hardware queue to protect a test, or defer a genuinely good upgrade
  because it perturbs a metric.
- Sequence two actions only when one **changes the correct choice** for the
  other — never for attribution. Otherwise order by what starts a real-time
  clock soonest (build slots first), then by attention cost.
- Confounded windows are fine: say plainly that the period measures a
  **bundle**, keep the passive ledger running (it is free), and attribute
  later or not at all. Methodology improves across sessions, not by slowing
  any one of them.

## Judgement rules (non-negotiable)

- Craft verdicts: only `potential` deltas clearing **UPGRADE_BAND** count —
  read the current band from `ih.py assumptions` (±5 as of 31 Jul 2026),
  never a hardcoded number. The ~5-point conservatism discount is RETIRED
  (wrong sign; see calibration). Judge close calls with `ih.py contract
  --deepen [--order]` — mean/p10/P(upgrade) — never by adjusting a point
  estimate, and read the `from:` decomposition plus the Δ-ex-suspect line
  before trusting a headline score. Apply the empirical guardrails in
  `CLAUDE.md`: sustain-anchor preservation, multiplicative AtkDmg loss that
  linear weights under-penalize, and the accessibility check (label every
  gate).
- **Record every approved craft** with `ih.py calibration --record "<item>"
  --slot S --projected N --p10 N --p90 N --p-upgrade N --date YYYY-MM-DD` at
  contract time, and fill `--realized` once the craft resolves. Three crafts
  are graded under the current planner (bias +20.7, interval coverage 0/3 —
  intervals are too narrow); every new grade sharpens the band re-fit.
- An approved craft is delivered as a full `docs/crafting.md` §10.1 contract —
  a name and a score is not a deliverable. At most one approved craft per
  advisory; everything else is a hold with a one-line reason. The craft is not
  a reason to hold back the homelab or hardware actions — all of them ship in
  the same session.
- Currencies are ranked by scarcity: **hackcoin > chips > Stability on the
  target item > credits** (credits ≈ unlimited; resources buyable ~2 cr/unit).
  Keep a hackcoin reserve for the next install gates (Hacking Simulator and
  Power & Cooling Rack are installed; next are the homelab-12 unlocks —
  CI/CD Pipeline, Snapshot Rollback, Quarantine Rules, Fan Controller —
  check `ih.py homelab` for their hackcoin lines when they surface).
- Homelab progress points are the route to install gates; credit-only jobs
  preferred when hackcoin is tight. **Rank by points per slot-hour** — build
  throughput is a fixed pool split across active jobs, so slots buffer work
  but never add rate (`mechanics.md` §15). Free slots are not a loss while
  something is running; **nothing active AND nothing queued** is. To reach a
  specific install gate soonest, run that job with as few others as possible
  and say plainly what it costs in points.
- **Never write "refill the homelab" or any bare imperative with no object.**
  Name the upgrade, target level, points, duration, cost **and the UI section
  it sits under** — homelab upgrades live beneath an install, so it is
  "Virtual Desktops [Command Workstation]", never bare "Virtual Desktops".
  `ih.py audit` and `ih.py homelab` both print a QUEUE block that does this
  (`ihlib.homelab_fill_suggestions`, ranked by total points because an idle
  slot costs more than a better hourly rate). Copy those lines through. The
  same rule applies to every recommendation: if it is worth saying, resolve it
  to a specific purchase, craft step or swap before writing it.
- Hardware %, homelab % and equipment % share **one additive pool**
  (confirmed formula-level 27 Jul 2026, `docs/mechanics.md`); a track whose
  gear-flat multiplicand is 0 produces exactly 0. The per-chip *ranking* is
  now exact; the CRAFT_WEIGHTS behind it remain heuristic — say "directional"
  about weights, not about pooling.
- If a combat A/B test is open, note which recommendations land inside its
  window and that the readout will measure a bundle. Do **not** defer them.

## Output format (exact sections, in order)

1. **TL;DR** — up to 4 bullets: best next action per scarce currency
   (Stability/craft, hackcoin/homelab, chips/hardware) + any urgent flag.
2. **Crafts** — approved craft with §10.1 contract, or "none approved" +
   the nearest-miss hold and why.
3. **Homelab queue** — the exact next jobs in order (name → target level,
   cost, +pts), what they do to the level-gate timeline, hackcoin budget line.
4. **Hardware buys** — exact purchases (track → levels, chip cost), reset
   note if available.
5. **Lock / unlock** — the exact `ih.py locks` actions, **deltas only**:
   which items to lock and which previously-locked items to unlock and
   decompile. **The operating model is that anything NOT locked is
   regularly decompiled and lost**, so this section is a standing part of
   every advisory, not an occasional one. Never list items that need no
   action, and never dump the inventory. Every line is an imperative with
   an item name. Value is the WEAKER of raw Δ and Δ-ex-suspect, so no
   lock verdict rests on a flagged weight, and depth is **one base per
   slot** — measured from a 0.92/day keeper arrival rate, a 1.2-day median
   base age at craft, and inventory slots priced at 10 hackcoin. **Quote
   the inventory denominator** (used/cap and the slot price) whenever the
   list recommends holding anything; the first version of this section
   recommended 13 holds without it and was rightly challenged. **The revert path of a hot A/B
   is held by name and must never appear in the unlock list** — if
   `protected_revert_items()` raises, the active experiment is missing its
   `revert_item` and that is a declaration defect to fix before advising.
6. **Tests in flight** — open A/Bs, data still needed, contamination
   warnings.
7. **Log actions** — decision-log entries now due (equipment changes, scarce
   spends, confirmed mechanics to move out of open-questions).

Lead with the decision; state confidence (directional vs formula-level) on
anything heuristic. Ask for a fresh capture instead of guessing when a
decision depends on state the capture doesn't show.
