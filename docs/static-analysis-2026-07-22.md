# Static Export Analysis — 22 July 2026

Findings mined from `data/loadouts/full-state-2026-07-22.json` (78 items, 415 affix instances). All fits are against this single snapshot; confidence noted per finding. Analysis scripts were one-off (rerun against future captures to re-verify).

## 1. Affix value scaling by item level — near-exact fit

Every affix effect carries `base_value` (reference magnitude) and `value` (actual). For percentage (`mult_add`) effects:

```text
value = base_value × ((item_level + 125) / 1125) ^ 0.391        R² = 0.99992
```

`base_value` is the affix magnitude normalized to **item level 1000**. Flat (`flat_add`) effects follow the same shape with a larger exponent (~0.785, R² 0.81 — integer rounding makes the fit noisier; suggestively ≈ 2 × 0.391).

Practical consequences:

- The same affix/tier/roll is materially stronger on higher-level items: ilvl 314 ≈ 69% of nominal, ilvl 1000 = 100%, ilvl 1311 ≈ 110%.
- Brutal Firewall of Perpetuity's celebrated package is achieved at a ~31% item-level malus — a same-tier replacement at ilvl 1100+ would exceed it by ~50% per identical roll. This sharpens the Firewall upgrade case considerably.
- Flat regeneration scales *more* steeply with item level than percentage stats — old low-ilvl regen items lose more than their percentage stats suggest.

## 2. Crafting cost model — exact and near-exact components

From `crafting_preview` (per-item, all 78 consistent):

- **Base cost:** `base_cost ≈ 1.586 × required_hack_level ^ 1.765` (R² 0.995). Cost is driven by required level, not item level.
- **Stability escalation:** `stability_multiplier = 1.03 ^ stability_spent` — **exact**. Each Stability spent compounds a 3% cost escalation.
- **Escalation applies to Credit costs only.** Primary/secondary resource costs are fixed multiples of the *raw* base cost:

| Operation (client key) | UI name (inferred) | Resource cost | Credit cost |
|---|---|---|---|
| `tier_promotion` | Version Upgrade | 1× base (primary) + 0.5× base (secondary) | — |
| `masterwork` | Refactor | 1× base | — |
| `annul` | Prune | 1× base | — |
| `augment` | Augment | 5× base | 10× escalated base |
| `bias` | Bias Reroll | 0.5× base | 1× escalated base (+20 Essence flat) |
| `lock` | Lock | — | 2× escalated base |
| `compile` | Compile | **0.18 × remaining Stability × base** | — |

UI-name mapping is inferred from client function signatures (`craftingAnnul(item)` = untargeted removal → Prune; `craftingMasterwork(item, affix, …)` = targeted → Refactor); verify once against the live UI.

Strategic consequences:

- Spending Stability inflates future **Credit** prices (Augment/Lock/Bias) by 3%/point compounding, on top of the known 0.5%/point Compile forfeit. Augment-first ordering (already doctrine) is now also cheapest.
- Compile's resource price *rises* with the Stability you preserved (0.18×/point) — a modest countervailing cost to very high Compile floors; at base_cost ≈ 100k, each preserved point adds ~18k primary resource to the final Compile.

## 3. Version Upgrade chances — confirmed at scale

`tier_promotion_chance = tier × 10%` (T1 = 0) across all 415 affix instances, uniform for every affix family. Hardens the schema-4 finding (was 165 crafting-panel controls).

## 4. Observed affix pool

56 distinct affixes (27 prefixes / 29 suffixes) extracted to `affix-pool.md` with effects, tiers and slots observed. Not exhaustive — it grows with future captures. No same-`group` duplicates appear anywhere in this snapshot, making the Fortified Firewall's double `of Sandboxing` (21 July Augment) look like a rare event rather than routine.

## 5. Still open (this data cannot answer)

- Whether Compile multiplies the implicit affix (needs before/after compile capture).
- Version Upgrade roll behaviour on success (needs before/after capture).
- Augment tier/affix distribution (needs samples).
- Hit-chance, mitigation and streak-recovery formulas (combat-side).
