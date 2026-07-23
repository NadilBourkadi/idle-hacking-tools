# Idle Hacking — Open Questions and Research Log

This file prevents working models from silently becoming facts.

## Confirmed crafting mechanics — 21 July 2026

### Stability and Compile

- items normally drop with 25-30 Stability;
- most craft actions cost 1 Stability;
- Compile consumes all remaining Stability;
- Compile grants +0.5% non-signature affix values per remaining point;
- Compile is permanent and should be last.

### Version Upgrade

The current schema-4 export showed a uniform chance table across 165 captured affix controls:

- T9→T8 90%;
- T8→T7 80%;
- T7→T6 70%;
- T6→T5 60%;
- T5→T4 50%;
- T4→T3 40%;
- T3→T2 30%;
- T2→T1 20%;
- T1 unavailable.

Failed attempts do not improve the tier and consume resources. Normal failures consume Stability; Snapshot Backup can sometimes prevent the Stability loss.

### Refactor

- rerolls numerical values within the same tier;
- can roll worse;
- bracketed ranges are the current tier's roll range;
- use after tier upgrades, not before.

### Augment / affix capacity

- normal cap is 3 prefixes and 3 suffixes;
- Augment fills the remaining affix slot;
- 3P/2S forces a suffix and 2P/3S forces a prefix;
- Augment's current UI cost can include primary resource plus Credits.

### Lock / Prune / Bias Reroll

- only one affix can be crafting-locked;
- Prune removes one random unlocked affix;
- Prune and Bias Reroll consume the active lock on success unless auto-relock succeeds;
- current Bias Reroll UI cost is primary resource + Credits + 20 Essence;
- the selected essence guarantees a category/orientation, not one exact affix.

## Priority open questions

### 1. Snapshot Backup — RESOLVED 22 July 2026

From `homelabInfo` in the rich capture:

- **Snapshot Backups** (crafting upgrade): +5% chance per level to not lose Stability on a failed Version Upgrade. **Current level: 0** — trigger chance 0%, so the "conservative" no-backup craft budgets are exact.
- Distinct upgrade with a confusable name: **Snapshot Rollback** (combat): recover 25% HP after lethal damage, once per 10 fights, cooldown −1/level. Also level 0. Anti-attrition candidate.
- Whether Snapshot Backups affects other failed actions remains unknown (irrelevant while level 0).

### 2. Successful Version Upgrade roll behaviour

First evidence 22 July (Storm Daemon, phases 1–2): roll positions moved 84%→71%, 39%→55%, 1%→80% across upgrades — the 1%→80% jump strongly suggests the new-tier value is **independently rerolled** (n=3 effects; treat as working model, not fact).

Still unknown:

- confirmation at larger n;
- whether relative roll percentile is preserved or transformed in any case.

Test:

- export before one successful tier upgrade;
- export immediately after;
- compare old/new ranges and percentile.

### 3. Bias Reroll exact semantics

Unknown:

- how many affixes are rerolled;
- whether selection is prefix/suffix constrained;
- exact interaction with a full item and one lock;
- whether failed/successful operation consumes Stability in all cases.

Test only on a disposable item after enough Essence is available.

### 4. Compile coverage — LARGELY RESOLVED 22 July 2026

Confirmed on the Perfect Strike Payload compile (+5.5%):

- explicit affix `value` fields are multiplied **in place** (×1.0552 exact); `value_min`/`value_max` stay at the tier range, so **post-compile roll positions are inflated and not comparable**;
- the **implicit is NOT multiplied** (5.86% unchanged pre/post);
- consequence: compiled items' displayed stats are final — never re-apply the bonus in analysis (fixed in `ihlib.plan_craft`).

Still unknown: rounding order; interaction with an Optimization Pass base bonus.

Test:

- before/after compile export with at least one percent and one flat stat.

### 5. Augment distribution

Unknown:

- tier weighting;
- affix weighting within the forced side;
- whether item level or rarity affects the roll distribution beyond magnitude.

### 6. Complete affix pool and slot constraints — PARTIALLY RESOLVED 22 July 2026

The full-state capture exposes `affix_id`/`group` per affix. Observed pool (56 affixes) is tabulated in `affix-pool.md` and grows with each capture. Still missing: unowned affixes, tier weighting, bias-category mapping.

### (superseded original text)

Need a durable table of:

- every prefix and suffix;
- stat outputs;
- supported slots;
- bias category;
- mutually exclusive families;
- tier availability/weighting.

The in-game Help Affixes table is authoritative but was not present in static export data. A passive structured capture of that visible table would make future Augment advice exact rather than based on observed names.

### 7. Exact hit-chance formula

Known: Accuracy and Evasion determine hit reliability.
Unknown: formula, caps/floors and modifier interactions.

### 8. Defense and Armor Penetration formula

Unknown: mitigation curve, penetration treatment and breakpoints.

### 9. Streak recovery model — RESOLVED 22 July 2026 (formula), residual unknowns

Exact law from 21 winning fights: `heal = heal_base × 0.99^(streak − 10)`, capped at missing HP. See `mechanics.md` §3.
`heal_base` resolved 22 July (second rich capture): **5 × player hack level** — `statsBreakdown.post_combat_heal` shows the full 4,470 under `level` (= 5 × 894); the earlier 4,465 sample matches level 893. Not max-HP- or equipment-scaled.
Remaining unknowns: what triggers `post_combat_heal_exhaustion_relief` (0 in all samples), and whether the 0.99^ decay would also apply to Homelab `thermal_budget` post-combat healing.

### 11. In-fight regeneration decay

In the streak-96 loss compact log, realised per-round regen (`prg`) declined within the fight — 179, 146, 113, 80, 47 … 14, 0 — quantized in steps of 33, hitting 0 near death, while listed loadout Regen was +148. One loss sample only; direction unknown on victories. If regen genuinely exhausts over a fight, long fights (32–47 rounds at late streak) run mostly regen-less, which makes fight-shortening stats (Accuracy vs high-evasion, Attack Speed, damage) worth more than a naive constant-regen model implies. Needs: compact logs from long winning fights, and whether `prg` correlates with current HP, rounds elapsed or a depleting pool.

### 10. Corruption and Thorns formulas

Observed and behaviorally described, but exact scaling/rounding remains unresolved.
Measured 22 July (streak-96 death fight): player Corruption 12 dealt `sum(ecd)` 990 vs 5,368 direct — ~15.6% of output, ramping over the fight (`ecd` 22→110/round). Corruption is a significant outgoing-DoT stat in long fights; per-point scaling and stack mechanics still unknown.

## Decision record

### 21 July 2026 — candidate requests redefined

Future candidate evaluations default to selecting and planning crafting projects. An immediate-equip comparison is secondary.

### 21 July 2026 — deterministic crafting protocol adopted

Every top recommendation must include Augment outcomes, target tiers, maximum attempt budgets and a Compile floor.

### 21 July 2026 — current Firewall priorities

- Primary: Citadel Firewall of Warding.
- Forced-suffix Augment probe: Fortified Firewall of the Giant.
- Alternate speed/barrier project: Aligned Firewall of Bastion.


---

## 22 July 2026 — static-analysis resolutions

From the first full-state capture (see `static-analysis-2026-07-22.md`):

- **Resource-cost scaling formula: RESOLVED.** `base_cost ≈ 1.586 × required_hack_level^1.765`; `stability_multiplier = 1.03^spent` (exact) applies to Credit costs only; per-operation multiples tabulated. Compile costs `0.18 × remaining Stability × base_cost`.
- **Item-level stat weighting: RESOLVED.** `value = base_value × ((ilvl+125)/1125)^0.391` for percentage stats (base normalized to ilvl 1000); flat stats ≈ exponent 0.785.
- **Version Upgrade chance table: re-confirmed** across 415 affix instances.
- Affix pool: observed table now maintained in `affix-pool.md` (see item 6 above).

## 21 July 2026 confirmed test outcomes

### Kernel trade rejected directionally

A trade of +11 listed Regeneration and +5.53% Max HP for -7.46% Defense, -1.57% Accuracy and -2.09% Attack Speed did not improve the observed streak range. This is a build-specific empirical veto, not a general stat-conversion formula.

### Augment operation details confirmed

A forced-suffix Augment:

- consumed one Stability;
- changed a five-affix Rare into a six-affix Epic;
- rolled T9;
- allowed a duplicate affix family.

### Newly prioritised open tests

1. Matched-enemy Hearty Kernel versus crafted Kernel comparison, preferably multiple samples per side.
2. Successful-fight exports to decode post-combat heal and exhaustion.
3. Version Upgrade before/after export to determine new-tier roll behaviour.
4. Snapshot Backup chance/trigger capture.
5. Bias Reroll before/after capture.

### 22 July 2026 — resolved

- The actual 0.6.1 userscript source was recovered from Tampermonkey and is archived at `tools/item-loadout-capture.user.js`.

### 12. Rarity promotion on 6th affix

Vital Driver of Precision displayed rare with 5 affixes; after Augment added a 6th (22 July, 21:25 capture) it displays **epic**. Single observation — unknown whether rarity is simply an affix-count display, whether promotion unlocks a Signature affix slot, or whether it affects drops/decompile yield. Check on the next rare that gains a 6th affix.
