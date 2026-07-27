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

- **Snapshot Backups** (crafting upgrade): +5% chance per level to not lose Stability on a failed Version Upgrade (`tier_promotion_stability_preserve`). Level 0 when this was written on 22 July 2026; **level 2 (=10%) by 27 July**, and the craft cost model went on assuming 0 the whole time — every Stability budget in between was ~6% over-conservative. **Read the level from the capture, never from this note:** `ihlib.stability_preserve_chance` does it, and `plan_craft` now budgets in Stability rather than attempts because the two diverge once this is above 0. Max level 5 (25%).
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

Vital Driver of Precision displayed rare with 5 affixes; after Augment added a 6th (22 July, 21:25 capture) it displays **epic**. Second observation 23 July (10:00 capture): Citadel Shell of Recovery, rare with 5 affixes, flipped to **epic** on its Augment adding a 6th. Third 27 July (15:25 capture): Targeted Analyzer of Lightning, rare with 5, flipped to **epic** when Augment added Ravaging. The rare→epic-on-6th-affix pattern is now **3/3**; still unknown whether rarity is purely an affix-count display, whether promotion unlocks a Signature affix slot, or whether it affects drops/decompile yield.

### 13. Hardware/homelab percentage stacking — RESOLVED 27 July 2026

Confirmed formula-level from `stats_breakdown`: hardware, homelab and equipment percentages share one additive pool, in three stat families. Moved to `docs/mechanics.md` §13, together with the decoded hardware chip cost curve.

### 14. Version Upgrade tier-roll behaviour — strong evidence 23 July 2026 (was: unresolved item 2)

During the Bastioned Payload craft (08:26 → 08:28 captures), of Infection went roll 100% → of Decay roll 50%, and of Targeting roll 82% → of Unerring roll 60% across multi-step promotions. Strong evidence that a successful Version Upgrade **rerolls the value within the new tier** rather than preserving relative roll position. Not yet formula-level (no per-step captures); one single-step before/after capture would finish it.

### 15. Hackcoin deduction timing (added 23 July 2026; narrowed 27 July)

Homelab job hackcoin costs did not visibly deduct at queue time (11 hc held at 09:44 with Worker Orchestrator +3 and QoS +1 queued; still 11 at 10:33 after queueing Snapshot Backups +1; 9 by 11:52 after QoS completed).

**27 July — credits and resources ARE charged at queue time.** Queueing 8 homelab jobs (4 `active_jobs` + 4 `pending_jobs`) dropped credits by exactly 3,544,295,863 against a summed `cost_snapshot` of 3.55B across both groups, and every pending job carries a full `cost_snapshot`. The general model is therefore **charge-on-queue**, which makes the 23 July hackcoin observation a *hackcoin-specific* anomaly rather than a general deferral — either hackcoin alone defers to completion, or the earlier reading was confounded.

Still unresolved, and it decides the install-gate reserve: until a queued hackcoin job is watched against a known balance, treat queued-but-incomplete hc costs as unpaid liabilities. One queued hc job plus a before/after capture settles it.

### 16. Version-Upgrade Stability cost — RESOLVED 27 July 2026 (it was Snapshot Backups)

Three consecutive crafts beat the planner's Stability budget by 1.2–1.5×, which looked like the documented chance table being wrong. The player identified the actual cause: **Snapshot Backups had reached level 2 (10% chance to preserve Stability on a failed Version Upgrade) while the cost model still assumed level 0.** Attempts and Stability are not the same quantity once that upgrade is above 0.

Corrected model (`vu_expected_stability` = `1 + ((1-p)/p) × (1-preserve)`), applied to every contract craft with the preserve level that was live at the time:

| Craft | promotions | expected Stability | actual | ratio |
|---|---|---|---|---|
| Bastioned Payload (23 Jul, 0%) | 8 | 11.8 | 21 | **1.78× worse** |
| Phoenix Shell (23 Jul, 0%) | 12 | 22.2 | 17 | 1.31× better |
| Targeted Analyzer (27 Jul, 10%) | 12 | 26.6 | 19 | 1.40× better |
| Titanic Router (27 Jul, 10%) | 12 | 24.5 | 20 | 1.22× better |

**Geometric mean 0.944 — 5.9% better than model across four crafts, well inside noise at ~12 promotions each. The documented chance table needs no revision.** The apparent trend was three favourable runs read without the one badly unfavourable run that preceded them, plus an un-modelled 6% discount. Snapshot Backups alone is worth −6.2% Stability on a T7→T1 chase, −4.3% on T8→T3, and the saving grows with depth because deeper steps fail more often.

Method note worth keeping: this was found because the player knew a game system the capture-derived model had silently outgrown. Any hard-coded "current level: N" in these docs is a decaying assertion — read levels from the capture.

### 17. What `reward_streak_soft_cap` actually caps (added 27 July 2026)

Every zone carries one (Small Business Server 120, Corporate Network 200). The community new-player guide advises moving zone once you can exceed the current cap by ~10%, which presupposes rewards stop scaling past it.

**Not visible in credits.** Across 5,325 winning fights, credits per enemy level are flat at 8.25 → 8.45 through every streak band 60–129, including the 120–129 band that sits past the cap. Either the cap applies to a different reward axis (drop chance, drop rarity, chips, contract progress — `rarity_multiplier` being a separate zone field points this way), or it softens gradually, or 34 fights past the cap is simply too few to see it.

Resolvable cheaply now that streaks routinely pass 120: bank ~200 fights above the cap and compare drop rate, `drop_rarity` distribution and `chips_drop` per fight against the 90–119 bands, normalised by enemy level. Until then treat the +10% guidance as external advice that our own data neither confirms nor refutes — the zone-transition case stands on the multipliers and offset arithmetic (`mechanics.md` §15), which do not depend on it.
