# Idle Hacking — Crafting Mechanics and Decision Protocol

**Consolidated:** 21 July 2026  
**Purpose:** Self-contained reference for evaluating uncrafted inventory items and issuing exact craft instructions without needing another external lookup.

## 1. Decision objective

A candidate export is primarily a set of **crafting bases**. The correct question is not “is this better if equipped now?” but:

> Can this item's fixed structure and finite Stability budget be converted into a better whole-loadout contribution than the current item?

`ih.py potential` mechanizes the first pass of this: it projects each candidate's realistic post-craft package from empirical tier ladders (per-tier normalized affix values measured across the whole inventory; interpolated tiers marked `~`) under a greedy Version-Upgrade plan (T3 cap, Compile floor, one Stability reserved when an Augment slot is open). Its score weights (`ihlib.CRAFT_WEIGHTS_*`) encode the current bottleneck model and are a planning heuristic, not a game formula. Use it for ranking; use this document's §10 contract before actually spending.

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

### Default budget rule

For a serious main-set craft:

- hard floor: **8 Stability** remaining → +4% Compile;
- preferred finish: **8-12 Stability** → +4% to +6%;
- only cross the floor when a clearly build-defining affix is one successful step away and the chance is at least 40%.

Compile is always the final crafting action.

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
- The player's current Snapshot Backup level/chance is not captured, so planning uses the conservative no-backup budget.

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
- Lock costs Credits and one Stabilizer.
- Unlock refunds the lock's Credits and Stabilizer.
- Lock is mainly relevant to random removal/reroll operations, not targeted Version Upgrade or Refactor.

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
- Current 0.6.1 snapshots showed primary resource + Credits + **20 Essence**. Older guide text showing one Essence is stale.
- Prune and Bias Reroll consume the active affix lock on success; auto-relock can restore it if resources are available.
- The exact number/selection of affixes changed by the current Bias Reroll implementation has not yet been captured in a before/after test. Do not prescribe it as a deterministic repair operation until that test exists.

For the player's current attrition bottleneck, Survival is the relevant bias; Precision is secondary for high-evasion/Mirrored targets.

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
8. **Compile** — floor 8, preferred finish 8–12 remaining; always the final action.
9. **Recapture checkpoints** — after Augment, after each phase group, after Compile.
10. **Post-craft test** — equip rule, number of streaks, metrics vs recorded baseline (death streak, rounds/fight at high streak, start-HP at death), explicit keep/revert criterion, decision-log entry.

## 11. Cost model (resolved 22 July 2026)

The full cost structure was decoded from the full-state capture — base-cost formula, exact 1.03^spent Credit-cost escalation, per-operation multiples and the Compile cost. See `static-analysis-2026-07-22.md` §2. Headline strategic additions to the rules above:

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

## 13. Realized-craft calibration — 22 July 2026 (Vital Driver)

First contract executed end-to-end. Lessons, all encoded in tooling where possible:

- **Verdict bands:** projected +3.9 realized as −2. Ceiling deltas within ±5 heuristic score of the equipped item are **sidegrades**; demand > +5 before calling a candidate an upgrade (`ihlib.UPGRADE_BAND`; `ih.py potential` now prints the verdict).
- **Projection ≠ contract:** the projection assumed the tool's greedy plan; the safer contract (capping of Haste at T5) cost ~5 score. Either align the contract with the tool plan or mentally discount projections by the contract's conservatism.
- **Economy lines are strategic, not cosmetic:** credits fund the Homelab track and global XP feeds `heal_base = 5 × level`. `potential` now prints the economy delta vs equipped. The Warmongering Driver's +13.4% credits / +13.4% global XP was silently load-bearing.
- **Corruption is outgoing DoT** worth ~1% of output per point in long fights (measured: 15.6% of output from 12 points, streak-96 death fight). Weight raised 0.08 → 0.6.
- **Affix display names change with tier** (of Precision→of the Hawk at T3). Track crafted items by id / `ih.py history`, never by name.
- **Whole-loadout function first:** a candidate that dumps the equipped item's densest line (AtkDmg+Corrupt here) starts deep in the hole regardless of its own gains — same lesson as the Kernel guardrail, now confirmed on an offensive slot.
