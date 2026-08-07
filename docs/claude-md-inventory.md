# CLAUDE.md consolidation — claim inventory

Working document for the 7 Aug 2026 consolidation. **Nothing moves until this
table is agreed.** Every distinct claim in `CLAUDE.md` appears below exactly
once with a proposed disposition, so no content changes state silently. The PR
diff is then checkable against this table: a deletion with no matching
disposition here is a mistake.

## Dispositions

| code | meaning |
|---|---|
| **KEEP** | stays in `CLAUDE.md` roughly as-is — load-bearing every session |
| **COMPRESS** | directive stays, narrative moves to `docs/incidents.md`, one clause of sting retained inline |
| **MOVE→x** | not a rule; belongs in another doc |
| **MERGE→n** | duplicate or near-duplicate of claim *n* |
| **ENFORCE** | a *total* check can carry it; prose shrinks to a pointer |
| **TRIPWIRE** | a partial check is possible but **may not shorten the prose** (see criterion) |
| **DROP** | stale, superseded, or true-but-inert — reason given |

## The enforcement criterion

A check may replace prose **only if it can enumerate the entire space it
claims to cover** — it iterates the real namespace rather than searching for
known-bad forms. Everything else is a *tripwire*: it catches specific known
regressions and proves nothing. A tripwire must say in its own docstring what
it does not cover and name `CLAUDE.md` as authoritative. **A tripwire may never
be cited as a reason to shorten a rule.**

Rationale: the userscript-safety invariant is semantic ("never interact with
the game"). Grepping for `.click(` misses `dispatchEvent`, binding mutation,
side-effecting getters, `postMessage`, and whatever the next client version
exposes. A green test named `test_userscript_is_read_only` that proves none of
that is worse than no test, because it stops the rule being read.

## Design principles for the rewrite

1. **Prose states rules; the tool states numbers.** Every number restated in
   prose is a number that goes stale silently. Three already had by 7 Aug: the
   untested-constant tally ("2 of 27" vs 4 asserted of 32), the calibration
   bias ("6 of 9, +15.9" vs 7/8, +16.8), and a pointer to `ci-local.sh` after
   it was deleted. All three were computable on demand.
2. **Recency is not significance.** ~1,136 words (20% of the file) were added
   on 7 Aug alone. Those compress first, and hardest.
3. **A rule that has never been violated is a candidate for demotion**; a rule
   violated repeatedly keeps its narrative regardless of length.

---

## Section 1 — header, source-of-truth order (30 w)

| # | claim | disposition |
|---|---|---|
| 1 | Workspace purpose, three kinds of work | KEEP — orients a new reader in 3 lines |
| 2 | Source-of-truth order (capture → current-state → mechanics → legacy) | KEEP — short, load-bearing, referenced constantly |

## Section 2 — File map (571 w)

| # | claim | disposition |
|---|---|---|
| 3 | One-line description per `docs/*.md` (10 files) | KEEP but **compress to one line each**. `simulator-protocol.md`'s entry is 120 words describing the doc's *contents*; that belongs in the doc's own header. |
| 4 | `data/*` directory descriptions | KEEP, compressed |
| 5 | `scripts/`, `tools/`, `capture-hub` descriptions | KEEP, compressed |
| 6 | **Inventory is not keep-by-default / lock model / hold depth** (283 w) | **MOVE→ Analysis rules** — it is a rule, not a file description, and it is the single longest bullet in the section. COMPRESS to the directive + the three measured numbers; the "first sweep found 17 of 18 inverted" narrative → `incidents.md`. |
| 7 | "inventory was 94/102 with slots priced at 10 hackcoin" | **DROP the framing** — `max_slots` is soft (archive held 103/102). Already corrected in `assumptions()`; restating it here duplicates a registered constant. |

## Section 3 — Working with the data (997 w)

| # | claim | disposition |
|---|---|---|
| 8 | Run `assumptions` before any weight/threshold verdict | KEEP — highest-value single line in the file |
| 9 | "Every defect found here has been an asserted/inherited row" + examples | COMPRESS — keep the claim, examples → `incidents.md` |
| 10 | New tunable constants must be registered in `assumptions()` | **ENFORCE** — a test can walk the module's actual constants. Would have caught `KEEP_DEPTH_PER_SLOT`. Prose → one line + test name. |
| 11 | Use `ih.py` for all queries; never parse capture JSON ad hoc | KEEP |
| 12 | Command list | **DROP** — `ih.py --help` is authoritative and this list has already drifted once (`locks` had to be hand-added). |
| 13 | Write contracts with `--deepen`; aim deeper than `plan_craft` | KEEP directive; COMPRESS the 29 Jul Daemon numbers → `incidents.md` |
| 14 | "A repeated successful deviation from a recommendation is a defect report" | **KEEP verbatim** — this is a general principle and it fired again on 7 Aug (the 13-item hold challenge) |
| 15 | Judge close crafts by simulating, not discounting; phase order matters | KEEP directive; COMPRESS Aegisbound narrative |
| 16 | Run `audit` first, every time | KEEP — one line. Partially enforced (`brief` orders it first). |
| 17 | `potential` plans to T1; `--cap 3` reproduces old numbers | MOVE→ `docs/crafting.md` — it is a tool behaviour note |
| 18 | Reusable `ihlib` primitives list | MOVE→ `ihlib` docstrings, where they cannot drift from the code |
| 19 | Candidate judgements use post-craft ceilings | KEEP |
| 20 | The ~5-point discount is retired | KEEP directive; numbers now read off `calibration` (fixed) |
| 21 | Never read a capture whole | **TRIPWIRE** — greppable but evadable (`read_text` + `json.loads`). Prose stays. |
| 22 | Lazy panels list | MOVE→ `docs/data-dictionary.md` |
| 23 | `data/incoming/` triage, legacy exports | MERGE→4 |
| 24 | Data files immutable once written | KEEP — one line |

## Section 4 — Never defer a known defect (445 w)

| # | claim | disposition |
|---|---|---|
| 25 | The rule itself | **KEEP VERBATIM** |
| 26 | Barrier-weight and Acc-weight incidents | **KEEP** — exception to the compress rule. The narrative *is* the enforcement; the section argues this itself ("the reasoning that produces this failure is always plausible"). |
| 27 | The four plausible-excuse phrases | **KEEP VERBATIM** — most re-read lines in the file |
| 28 | Fix-now / legitimate-deferral / PENDING_REFITS / A-B-never-blocks / outranks-everything | KEEP, lightly tightened |

**Net: this section does not shrink.** It is 8% of the file and has justified
itself four times.

## Section 5 — Code changes: review before session ends (271 w, added 7 Aug)

| # | claim | disposition |
|---|---|---|
| 29 | Run `/code-review` on significant code changes | KEEP — compress to 2 lines |
| 30 | "Every defect found by a human question or coincidence, never by re-reading" | **MERGE→46** — restated more sharply in the 7 Aug section |
| 31 | The 7 Aug examples (collision, ETA, `decompile_locked`) | MOVE→ `incidents.md` |
| 32 | Run on the diff; fix findings same session; report what was done | KEEP as 3 short bullets; the deferral clause MERGE→25 |
| 33 | Guidance on *when* the expensive workflow review is warranted | **ADD** — currently missing, and the run cost 1.5M tokens. Belongs here. |

## Section 6 — Git workflow (556 w, added 7 Aug)

| # | claim | disposition |
|---|---|---|
| 34 | Never commit to main; branch naming | KEEP, 1 line |
| 35 | Commit when coherent and green; not per file; "two ands = two commits" | KEEP, 1 line |
| 36 | Each commit stands alone, suite green at every commit | KEEP, 1 line |
| 37 | Rebase into a readable story | KEEP, 1 line |
| 38 | Message format + record how a defect was found | KEEP, 1 line |
| 39 | No `Co-Authored-By` trailer | **ENFORCE** — already is, via `.claude/settings.json`. Prose → pointer. |
| 40 | Run `make ci` before push; why `unittest` alone is insufficient | KEEP directive; the two-failure narrative → `incidents.md` |
| 41 | Suite is data-isolated; `IH_DATA_DIR`; set in two places and why | **MOVE→ `tests/__init__.py` docstring** — it is a fact about the test harness, and it already appears there. Keep one line in `CLAUDE.md`. |
| 42 | Poll CI after pushing; a failing job masks later ones | KEEP, compress to 2 lines |
| 43 | Open a PR with `gh`; body leads on decision-relevant changes | KEEP, 1 line |
| 44 | Do not merge without explicit go-ahead | **KEEP VERBATIM** — irreversible, outward-facing |
| 45 | `data/` git-ignored; check `git status` | MERGE→24 |

**Target: 556 → ~180 words.** Written in one sitting hours ago; the narrative
has not yet earned permanence.

## Section 7 — Two rules learned 7 August (309 w, added 7 Aug)

| # | claim | disposition |
|---|---|---|
| 46 | Every defect found by two things that should agree, disagreeing → build the second opinion deliberately | **KEEP** — compress the five examples to two |
| 47 | Rules govern any decision-bearing number, not just the game model | KEEP — compress examples to one |
| 48 | "The tests pass is a fact; verified is a claim" | **KEEP VERBATIM** |
| 49 | Prefer models that self-validate against game ground truth | **MERGE→60** — stated three times in the file (here, claim 18, claim 60) |

## Section 8 — Analysis rules (1,977 w — the main body of work)

| # | claim | disposition |
|---|---|---|
| 50 | Every recommendation resolves to a specific action + UI section | **KEEP VERBATIM** — most frequently applicable rule in the file |
| 51 | Progression first, measurement second | KEEP, compress |
| 52 | A decision-critical unknown is a blocker, not a caveat | KEEP; 28 Jul narrative → `incidents.md` |
| 53 | Currency stock-and-flow incomplete until the conversion graph is checked | KEEP — corollary of 52, keep both |
| 54 | Never recommend a spend without its denominator; measure before challenged; check recoverability; do not hedge an unsized risk | **KEEP** — violated again 7 Aug; narrative → `incidents.md` |
| 55 | Check whether anything has ever measured a quantity; archive holds natural experiments | KEEP directive; Corrupt/AtkSpd narratives → `incidents.md` (this is the single longest bullet, 214 w) |
| 56 | Models fitted on currently-owned state rot; prefer archive-wide fits | KEEP, compress |
| 57 | A/B keep rules gate on outcome and contamination, never mechanism | KEEP, compress |
| 58 | State the regime a model was fitted in; re-validate outside it | KEEP; three 27 Jul examples → `incidents.md` |
| 59 | Declare the cohort before computing from it | KEEP, compress |
| 60 | Prefer models that self-validate against game ground truth | KEEP here as the canonical statement (49, 18 merge in) |
| 61 | A log field's meaning is a hypothesis until shown to vary | KEEP — short and sharp already |
| 62 | Segment by the natural categorical before concluding from a pooled mean | KEEP |
| 63 | A scalar ranking cannot audit its own weights | KEEP |
| 64 | Audit before you model; add missed checks | MERGE→16 |
| 65 | Before an irreversible action, enumerate every field it *writes* | **KEEP** — irreversible-action rule, cheap to state |
| 66 | Check accessibility/gates; use display names not slugs | KEEP, compress |
| 67 | Hackcoin is the only scarce currency; price in hackcoin-equivalents | **KEEP** — but the rate, the balance and the contract-board mechanics MOVE→ `docs/mechanics.md`; the *rule* is one line |
| 68 | Newest export is source of truth | MERGE→2 |
| 69 | Separate verified facts, working models, unknowns; never invent mechanics | KEEP — 1 line |
| 70 | Evaluate as crafting bases, not item level; follow §10 contract | KEEP — 1 line |
| 71 | Long-streak loss diagnostic order | MOVE→ `docs/mechanics.md` — it is a method, not a rule |
| 72 | Fields to inspect in a combat log | MOVE→ `docs/data-dictionary.md` |
| 73 | Homelab throughput is a fixed pool; rank by points per slot-hour | KEEP directive (1 line + pointer); the 250-word incident → `incidents.md` |
| 74 | "In-game description text outranks inference from minified client code" | **KEEP VERBATIM** — general, hard-won, easy to forget |

## Section 9 — Empirical guardrails (251 w)

| # | claim | disposition |
|---|---|---|
| 75–80 | All six claims (Defense/regen/tempo, attack speed is mitigation, accuracy saturation falsified, Kernel trade, listed vs realised regen, sustain anchors) | **MOVE→ `docs/mechanics.md`** — this is domain knowledge, not instruction. Leave a one-line pointer. |

## Section 10 — Userscript safety (93 w)

| # | claim | disposition |
|---|---|---|
| 81 | The whole section | **KEEP VERBATIM — DO NOT TOUCH.** Non-negotiable, already the tightest section, and semantically unenforceable. |
| 82 | Bump `@version` on every change | **ENFORCE** — CI check: if the userscript changed in the diff, the version must have. Prose keeps the line anyway (cheap, and the check is about the diff, not the behaviour). |

## Section 11 — Maintenance conventions (63 w)

| # | claim | disposition |
|---|---|---|
| 83–86 | Append to decision log; move confirmed mechanics out of open-questions; current-state stays singular; lead with the decision and state confidence | KEEP — already 4 lines |

---

## Coverage check — every incident keeps an owner

The acceptance criterion. If a row has no owner in the new structure, the
consolidation dropped signal.

| incident | owned by |
|---|---|
| Barrier weight left unchanged (29 Jul) | 25/26 — verbatim |
| Acc weight asserted 1.0 for two days | 25/26 — verbatim |
| T3 tier cap never tested | 8, 58 |
| Zone transition cost, wrong 4.5× across zones | 58 |
| `hardware_plan` at the wrong budget scale | 58, 60 |
| "Attack speed → fights per hour" never measured | 55 |
| `Corrupt` fitted on n=1 | 55 |
| `pcd`/`ecd` documented backwards | 61 |
| Pooled net-drain hid three lethal enemy classes | 62 |
| Cohort selected with no date bound (29 Jul) | 59 |
| `locked_resources` post-condition field | 65 |
| Homelab slots misread for a week | 73, 74 |
| Hacking Simulator deferred on a credit misread | 52, 53, 67 |
| Ladder rot from decompiling a sidegrade | 56 |
| Affix display-name collision (7 Aug) | 46 |
| Homelab ETA two-panel drift (7 Aug) | 46 |
| `decompile_locked` unread for three weeks | 16/64 |
| 13-item hold list, no denominator (7 Aug) | 54, 47 |
| `KEEP_DEPTH_PER_SLOT` unregistered (7 Aug) | 10 (enforced) |
| CI red twice: ruff never run, test read live captures (7 Aug) | 40, 41 |
| Audit reporting a rule `locks` no longer used (7 Aug) | 46 |

**21 incidents, 21 owners, no orphans.**

## Projected result

| section | now | after |
|---|---:|---:|
| Header + source-of-truth | 30 | 30 |
| File map | 571 | ~220 |
| Working with the data | 997 | ~430 |
| Never defer a known defect | 445 | **445** |
| Code review | 271 | ~120 |
| Git workflow | 556 | ~180 |
| Two rules (7 Aug) | 309 | ~150 |
| Analysis rules | 1,977 | ~850 |
| Empirical guardrails | 251 | ~15 (pointer) |
| Userscript safety | 93 | **93** |
| Maintenance | 63 | 63 |
| **total** | **5,563** | **~2,600** |

Roughly **halved**, with the two non-negotiable sections untouched and every
incident still owned.

## Resolved — the three open questions

All three changed once measured rather than reasoned about.

1. **`docs/incidents.md` is an INDEX, not a store.** The narratives are
   already in `decision-log.md` (Barrier appears 73 times there, the ladder
   incident 16, the denominator incident 8). Moving them would have created a
   *third* copy — exactly the duplication that produced the three stale
   claims fixed at the top of this branch. It is a one-page table: failure
   mode, what it cost, the rule that owns it, indexed by kind because the log
   is indexed by date.
2. **Fix `--help`, then drop the list.** "Just use `--help`" would not have
   worked: only 7 of 20 subcommands had a `help=` string, so both sources
   documented nothing and one merely did it more visibly. All 20 now carry a
   description, `CliHelpTest` asserts it (a total check — it walks the real
   subparser registry), and the prose list is gone.
3. **The hackcoin *rate* moves; the *rule* stays.** That bullet was four
   things: a rule (stays), the rate (already in `assumptions()` — and the
   register's copy carries a "re-confirm before leaning on it" caveat the
   prose copy lacked, so the duplicate was strictly worse), the consequences
   (stay), and contract-board mechanics (already in `mechanics.md` §20). The
   instinct to protect it was pattern-matching on "important number" when the
   actual risk ran the other way.

## Outcome

| section | before | after |
|---|---:|---:|
| whole file | 5,563 w | **3,019 w** (−46%) |
| Never defer a known defect | 445 | 445 (untouched) |
| Userscript safety | 93 | 93 + 3 lines on why it cannot be tested |

Coverage verified mechanically: 19 load-bearing phrases still present in
`CLAUDE.md`, 5 relocated claims present in their destination and absent from
`CLAUDE.md` (no duplicates), 21 of 21 incidents owned. Three enforcement
checks now carry rules that were prose only — `AssumptionsRegistryTest`,
`CliHelpTest`, and the CI `@version` job — and the first of those immediately
found `DAMAGE_K` and the fitted hit law unregistered since 29 Jul.
