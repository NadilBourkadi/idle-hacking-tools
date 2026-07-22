# Idle Hacking — Crafting Mechanics and Decision Protocol

**Consolidated:** 21 July 2026  
**Purpose:** Self-contained reference for evaluating uncrafted inventory items and issuing exact craft instructions without needing another external lookup.

## 1. Decision objective

A candidate export is primarily a set of **crafting bases**. The correct question is not “is this better if equipped now?” but:

> Can this item's fixed structure and finite Stability budget be converted into a better whole-loadout contribution than the current item?

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

## 11. Current unresolved mechanics

These remain unknown and must not silently become facts:

- exact Snapshot Backup trigger chance at the player's current Homelab level;
- whether a successful Version Upgrade preserves relative roll position or rolls a new value in the new tier;
- exact current Bias Reroll selection semantics and number of affected affixes;
- whether Compile multiplies the implicit affix as well as explicit non-signature affixes;
- exact resource-cost scaling formula by item level;
- complete slot-specific affix pool and tier-weight distribution;
- Augment's tier distribution.

A fresh before/after export can resolve the first three operationally.
