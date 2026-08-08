# Incident index — failure modes, and the rule that owns each

An **index, not a store.** Every incident below is already written up properly
in `decision-log.md` on the date given; this page exists to answer a different
question — *"has this kind of mistake happened before, and what stops it
now?"* — which a 36,000-word chronological log cannot.

Read it when a rule in `CLAUDE.md` looks excessive. Each one is here because
it was learned the expensive way, and the cost is in the third column.

**Rule of use:** if you are about to do something on this list, the rule that
owns it is not negotiable in that moment. Argue with it afterwards, in writing.

| # | failure mode | what it cost | owned by |
|---|---|---|---|
| 1 | **A known-wrong weight left in place** because fixing it "deserved its own change" (`CRAFT_WEIGHTS_FLAT["Barrier"]`, measured ~5× its applied value) | every candidate ranking for the rest of that session, including a craft verdict that was acted on. Surfaced only because the player asked an unrelated question hours later | *Never defer a known defect* |
| 2 | **A flagged weight left asserted for two days** (`Acc` at 1.0, "probably far too high"; measured 0.14), with `potential` printing footnotes instead of the fix | everything Accuracy-carrying mis-ranked throughout | *Never defer a known defect* |
| 3 | **An untested default** — the craft planner's T3 tier cap | excluded the two best steps on the ladder; gain per Stability point peaks exactly at the excluded step. Uncapping flipped two slots from sidegrade to UPGRADE | *Run `assumptions` first*; *state the regime* |
| 4 | **A model used outside its fitted regime** — zone transition cost, fitted on a handful of high-streak fights in one zone | wrong by 4.5× when applied across zones | *State the regime* |
| 5 | **A model validated at one end of its range only** — `hardware_plan`, exercised at a ~1.08M-chip reset budget | returned a 108K-chip plan against a 37K balance | *State the regime*; *prefer self-validating models* |
| 6 | **A number nobody ever looked up** — "attack speed → more fights per hour", asserted, never measured | propagated through four sessions, priced into two craft verdicts, written into an A/B keep rule. Cadence is a fixed tick; a +9.9% AtkSpd equip moved it 0% | *Measure before it becomes an argument* |
| 7 | **A weight fitted on n=1** (`Corrupt`, one fight at 12 points) while the ledger held the natural experiment | stated rationale ~2× off and the response non-linear; nobody looked for six days | *Measure before it becomes an argument* |
| 8 | **A log field's meaning assumed** — `pcd`/`ecd` documented backwards | a week of analysis built on it. The giveaway was that `pcd` is flat across all nine enemy classes, which no measure of incoming damage could be | *A field's meaning is a hypothesis* |
| 9 | **A pooled mean that hid a bimodal split** — "net drain is negative in every streak band" | true and deeply misleading: three of nine enemy classes were strongly positive and caused 100% of deaths | *Segment by the natural categorical* |
| 10 | **A cohort selected with no date bound** (`17000 < max_hp < 18000`) | pooled a full day of pre-craft fights; two constants "refined", published and withdrawn within the hour | *Declare the cohort first* |
| 11 | **A field treated as inert because it read empty** — `locked_resources` before the hardware reset | the reset filled it; the refunded hackcoin was permanently shop-bound, invalidating a claim already given to the player | *Enumerate what an irreversible action writes* |
| 12 | **Inference from minified client code, over the game's own description** — homelab build throughput read as per-slot | wrong for a week, then wrong twice more in one session; "4 slots sat empty" was written up as a loss it never was | *In-game text outranks code inference* |
| 13 | **A currency read without its conversion graph** — credits as a depleting stock | a whole strategy (defer the Hacking Simulator, switch the homelab to credit-efficient jobs) built on it. Hackcoin converts at ~8.33B credits each; one question would have replaced hours | *A decision-critical unknown is a blocker* |
| 14 | **A model fitted on currently-owned state** — tier ladders fitted per capture | decompiling a +1.7 sidegrade deleted the only T7 observation owned and moved a live verdict +9.0 → +4.6 with no game state changed | *Prefer archive-wide fits* |
| 15 | **Affix display names assumed unique** — they are not; two affixes on one item both read "of Mending" | the contract simulator promoted both for one phase's Stability: mean +98.5 against a planner ceiling of +52.3. Caught only because a mean cannot exceed an optimal-plan ceiling | *Build the second opinion* |
| 16 | **Two panels computing the same thing separately** — homelab ETA in raw ticks vs build-speed-adjusted | 229 min vs 73 min for the same job. Recreated within hours of being fixed, in `_audit_decompile_locks`, and again in a stale audit message | *Build the second opinion*; one implementation, two callers |
| 17 | **A schema field nobody had ever read** — `decompile_locked` | three weeks. The lock set was almost exactly inverted against value: 17 of 18 locked items not worth holding, 13 band-clearing bases unlocked and one click from irreversible deletion | *Audit before you model* |
| 18 | **A recommendation shipped without its denominator** — hold 13 craft bases | on *hackcoin*, the exact resource the denominator rule was written about. Corrected to 6 once the arrival rate (0.92/day) and craft age (median 1.2d) were measured — both sitting in the capture the whole time | *Never recommend a spend without its denominator* |
| 19 | **A new tunable that decided irreversible actions, unregistered** — `KEEP_DEPTH_PER_SLOT` | invisible to the provenance sweep that exists to catch exactly this. Now enforced by `AssumptionsRegistryTest`, whose first run found `DAMAGE_K` and the hit law unregistered too | *Register every constant* (enforced) |
| 20 | **"Verified" claimed from a check that could not see the failure** — a green local suite, twice | ruff was never run locally; then a test read live captures and passed against 146 of them while CI, which has none, failed. One failing job masked the other | *`make ci` is the gate*; *"tests pass" is a fact, "verified" is a claim* |
| 21 | **Numbers restated in prose, going stale silently** — three in `CLAUDE.md` at once | an untested-constant tally, the calibration bias, and a pointer to a file deleted hours earlier. All three were computable on demand | *Prose states rules; the tool states numbers* |
| 22 | **A safety rule that only protected the status quo** — "a contested item gets NO action, it stays as it is" | the guarantee held only for items already LOCKED. For a fresh drop the status quo is UNLOCKED, and unlocked means deleted, so unlocked contested bases were destroyed by exactly the flagged weight the rule promised would never decide a decompile. Four band-clearing bases lost, including the highest-raw base owned (+121.2) | *State the default an inaction rule falls back to* |
| 23 | **A measured constant justified by the wrong quantity** — `KEEP_DEPTH_PER_SLOT = 1` | "0.92 band-clearing keepers/day" counts everything over the band and treats those bases as interchangeable. Top-decile bases arrive every 6.8 days, not daily, so depth 1 discarded rank-2 bases whose real replacement time was ~7x its own justification | *Check that the rate you measured is the rate the decision needs* |
| 24 | **One finding kept in two registries, one of them unread by most callers** — the Barrier score→depth result lived in `DEPTH_SUSPECT_STATS` (hardware only) and not in `SUSPECT_WEIGHTS` (crafts, locks, contracts) | `hardware` printed the caveat while the craft board three sections above it ranked Barrier at face value in the same `brief`. Brutal Driver of Hardening read +57.0 raw / −6.4 ex-suspect; Leviathan's Firewall of Isolation +98.8 → −120.6 | *Build the second opinion*; merge, never synchronise |
| 25 | **A disbelieved weight was applied to the scoring but not to the PLAN** — `locks` re-scored the raw-optimal craft plan ex-suspect | that plan spends Stability where the flagged family scores highest, so the ex-suspect number priced a contract nobody would run. It released the best Analyzer base owned to the deletion list at +43.4 (true ex-suspect value +70.9) in the same advisory where `potential` called it best in slot | *If you disbelieve a weight, re-optimise under the disbelief — do not just re-score* |
| 26 | **A stat family's formula assumed from its siblings** — the homelab term put in the pool for gear-flat stats | wrong by +0.35% the moment a gear-flat stat first carried one, in 159 captures. The game credits the raw fraction as a flat addend, so "+0.5% Corruption" delivers +0.005 — ~90× less than the description, and a homelab upgrade recommended for its stat is worth nothing | *Self-validate against the game's own totals* |

## What the shape of this list says

**Twenty-two of the twenty-six were found by something other than reading the
code** — a player question, a coincidence, a cross-check between two views,
or an automated review. That is the argument for building second opinions
deliberately rather than trusting a careful read.

**Nine are the same underlying mistake**: a number was believed without anyone
checking whether it had ever been measured (#3, #4, #5, #6, #7, #13, #18, #19,
#21). That is why `ih.py assumptions` runs before any verdict resting on a
weight, and why the register is the first thing `audit` prints.

**Four are duplication** (#15, #16, #21, #24): the same fact computed, written
or registered in two places, drifting apart. Prefer one implementation with two
callers, and prefer pointing at a command over restating its output. #24 is the
sharpest form — the two copies never drifted, one was simply never consulted by
the callers that needed it, so both were individually correct and the advice was
still wrong.
