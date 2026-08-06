# Idle Hacking — Crafting Mechanics and Decision Protocol

**Consolidated:** 21 July 2026  
**Purpose:** Self-contained reference for evaluating uncrafted inventory items and issuing exact craft instructions without needing another external lookup.

## 1. Decision objective

A candidate export is primarily a set of **crafting bases**. The correct question is not “is this better if equipped now?” but:

> Can this item's fixed structure and finite Stability budget be converted into a better whole-loadout contribution than the current item?

`ih.py potential` mechanizes the first pass of this: it projects each candidate's realistic post-craft package from empirical tier ladders (per-tier normalized affix values measured across the whole inventory; interpolated tiers marked `~`) under a greedy Version-Upgrade plan (tier depth limited only by the Stability budget, Compile floor, one Stability reserved when an Augment slot is open). Its score weights (`ihlib.CRAFT_WEIGHTS_*`) encode the current bottleneck model and are a planning heuristic, not a game formula. Use it for ranking; use this document's §10 contract before actually spending.

Evaluate in this order:

1. Which bottleneck must the item solve?
2. Is the implicit useful?
3. Are the existing affix families useful?
4. Which side will Augment fill?
5. How much Stability is needed to reach minimum useful tiers?
6. What Compile bonus remains after a realistic failure budget?
7. What outcome ends the craft?

## 2. Item and affix structure

### Verified

- Normal items can have at most **3 prefixes and 3 suffixes**.
- Observed Rare items normally have five explicit affixes; observed Epic items normally have six.
- T1 is strongest and T9 weakest.
- Tier determines the value range. The bracket shown in the crafting panel is the current tier's possible range.
- Prefixes normally combine an economy/progression component with a basic stat. Special prefixes can instead be pure Drop Boost or Item Rarity.
- Suffixes are combat-focused.
- Epic Signature affixes are extra special effects. They cannot be removed, rerolled or changed, and Compile does not multiply them.

### Augment side

Augment fills one remaining explicit-affix slot:

- `3P / 2S` → forced suffix.
- `2P / 3S` → forced prefix.
- A full `3P / 3S` item cannot gain a normal seventh affix unless a special effect such as Stable Construction expands capacity.

The forced side is strategically important. A 2P/3S Firewall cannot Augment another regeneration suffix; it can only gain a prefix basic stat.

## 3. Stability and Compile

- Items drop with 25-30 Stability.
- Most crafting actions spend 1 Stability.
- At 0 Stability, normal crafting is unavailable; Unlock remains available.
- Compile consumes all remaining Stability and is permanent.
- Compile bonus is:

```text
Compile bonus = 0.5% × remaining Stability
```

- Compile multiplies non-signature affix values.
- Every Stability-spending action therefore sacrifices **0.5 percentage points** of possible Compile.

### Default budget rule (rewritten 28 July 2026 — the old rule was costing ~11-13 score points per craft)

For a serious main-set craft:

- hard floor: **2 Stability** remaining (`ihlib.COMPILE_FLOOR`) → +1% Compile;
- spend everything above the floor on tier depth;
- the floor exists only to keep one Refactor/retry in hand (§10.1 phase 7), not because Compile is worth reserving for.

Compile is always the final crafting action.

**Why the floor moved 8 → 2.** Compile pays 0.5% per preserved point spread across *all* affixes; one deeper Version-Upgrade step multiplies *one* affix by 1.26-1.40×. Because affix value is concentrated in one or two lines, the tier step wins almost always. `simulate_contract` swept floors 0/2/4/6/8/10 over three live candidates on 28 July: **lower was better on mean, median, p10 and p90 in every case**, with the worst case flat.

| candidate | floor 8 mean | floor 0 mean |
|---|---|---|
| Assault Kernel of Corruption | +14.9 | **+26.3** |
| Titanic Firewall of Sandboxing | +15.5 | **+28.3** |
| Untouchable Payload of Lightning | +11.0 | **+19.0** |

Confirmed live the same evening. The Resilient Firewall of Perpetuity contract was written to floor 8 (projected mean +15.1, p90 +18.9); the player crossed the floor and ran to 1 Stability, reaching T1/T1/T3/T5 instead of the planned T3/T1/T6/T7, and the item realized **+44.6** — more than double the floor-8 p90. Compile's resource price also *falls* with a lower floor (this item's Compile cost 49,999 at 1 Stability vs 1,249,951 at 25).

**Standing lesson.** `floor=8` was never measured — it was a plausible default written once and then inherited by `plan_craft`, `simulate_contract`, `ih.py potential` and every craft verdict for six days. It suppressed every ceiling by more than `UPGRADE_BAND` itself, which means candidates rejected as sidegrades before 28 July were re-ranked, not merely re-scored. Same failure shape as the T3 tier cap and the "attack speed → fights/hour" assertion: **a default nobody ever exercised at both ends of its range.**

## 4. Version Upgrade

Version Upgrade attempts to improve one selected affix by one tier. The current export showed the same chance for every affix at a given tier.

| Current tier | Target tier | Success chance | Expected attempts* |
|---:|---:|---:|---:|
| T9 | T8 | 90% | 1.11 |
| T8 | T7 | 80% | 1.25 |
| T7 | T6 | 70% | 1.43 |
| T6 | T5 | 60% | 1.67 |
| T5 | T4 | 50% | 2.00 |
| T4 | T3 | 40% | 2.50 |
| T3 | T2 | 30% | 3.33 |
| T2 | T1 | 20% | 5.00 |
| T1 | — | 0% | unavailable |

\*Geometric expectation assuming independent attempts and ignoring Snapshot Backup.

Equivalent pattern:

```text
P(success from Tn to T(n-1)) = 10 × n percent, for n = 2..9
```

### Failure behaviour

- A failed attempt does not improve the tier.
- Resources are consumed on failure.
- Normally 1 Stability is also consumed.
- The Homelab **Snapshot Backup** upgrade can sometimes prevent Stability loss on a failed attempt.
- Snapshot Backups is +5%/level, max 5. **Never state its level here — read it from the capture** (`ihlib.stability_preserve_chance`; level 2 = 10% preserve as of 27 July 2026). This line previously asserted "level 0", which was true on 22 July and silently rotted for five days, leaving every Stability budget ~6% over-conservative (`open-questions.md` §16).
- Because a preserved failure costs an attempt but no Stability, **attempts and Stability diverge above level 0**; `plan_craft` budgets in Stability and reports both.

### Useful cumulative budgets

| Path | Expected Stability | Practical capped budget | Chance within cap* |
|---|---:|---:|---:|
| T7 → T4 | 5.10 | 8 | 94.0% |
| T7 → T3 | 7.60 | 10 | 86.3% |
| T6 → T4 | 3.67 | 5 | 86.4% |
| T9 → T5 | 5.46 | 6 | 80.1% |

\*Independent-attempt calculation; Snapshot Backup improves effective Stability retention but not resource cost.

Do not automatically chase T2/T1. The last steps are deliberately expensive in Stability expectation.

## 5. Refactor

Refactor rerolls the selected affix's numerical values **within its current tier**.

- It does not change the affix family.
- It does not improve tier.
- It costs the slot's secondary resource and 1 Stability.
- It can roll worse.

Use the captured range to calculate roll position:

```text
roll position = (current - minimum) / (maximum - minimum)
```

Guideline:

- 0-20%: poor; consider one Refactor after tier work.
- 20-40%: below average; only Refactor if the line is important and Stability is plentiful.
- 40-80%: keep.
- 80-100%: do not Refactor.

Always perform Version Upgrades first because a tier change supersedes the value range you were optimizing.

## 6. Augment

Augment adds the missing random prefix or suffix and normally costs 1 Stability.

The current 0.6.1 UI snapshots showed **primary resource plus Credits** for Augment, while the static help text only listed the primary resource. Use the current crafting snapshot as the cost source of truth.

### Required response for every Augment project

State three result classes before the user clicks:

1. **Continue:** the affix directly solves the identified bottleneck.
2. **Conditional:** usable only at a sufficiently strong starting tier or with spare Stability.
3. **Abort:** the new line cannot justify the Stability and resource budget.

After Augment, capture a fresh crafting snapshot before any other operation.

## 7. Lock, Prune and Bias Reroll

### Lock

- Only one affix can be crafting-locked at a time.
- Lock costs `lock_cost` Credits and **one Stabilizer**.
- Unlock refunds the lock's Credits and Stabilizer.
- Lock is mainly relevant to random removal/reroll operations, not targeted Version Upgrade or Refactor.
- **Stabilizers come from decompiling** (`stabilizers_gained`; the 27 July mass-decompile of 43 items yielded +7) and **nothing else consumes them**, so the balance is simply a count of remaining Locks — 94 as of 27 July 2026.

### Prune

Prune removes one random unlocked affix and spends 1 Stability.

The odds of removing one specific bad affix are:

```text
1 / number of unlocked affixes
```

Examples:

- Six-affix item, one line locked → five unlocked → 20% chance.
- Five-affix item, one line locked → four unlocked → 25% chance.

Therefore, random Prune is not a routine repair tool. Use it only when several unlocked outcomes are acceptable or the item has otherwise exceptional value.

### Bias Reroll

- Bias Reroll uses a selected essence category to guarantee the orientation, not an exact affix.
- Categories shown by the current UI: Optimization, Prosperity, Expertise, Precision, Damage, Survival, Retribution and Dexterity.
- Cost is `bias_primary_cost` + `bias_credit_cost` + **`bias_essence_cost` = 5 × (affix count − 1)**: 20 on a 5-affix item, 25 on a 6-affix item, measured across all 17 items in the 27 July 2026 capture. The flat "20 Essence" in earlier 0.6.1 notes was a 5-affix observation, not a constant. Older guide text showing one Essence is stale.
- The client sends only `BIAS_REROLL {item_id, essence}` — the essence → affix-category mapping is resolved server-side and is **not** present in the client JS, so it cannot be decoded statically (open-questions §3).
- Prune and Bias Reroll consume the active affix lock on success; auto-relock can restore it if resources are available.
- The exact number/selection of affixes changed by the current Bias Reroll implementation has not yet been captured in a before/after test. Do not prescribe it as a deterministic repair operation until that test exists.

For the player's current attrition bottleneck, Survival is the relevant bias; Precision is secondary for high-evasion/Mirrored targets.

### UI button names vs `crafting_preview` keys (decoded 27 July 2026)

Two operations are stored under names that do not match their buttons, so the
cost fields were easy to mis-read. From `vendor/game-js/inventory.js`:

| UI button | WebSocket message | Cost key(s) |
|---|---|---|
| LOCK AFFIX | `EQUIPMENT_LOCK` | `lock_cost` Credits **+ 1 Stabilizer** |
| **PRUNE** | **`EQUIPMENT_ANNUL`** | **`annul_cost`** |
| **REFACTOR** | **`EQUIPMENT_MASTERWORK`** | **`masterwork_cost`** |
| AUGMENT | `EQUIPMENT_AUGMENT` | `augment_cost` + `augment_credit_cost` |
| Version Upgrade | `EQUIPMENT_TIER_PROMOTE` | `tier_promotion_primary/secondary_cost` |
| Bias Reroll | `BIAS_REROLL` | `bias_primary/credit/essence_cost` |

The REFACTOR button is **disabled when every effect on the affix already sits at
`value_max`** — independent confirmation that Refactor rerolls within the current
tier and cannot improve a maxed roll (§5). `ih.py item` prints all of these.

## 8. Slot resource mapping

| Slot | Primary | Secondary |
|---|---|---|
| Payload | Snippets | Cycles |
| Firewall | Hashes | Packets |
| Analyzer | Packets | Cycles |
| Shell | Hashes | Snippets |
| Driver | Cycles | Snippets |
| Router | Packets | Hashes |
| Daemon | Cycles | Packets |
| Kernel | Snippets | Hashes |

Version Upgrade uses both resources. Refactor and Prune use the secondary resource. Compile uses the primary resource. Current UI snapshots override static help when a displayed cost differs.

## 9. Crafting operation order

Default sequence:

1. Inventory-lock the candidate against accidental decompile.
2. Confirm the bottleneck and minimum acceptable final package.
3. Augment first when the missing slot matters.
4. Export immediately and apply the declared Continue/Conditional/Abort rule.
5. Version Upgrade build-defining affixes using explicit attempt caps.
6. Upgrade supporting affixes only while preserving the Compile floor.
7. Export again; inspect new tier ranges and current roll positions.
8. Refactor only important bottom-quartile rolls, one attempt at a time.
9. Avoid Prune/Bias Reroll unless their risk is explicitly justified.
10. Compile last.
11. Export the finished item and run comparable combat/streak tests before replacing the current item permanently.

## 10. Candidate evaluation output contract

Every future recommendation should include:

- current item and candidate structure;
- forced Augment side;
- intended role and bottleneck;
- Augment Continue / Conditional / Abort list;
- ordered affix targets;
- target tier for each affix;
- maximum attempts for each phase;
- minimum Stability before starting an optional phase;
- final Compile floor;
- expected resource classes and current displayed costs;
- post-craft test plan.

### 10.1 Standard craft contract template (locked 22 July 2026)

Every approved craft recommendation is delivered as an explicit contract with exactly these sections — high-level suggestions are not deliverables. All displayed costs come from the item's current `crafting_preview`; the in-game panel wins on any mismatch.

0. **Header & evidence** — item, slot, ilvl, Stability; ceiling verdict (score Δ must exceed `UPGRADE_BAND`); 2–3 sentences tying the craft to the current bottleneck with measured numbers; key trade vs equipped including the economy delta.
1. **Shopping list** — worst-case resource totals (all caps hit + Compile), in units and credit-equivalents; marketplace purchases required before starting.
2. **Pre-flight** — decompile-lock the base; confirm current capture matches the plan; equipped item stays equipped throughout.
3. **Version-Upgrade phases, numbered, in execution order.** Each phase states: the affix (display name, stat, current tier/value/roll), target tier, per-attempt cost, per-step success chances, expected attempts, and a **hard attempt cap**. On-cap rule (amended 22 July after the Payload Phase-1 cap-out): **never chase the capped line further; recapture and re-plan the remaining budget** against the verdict bands — other planned phases may still run if they independently justify their Stability. Auto-compiling on first cap-out abandons value; chasing the capped line is the sunk-cost trap. Re-declare the expected final verdict (UPGRADE/sidegrade) after every re-plan so expectations track reality.
4. **Conditional phases** — explicit Stability gates ("only if Stability ≥ N").
5. **Augment phase** (only if a slot is open; run first for cost reasons) — forced side, cost, pre-declared Continue/Conditional/Abort outcome classes. Recapture immediately after.
6. **Do-not-touch list** — affixes already at target with rolls ≥80%; and never Refactor an affix whose *other* effect rolls ≥60% (Refactor rerolls **all** effects of the affix — learned on of Rending, 22 July).
7. **Refactor pass** — qualifying lines (roll <20% after VU work), maximum count, minimum Stability (floor + 1).
8. **Compile** — floor **2**, preferred finish 2–6 remaining; always the final action. (Was "floor 8, preferred finish 8–12" from 22 July until **28 July 2026**, when a sweep over 0/2/4/6/8/10 on three live candidates showed a lower floor better on mean, median, p10 **and** p90 in every case; 2 rather than 0 keeps one Refactor in hand. Any contract written before that date reserved ~6 Stability too many.)
9. **Recapture checkpoints** — after Augment, after each phase group, after Compile.
10. **Post-craft test** — equip rule, number of streaks, metrics vs recorded baseline (death streak, rounds/fight at high streak, start-HP at death), explicit keep/revert criterion, decision-log entry.

## 11. Cost model (resolved 22 July 2026)

The full cost structure was decoded from the full-state capture — base-cost formula, exact 1.03^spent Credit-cost escalation, per-operation multiples and the Compile cost. See `static-analysis-2026-07-22.md` §2. Headline strategic additions to the rules above:

- **Attempts and Stability are different quantities.** Homelab **Snapshot Backups** grants `tier_promotion_stability_preserve` 5%/level (level 2 = 10% as of 27 July 2026, max 5 = 25%): a *failed* Version Upgrade then has that chance to cost no Stability. Expected Stability for one promotion is `1 + ((1-p)/p) × (1-preserve)`, not `1/p`. Budget in Stability (`ihlib.version_upgrade_expected_stability`), state contract attempt caps in attempts (`version_upgrade_expected_attempts`) — the player counts clicks at the panel. At 10% preserve a T7→T1 chase costs 14.9 Stability rather than 15.9 (−6.2%), and the saving grows with depth because deeper steps fail more often. **Read the level from the capture** via `ihlib.stability_preserve_chance`; it silently went 0 → 2 between 22 and 27 July while the cost model assumed 0 throughout.
- Stability spending compounds future Credit costs (Augment/Lock/Bias) at 3%/point — Augment early is also Augment cheap. (Confirmed live 22 July: after 1 Stability spent, augment credit cost rose exactly ×1.03; Version Upgrade resource cost unchanged; Compile cost fell.)
- Compile's resource price rises 0.18× base_cost per preserved Stability point; the +4-6% Compile floor remains correct, but very high floors carry a real resource price.
- **Marketplace closes the resource loop:** basic crafting resources are purchasable at ~2 credits/unit (22 July 2026 quote: 5M Cycles = 10.2M credits). Budget crafts in credit-equivalents; never delay a justified craft to gather resources while credits are abundant.

## 12. Current unresolved mechanics

These remain unknown and must not silently become facts:

- exact Snapshot Backup trigger chance at the player's current Homelab level;
- whether a successful Version Upgrade preserves relative roll position or rolls a new value in the new tier;
- exact current Bias Reroll selection semantics and number of affected affixes;
- whether Compile multiplies the implicit affix as well as explicit non-signature affixes;
- affix tier-weight distribution and unowned parts of the affix pool (observed pool: `affix-pool.md`);
- Augment's tier distribution.

A fresh before/after export can resolve the first three operationally.

### 12.1 Tier ladder growth is family-specific — 27 July 2026

How much an affix gains per tier is **not one constant**, and the single 1.4 the toolkit used was fitted on shallow tiers only. Measured within-family across every percentage affix in the 27 July capture:

| Region | n | median | p25 | p75 |
|---|---:|---:|---:|---:|
| upper tier ≥ 6 | 50 | **1.398** | 1.341 | 1.415 |
| upper tier ≤ 5 | 25 | **1.263** | 1.250 | 1.288 |

Deep steps are also far more **family-dependent** than shallow ones — `suffix_attack` decelerates hard (1.232 → 1.171 → 1.146 approaching T1) while `suffix_adaptive_shell` and `suffix_regeneration` hold ~1.41 all the way down. So the spread on an *unmeasured* family's deep ladder is roughly 1.15–1.42, which over a five-tier chase is a 2.7× spread in the final affix value.

Consequences, all now in tooling:

- `ihlib.ladder_value` walks a region-aware step when it extrapolates; log-linear interpolation is kept only *between* observations, where it is bounded by data.
- `ihlib.fit_tier_steps(capture)` re-fits both constants from the capture, so the law cannot rot as the inventory turns over.
- `plan_craft` returns `score_low` (the same plan re-valued at the p25 deep step) and `deep_reliance` (planned promotions into tiers that family has never been observed at). **A verdict that only clears `UPGRADE_BAND` at the median is resting on extrapolation, not evidence.**
- The 27 July uncapping argument — that reliance on interpolated points was "unchanged at 43/50" — counted interpolated points without checking their **bias**, which was the whole problem. Uncapping to T1 remains right; it just has to be priced on the correct ladder.

**The cheapest way to resolve a family is to buy one tier of it.** `value_min`/`value_max` in the capture are the tier's full range, so a *single successful* Version Upgrade reveals the next tier's exact midpoint — a deterministic measurement, not a noisy sample.

### 12.1.1 Ladder amnesia — decompiling used to delete the evidence

`tier_ladders(capture)` read one capture, so a tier was "observed" only while an owned item still carried it. **Decompiling therefore silently degraded craft verdicts**, and did:

- 27 Jul 19:54Z → 20:57Z, three sidegrades were decompiled. One of them, `Elusive Kernel of Regeneration` (+1.7), held `of Regeneration` **T7 — the only `suffix_adaptive_shell` T7 observation owned.**
- That is the family the Bastioned Firewall of Infection's whole plan runs through. With T7 present the greedy planned `of Recovery` T8→T1 inside measured data and scored **+9.0**; without it the T4–T7 region became interpolated, the greedy flipped to a shallower `of the Bastion` T5→T2 plan, and the same item on the same build scored **+4.6**.
- **No game state changed at all** — not the item, not its Stability, not the loadout, not hardware. A 4.4-point verdict swing, comparable to the entire `UPGRADE_BAND`, came purely from the model forgetting.

An affix's per-tier range is a game constant, so an observation stays valid after the item is gone. `ihlib.tier_ladders_archive()` unions every capture in `data/captures/` and is what `ih.py potential` now uses: **150 → 582 tier observations, 83 → 97 affix families**, and the ladder can only improve from here. `fit_tier_steps` takes the same archive ladders. Regime caveat: this is sound only while the game does not rebalance affix ranges — if it ever does, pre-change captures become contaminating and the fit must be re-based from the boundary.

This is the same failure shape as the T3 tier cap and the zone transition cost: **a model quietly used outside the regime it was fitted in.** The new twist is that the regime moved on its own — nobody changed the model, the data under it was thrown away by a routine inventory action.

### 12.2 Roll position is lost on promotion — plan around it

`plan_craft` values an upgraded affix at the new tier's **midpoint**. When the current roll is high, one promotion can therefore be worth much less than the ladder step suggests, and adjacent tier ranges overlap: the Aegisbound Driver's `of Execution` sits at 99% of the T6 range (0.1667 of 0.1231–0.1670), while a bottom-of-range T5 roll would land near 0.156 — **a downgrade**. This does not bias a *ceiling* comparison (which compares final-tier midpoint against the equipped item's actual values), but it does bias the marginal "is this one step worth the Stability" question. Check the roll before spending on a single step.

## 13. Realized-craft calibration — 22 July 2026 (Vital Driver)

First contract executed end-to-end. Lessons, all encoded in tooling where possible:

- **Verdict bands:** projected +3.9 realized as −2. Ceiling deltas within ±5 heuristic score of the equipped item are **sidegrades**; demand > +5 before calling a candidate an upgrade (`ihlib.UPGRADE_BAND`; `ih.py potential` now prints the verdict).
- **Projection ≠ contract:** the projection assumed the tool's greedy plan; the safer contract (capping of Haste at T5) cost ~5 score. Either align the contract with the tool plan or mentally discount projections by the contract's conservatism.
- **Economy lines are strategic, not cosmetic:** credits fund the Homelab track and global XP feeds `heal_base = 5 × level`. `potential` now prints the economy delta vs equipped. The Warmongering Driver's +13.4% credits / +13.4% global XP was silently load-bearing.
- **Corruption is outgoing DoT** worth ~1% of output per point in long fights (measured: 15.6% of output from 12 points, streak-96 death fight). Weight raised 0.08 → 0.6.
- **Affix display names change with tier** (of Precision→of the Hawk at T3). Track crafted items by id / `ih.py history`, never by name.
- **Whole-loadout function first:** a candidate that dumps the equipped item's densest line (AtkDmg+Corrupt here) starts deep in the hole regardless of its own gains — same lesson as the Kernel guardrail, now confirmed on an offensive slot.

## 14. Contract-execution lessons — 23 July 2026 (Phoenix Shell craft + A/B)

Third contract executed end-to-end; first to realize **above** projection (+22.6 vs +20.2). New rules, amending §10.1:

- **Identify affixes by visible stat lines, never by display name alone.** The Shell carried two suffixes both displayed as "of Recovery"; the contract said "the regeneration line" but the player promoted the other one (the Def+Regen dual — favourable, by luck). Names collide *and* change with tier. Contracts must reference each affix as e.g. "the suffix showing only `Regen +5`" vs "the suffix showing `Def % + Regen`", and quote its current values.
- **Define post-craft test metrics at field level, verified against the data dictionary, before equipping.** The original keep rule said "damage taken/fight ≤ +5%" — but `damage_taken` is gross intake (see data-dictionary), which *must* rise under a mitigation→recovery trade and silently over-credits any barrier-carrying baseline. The clause was amended pre-outcome at 4/10 deaths to net drain (gross − in-fight `prg` − barrier absorption). General form: **when a craft trades across stat categories, the test metric must be the net quantity the trade affects**, not a component the trade is guaranteed to move.
- **Plan for equip-on-compile.** The contract scheduled a post-VLAN baseline before equipping; the player equipped within minutes of compiling. The passive combat-stream baseline (14 payload-era deaths already banked) is what made the test valid anyway. Baselines must come from the always-on ledger, with `segment_ms` boundaries pre-declared for known upcoming stat events — never from a promised future waiting period.
- **Audit accounting identities at the first interim readout, not at verdict time.** The gross-vs-net problem was caught at 4/10 because the interim pass included a `damage_taken − regen − HP-drop` closure check. Make that check standard for any test whose keep rule references a damage or sustain field.

### Realized-vs-projected ledger (all contract crafts)

| Craft | Projected Δ | Realized Δ | Note |
|---|---|---|---|
| Vital Driver (22 Jul) | +3.9 | −2.0 | source of the ±5 verdict band |
| Storm Daemon (22 Jul) | +8.0 | ~+9 | first surviving UPGRADE |
| Targeted Payload (22 Jul) | +6.9 | +1.7 | Phase-1 cap-out; on-cap replan rule |
| Bastioned Payload (23 Jul) | +30.2 (post-Augment) | ~+10 realized score, A/B KEEP | unlucky VU run (13 fails) |
| Phoenix Shell (23 Jul) | +20.2 (post-Augment) | +22.6, A/B KEEP | lucky VU run (17 attempts / 12 promotions vs ~22 expected) |
| Targeted Analyzer (27 Jul) | +13.5 (post-Augment) | **+24.9** | best on record; all three suffix targets overshot T3 to **T2** on 19 VU attempts for 12 promotions vs ~28 expected |
| Titanic Router (27 Jul) | +22.8 (uncapped planner) | **+38.7** | new best; first craft planned under the uncapped planner. `of Regeneration` completed the full T7→T1 chase (Regen +92 [79%]) and `of Alacrity` overshot T6→**T3** (AtkSpd +17.47%). 12 promotions on ~20 attempts vs ~25.8 expected |

Spread vs projection had two sources pulling opposite ways: roll luck (±5–10, symmetric) and the planner's old T3 cap (one-directional, always understating). **The cap was removed 27 July 2026**; every row above was computed under it and its projected-Δ column is not comparable to future ones.

Re-running both over-realizing crafts against their pre-craft captures separates the two causes, and they turn out to be different:

| Craft | capped projection | uncapped projection | realized |
|---|---|---|---|
| Phoenix Shell (23 Jul) | 61.5 | **69.8** | 63.8 |
| Targeted Analyzer (27 Jul) | 65.8 | **65.8** | 77.3 |

The Shell was a genuine cap artifact — uncapped projection minus the ~5-point contract discount is 64.8 against 63.8 realized, near-exact. The Analyzer was **not**: its Stability budget was binding either way, so the cap cost nothing there and the whole +11.4 was roll luck (12 promotions in 19 attempts against ~28 expected). The general shape: **the cap never reduced the budget, it constrained how the budget was allocated** — neutral when the budget binds early, expensive when the greedy would rather go deep on one line than broad across three (Titanic Router of Regeneration, +8.3 capped vs +22.8 uncapped on the same ~19.7 Stability).

With the cap gone the remaining bias points one way: a §10.1 contract, with attempt caps and a hard Compile floor, is deliberately less ambitious than the planner's optimal plan. **The ~5-point contract-conservatism discount therefore matters more now, not less** — the cap had been partly cancelling it. Re-derive the discount and `UPGRADE_BAND` after the next two or three crafts. Verdicts near the band remain coin flips — reserve craft spend for double-band margins (the two ~+20 projections both delivered).
