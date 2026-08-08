# Idle Hacking — research, strategy and tooling workspace

Long-running analysis workspace for the browser game **Idle Hacking** (single-player campaign). Migrated from a ChatGPT Project on 2026-07-22; the raw handover is preserved in the initial git commit. Three kinds of work happen here: loadout/crafting strategy analysis, game-mechanics research, and development of the passive capture userscript.

**How this file works.** It states *rules*. Numbers come from the tool (`ih.py assumptions`, `ih.py calibration`), mechanics from `docs/mechanics.md`, and the incidents behind each rule from `docs/incidents.md` — a one-page index into `decision-log.md`, worth reading when a rule here looks excessive. Every rule below cost something to learn.

## Source-of-truth order

1. The latest capture in `data/captures/` (query via `scripts/ih.py`).
2. `docs/current-state.md` (interpretation) and `docs/decision-log.md`.
3. `docs/mechanics.md`, `docs/crafting.md`, `docs/static-analysis-2026-07-22.md`.
4. Older schema-4/3 exports (`data/loadouts/`) and historical combat logs (`data/combat/`).

## File map

- `docs/mechanics.md` — combat-stat model, equipment structure, build guardrails (§21), evaluation method.
- `docs/crafting.md` — Stability/Compile economy, operation reference, decision protocol, §10.1 craft-contract template.
- `docs/current-state.md` — latest reviewed loadout baseline and bottleneck model.
- `docs/candidate-status.md` — per-item project status and safe-decompile list.
- `docs/equipment-tests.md` — measured A/B trial evidence.
- `docs/decision-log.md` — append-only record of decisions.
- `docs/incidents.md` — failure modes indexed by kind, and the rule that owns each.
- `docs/open-questions.md` — unknowns and planned tests; prevents working models becoming "facts".
- `docs/data-dictionary.md` — combat-log field meanings, lazy-panel notes, analysis conventions.
- `docs/capture-tool.md` — userscript reference and safety boundary.
- `docs/simulator-protocol.md` — Hacking Simulator operating manual; **§9 is the CI/CD protocol** (sim-first equip decisions, live gates for confirmation).
- `docs/game-client-internals.md` — how the client stores state; basis for full-state capture.
- `data/captures/` full-state captures · `data/combat-stream/` fight/death ledger · `data/sim-runs/` simulator runs · `data/predictions.jsonl` craft prediction ledger · `data/incoming/` needs triage · legacy exports in `data/loadouts/`, `data/combat/` (see `data/README.md`).
- `scripts/ih.py` + `scripts/ihlib.py` — capture query CLI and analysis library. `ih.py --help` lists every command; that list is not duplicated here because it drifted when it was.
- `tools/item-loadout-capture.user.js` — the read-only capture script · `scripts/capture-hub.py` — localhost:8123 hub (systemd user service `idle-hacking-capture-hub`).

## Working with the data — query-first

**Run `ih.py assumptions` before any verdict that rests on a weight or a threshold.** It is the provenance register for every tunable constant — `measured` / `asserted` / `inherited` / `supplied`, and when each was last validated. **Every defect ever found in this workspace has been an `asserted` or `inherited` row in that table.** Anything it lists as `asserted` or `inherited` is a hypothesis: say so in the advisory rather than quoting its output as fact. Read the counts off the command, never from this file — an untested-constant tally restated in prose goes stale silently, and this one did. New tunable constants must be registered in the same change that introduces them (`AssumptionsRegistryTest` enforces it).

**Use `python3 scripts/ih.py <cmd>` for all capture queries; never parse capture JSON ad hoc.** Captures land in `data/captures/` automatically; latest = lexicographically last. For bespoke analysis import `ihlib` — it encodes the slot mapping, scaling law, cost model, stat-composition families, hardware cost curve/planner and archive-wide tier ladders so they are never re-derived.

**Write every contract with `ih.py contract --deepen`, and aim deeper than `plan_craft` proposes.** `plan_craft` stops when the next step's expected Stability exceeds the budget, maximising P(all phases complete) — a vanity metric. Tier value compounds while attempt cost grows linearly, and an over-committed plan that runs out of Stability simply stops, leaving a shallower craft that is still an upgrade and that you need not equip. Downside bounded, upside not. **A repeated, successful deviation from a recommendation is a defect report about the recommendation** — the player beat the contract this way twice before it was modelled.

**Judge a close craft by simulating the contract, not by discounting it.** `ih.py contract` returns the outcome distribution. A flat discount cannot see that phases are **non-separable** (Stability spent cuts Compile, which multiplies every affix), nor that the downside is bounded and optional — a bad craft simply is not equipped. **Phase order is not cosmetic**: an expensive low-probability step belongs last, where it absorbs leftover Stability instead of starving the cheap phases. Use `--order`.

**The "~5-point contract-conservatism discount" is retired — it has the wrong sign.** Bias has been positive in every uncapped era; projections under-shoot. Read the current bias and n off `ih.py calibration`. **Record every approved craft with `calibration --record` at contract time and fill `--realized` after.**

**Candidate judgements use post-craft ceilings, never current rolls.** Equipped items are at 0 Stability; inventory items carry 25–30 Stability of headroom, so `compare`/`candidates` systematically understate them. `ih.py potential` projects realistic ceilings and prints a **`from:` decomposition** of every Δ — read it, because a scalar hides which weight is carrying the verdict.

**Run `ih.py audit` first, every time, before any optimization.** Every check exists because a real instance was missed by going straight to modelling. If you find an anomaly the audit missed, add the check.

- Captures are ~1 MB. **Never read one whole** — `ih.py` or targeted `ihlib` scripts only.
- **Data files are immutable once written**; a new capture beats editing an old one. `data/` is git-ignored.
- Lazy panels (`statsBreakdown`, `combatLog`, `homelabInfo`, …) are captured only if that game panel was opened — `ih.py captures` shows what each contains. Details in `docs/data-dictionary.md`.

**Inventory is not keep-by-default: anything NOT `decompile_locked` is regularly decompiled and lost.** The lock flag is the only thing between a craft base and deletion, so drift in it is a silent irreversible loss. `ih.py locks` prints the daily **delta**; `audit` flags both directions. Keep value uses the **weaker** of raw Δ and Δ-ex-suspect and discard needs **both** readings to agree. An item they disagree about is **held, not ignored**: already-locked stays locked, and an **unlocked** one is a LOCK action — "no action" protects only the status quo, and for a fresh drop the status quo is deletion (this cost four bases on 7 Aug 2026). **Hold depth is `KEEP_DEPTH_PER_SLOT` bases per slot, sized on how long a base of EQUAL QUALITY takes to replace** — top-decile ~6.8 days in the measured slot, *not* the ~0.92/day rate at which any band-clearing base arrives, which counts them as interchangeable and was the wrong quantity. Band-clearing bases held beyond that depth are printed as **AT RISK**, because a delta-only list is otherwise silent while they are deleted. The **revert path of a hot A/B is held by name** via the experiment's `revert_item`.

## Never defer a known defect (highest-priority rule in this file)

**When you discover something is wrong, fix it in the same session you discover it. There is no "later".** This has been the single most damaging failure mode in this workspace, it has recurred in several disguises, and every instance looked reasonable at the time.

- On 29 Jul 2026 `CRAFT_WEIGHTS_FLAT["Barrier"]` was measured at ~5x its applied value and **deliberately left unchanged**, with the written justification that re-fitting "moves live verdicts, so it belongs in its own change". Every candidate ranking produced for the rest of that session was computed from a number already known to be false — including a craft verdict that was acted on. It surfaced only because the player asked an unrelated mechanical question hours later.
- `CRAFT_WEIGHTS_PCT["Acc"]` sat at an asserted `1.0` for two days after being flagged as "probably far too high", with `potential` printing "ex-suspect" footnotes instead of the weight being fixed. Measured value: **0.14**. Everything Accuracy-carrying was mis-ranked in the meantime.

**The reasoning that produces this failure is always plausible**, which is why it needs a hard rule rather than judgement: *"it deserves its own change"*, *"it would move live verdicts"*, *"an A/B is mid-flight"*, *"resolve it with the Software Profiler later"*, *"flag it and move on"*. All of these are ways of shipping advice you already know is wrong. **Note the asymmetry that makes them wrong: leaving a known-bad value in place also moves verdicts — away from the truth — and does it invisibly, with no flag on the output.** A fix is visible and reviewable; a deferral is neither.

Concretely:

- **Fix it now.** A weight, a doc line, a mis-scoped filter, a wrong field description, a broken accessor — correct it in the same change, then re-run whatever the change invalidates and re-state any verdict that moves. Say plainly in the reply that a number changed and why.
- **A deferral is only legitimate when the fix is blocked on data that does not exist yet** — not on effort, tidiness, or comparability. Then it MUST be entered in `ihlib.PENDING_REFITS` with an `unblock` naming the specific observation that resolves it. `audit` lists those rows **first**, and `potential`/`contract`/`hardware`/`locks` print a banner while any exist, because numbers computed from a known-wrong constant must never look clean.
- **Never let an in-flight A/B block a fix.** Comparability is worth less than correctness. Re-baseline the test or record a segment boundary — both are cheap and `ih.py ab` supports both.
- **This outranks the output format, the session's plan, and the user's immediate question.** Fixing the defect *is* the work.

## Two rules that generalise the rest

**Every defect ever found here was found by two things that should agree, disagreeing** — never by re-reading code. A contract mean above its own planner ceiling; two panels 3.125× apart on one ETA; a chip ranking that contradicted the craft in the same advisory. **So build the second opinion deliberately.** Where a decision-bearing number has one producer, its defects are invisible: prefer models that self-validate against a game-provided ground truth (`hardware_cost_curve` checks itself against the game's own reset refund), and when two commands report on the same thing they must **share one implementation**, not two that agree today.

**These rules govern any decision-bearing number, not just the game model** — tooling thresholds, display cut-offs and defaults are model constants too. All three 7 Aug violations came from reading them as being about gameplay analysis only. Corollary: **"the tests pass" is a fact, "verified" is a claim** — state which one you have. A review found 10 confirmed defects in code that already had 30 passing tests, because tests written alongside a misunderstanding encode it.

## Analysis rules

- **Every recommendation resolves to a specific action.** Never write a bare imperative with no object — "refill the homelab", "spend the chips". Name the upgrade/item, target level, cost, duration and **always the UI section it sits under** (homelab upgrades live beneath an install — "Virtual Desktops [Command Workstation]", never bare). A name without its panel still means hunting.
- **Progression first; measurement second.** Recommend every worthwhile action in the same session; never stagger independently-good actions for attribution, never gate progress behind a baseline, never freeze a queue to protect a test. Sequence two actions only when one changes the *correct choice* for the other. Confounded windows are fine — say the period measures a bundle and move on.
- **If one unknown fact would flip the recommendation, it is a blocker — resolve it or branch the advice on it.** Never write the confident version and append the unknown as a closing caveat. Corollary: **a stock-and-flow model of any currency is incomplete until the conversion graph is checked** — what converts into it, what it converts into, at what rate.
- **Never recommend a spend without its denominator, and measure the rate before recommending, not when challenged.** "Spend 133,530 chips" is not an action; "133,530 chips = 24h of income = 98% of stock" is a decision. Check whether the spend is **recoverable**. And do not hedge against a risk you have not sized.
- **Before a quantity enters a verdict, check whether anything has ever measured it — and if nothing has, check the archive for natural variation before concluding it is unmeasurable.** The capture archive is a longitudinal dataset and most weights have a free natural experiment sitting in it. Segment by the stat's own change-points, match on streak band, and normalize against a co-scaling quantity so player growth does not masquerade as effect.
- **A model fitted on *currently-owned* state rots when the inventory turns over.** Affix ranges are game constants, so `tier_ladders_archive()` unions every capture. Prefer archive-wide fits wherever the underlying quantity is a constant.
- **An A/B keep rule may gate on the outcome and on contamination checks — never on the mechanism you guessed.** Being right about the effect and wrong about why is the normal case. Amend a rule only for impossibility, never after seeing a favourable result; when a rule turns out mis-specified mid-flight, record that **before** the readout and let the primary outcome govern.
- **State the regime a model was fitted in, and re-validate before using it outside that regime.** Prefer models that **self-validate against a game-provided ground truth**; where that is impossible, exercise the model at both ends of its range before trusting it.
- **Declare the cohort before you compute anything from it.** Any era/segment filter is a regime declaration — `ihlib.cohort_summary(rows)` prints its own boundaries and warns when `max_hp` spans a gear change.
- **A log field's meaning is a hypothesis until it is shown to vary with the thing it supposedly measures.** Before a field enters an argument, run the discriminant check: find something it must correlate with, and confirm it does.
- **Before concluding from a pooled mean, segment by the natural categorical and look for bimodality** — enemy class, zone, item era, whichever grouping the game itself uses.
- **A scalar ranking cannot audit the weights it is built from.** Every weight defect here was found by testing a *mechanism* against the ledger, never by looking at `potential` output — which renders wrong weights as confident scores. Treat any question about how a stat works as higher priority than any ranking that uses it.
- **Before an irreversible or once-a-month action, enumerate the state it touches and check every field it will *write*, not just the ones it reads.** A field that is empty now may be a post-condition field. When a field's meaning under the action is unclear, say so before recommending it.
- **Check accessibility before recommending any game system.** Installs, upgrades, zones and craft operations carry gates in the capture; label anything not currently reachable with its gate ("unlocks at homelab 9"). Gated upgrades may be invisible in the UI, so never assume the player has seen them. Use display `name` fields, never internal slugs.
- **Hackcoin is the only scarce currency; credits are bought with it.** Price every decision in **hackcoin-equivalents** (`ihlib.hackcoin_equivalent`), never in credits — reading a balance in credits produced exactly one wrong recommendation. Spend credits freely, never stagger or defer to bank them, and rank purchases by hackcoin cost. Basic resources are purchasable at ~2 credits/unit, so on-hand gathering resources are never a schedule gate. The rate is a **supplied** constant — see `assumptions`; contract-board mechanics are in `mechanics.md` §20, and **contract throughput is the real economic lever**.
- **In-game description text is primary evidence and outranks any inference from minified client code.** Homelab build throughput is a **fixed pool split evenly across active jobs — slots never add rate** (`mechanics.md` §15): rank jobs by **points per slot-hour**, an empty slot costs nothing while one job runs, and the only losing state is **nothing active AND nothing queued**. To reach one install gate soonest, run it with as few concurrent jobs as possible and state the point cost.
- **Separate verified facts, working models and unknowns. Never invent formulas or mechanics.** Evaluate candidates as crafting bases and as parts of the whole loadout — never on Item Level alone; follow the `crafting.md` §10 output contract.
- Long-streak loss analysis and combat-log reading conventions: `mechanics.md`, `data-dictionary.md`.

## Code and repository work

**Run the `/code-review` skill on any significant change to `scripts/`, `tools/` or `tests/` before wrapping up** — anything beyond a one-line constant. Run it *after* the tests pass, not instead: the suite proves the code runs, the review catches what the suite was written blind to. **Fix what it finds in the same session** (the anti-deferral rule governs review findings exactly as it governs weights), and report what was done; if a finding is declined, say why. The workflow-backed review is expensive (~1.5M tokens) — reserve it for new subsystems and anything touching irreversible actions; use the inline review otherwise.

**Git.** Never commit to `main` — branch (`fix/`, `feat/`, `chore/`). Commit when a unit of work is coherent and green; if describing it needs "and" twice, it is two commits. **Each commit must stand alone with the suite passing**, not just the tip. Rebase into a readable story before pushing. Message: `<type>(<scope>): <imperative>` plus a body saying **why** and, for anything found by review or accident, **how it was found**. **Run `make ci` before every push** — `python -m unittest` alone is not sufficient and has let a red PR through twice. **After pushing, poll the run and fix failures unprompted**; a red PR is unfinished work, not a notification. A failing job masks later ones, so re-check the whole pipeline after each fix. Open a PR with `gh`, leading on decision-relevant changes.

**Finishing a branch means opening the PR — do not wait to be asked.** The moment the work is complete and verified locally (every commit independently green, `make ci` passing at the tip, review findings fixed), **push and open the PR in the same turn**, then poll CI. A branch sitting unpushed on a local machine is not delivered work, it is work the player cannot review — and the review is the point. Do not end a turn with "ready to push, say the word": that invents a gate this file does not contain, and it cost a full session of finished work sitting idle on 8 Aug 2026. **The ONLY gate is merge.** Push, PR, CI polling and unprompted failure fixes are all part of finishing; **merging is the single step that needs the player's explicit go-ahead.** If the work is genuinely incomplete, say what is missing — do not describe complete work as if permission were the blocker.

**Never merge without the player's explicit go-ahead.** The PR is the review surface: lead the description with what changes a decision or a number, name anything you want a second opinion on, and flag judgement calls made under uncertainty so they can be overruled cheaply.

**Tests are data-isolated by construction:** `IH_DATA_DIR` points them at an empty tree so none can read the working tree's captures (`DataIsolationTest`). Build synthetic captures — never call `load_capture()` in a test.

## Userscript safety (non-negotiable)

The capture tool must remain passive/read-only: it reads game state bindings from page scope (values only — never calling game functions, not even getters), and delivers data only to a download or the local capture hub — via user-click-initiated full captures or the opt-in auto-stream timer (combat-only payload; boundary amended 23 Jul 2026 at the player's request, still zero game interaction). Never simulate input, automate equip/enhance/decompile/purchase/combat selection, or make any API/WebSocket/server request against the game or a remote host. Bump the script's `@version` on every change (Tampermonkey won't update otherwise).

This boundary is **semantic and cannot be tested**. CI checks only that `@version` moved when the file did; no check verifies the read-only guarantee, and none should pretend to — a green test named for it would stop this rule being read. This paragraph is the enforcement.

## Maintenance conventions

- Append to `docs/decision-log.md` whenever equipment changes, a scarce resource is spent or a mechanic is confirmed. Add a row to `docs/incidents.md` when a *new failure mode* appears.
- When a mechanic is confirmed, move it from `open-questions.md` into `mechanics.md` or `crafting.md`.
- `docs/current-state.md` always represents the latest reviewed baseline; avoid accumulating contradictory "current state" prose.
- Lead with the key decision; be explicit about uncertainty and confidence (directional vs formula-level).
