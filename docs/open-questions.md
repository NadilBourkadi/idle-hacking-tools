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

### 3. Bias Reroll exact semantics — PARTIALLY RESOLVED 27 July 2026

Resolved from `vendor/game-js` and the capture (see `crafting.md` §7): the client sends only `BIAS_REROLL {item_id, essence}`; cost is `bias_primary_cost` + `bias_credit_cost` + **5 × (affix count − 1)** Essence; Prune and Bias Reroll consume the active lock, and the panel offers an auto-relock toggle costing Credits + 1 Stabilizer. **Lock costs 1 Stabilizer**, which is what Stabilizers are for — nothing else consumes them.

Still unknown, all server-side:

- how many affixes a Bias Reroll actually rerolls;
- the essence → affix-category mapping (8 essences: optimization, prosperity, expertise, precision, damage, survival, retribution, dexterity — the client only passes the name);
- whether selection is prefix/suffix constrained;
- whether the operation consumes Stability on both outcomes.

Now cheap to test: Essence is abundant (survival 2,699 ≈ 100+ rerolls) and Stabilizers are plentiful (94 ≈ 94 Locks). One disposable item, lock a known affix, bias with a known essence, capture before and after.

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

### 7. Exact hit-chance formula — **RESOLVED 29 July 2026** (`mechanics.md` §18)

**`logit(hit) = 0.532 + 1.208 × ln(Accuracy / Evasion)`**, fitted on 2,953 attacks over enemy evasion 3,002–7,699 from a Software Profiler sweep. The ratio-power form `acc^k/(acc^k+eva^k)` is rejected. **Accuracy is not saturated** at this build's level (76–79% hit at the evasion the deep bands face), which retires the 27 July reading; `CRAFT_WEIGHTS_PCT["Acc"]` moved 0.14 → 0.19. Residual unknowns: caps/floors outside the fitted ratio range 1.20–3.07, and whether the constants depend on player level.

### 8. Defense and Armor Penetration formula — **RESOLVED 29 July 2026** (`mechanics.md` §18)

**`damage = AttackDamage × K / (K + Defense − ArmorPen)`, K ≈ 205** — fitted independently on both directions (K = 190.2 outgoing, 219.3 incoming). ArmorPen subtracts directly from Defense, so the curve is convex and ArmorPen's value per point *rises* as it approaches the target's Defense. Defense elasticity is −0.88 at our 1,487. ArmorPen's inherited weight of 0.05 is **validated** (measured 0.044–0.051). Residual unknowns: whether K is a constant or scales with level, and behaviour when ArmorPen exceeds Defense.

### 9. Streak recovery model — RESOLVED 22 July 2026 (formula), residual unknowns

Exact law from 21 winning fights: `heal = heal_base × 0.99^(streak − 10)`, capped at missing HP. See `mechanics.md` §3.
`heal_base` resolved 22 July (second rich capture): **5 × player hack level** — `statsBreakdown.post_combat_heal` shows the full 4,470 under `level` (= 5 × 894); the earlier 4,465 sample matches level 893. Not max-HP- or equipment-scaled.
Remaining unknowns: what triggers `post_combat_heal_exhaustion_relief` (0 in all samples), and whether the 0.99^ decay would also apply to Homelab `thermal_budget` post-combat healing.

### 11. In-fight regeneration decay

In the streak-96 loss compact log, realised per-round regen (`prg`) declined within the fight — 179, 146, 113, 80, 47 … 14, 0 — quantized in steps of 33, hitting 0 near death, while listed loadout Regen was +148. One loss sample only; direction unknown on victories. If regen genuinely exhausts over a fight, long fights (32–47 rounds at late streak) run mostly regen-less, which makes fight-shortening stats (Accuracy vs high-evasion, Attack Speed, damage) worth more than a naive constant-regen model implies. Needs: compact logs from long winning fights, and whether `prg` correlates with current HP, rounds elapsed or a depleting pool.

### 10. Corruption and Thorns formulas

Observed and behaviorally described, but exact scaling/rounding remains unresolved.
Measured 22 July (streak-96 death fight): player Corruption 12 dealt `sum(ecd)` 990 vs 5,368 direct — ~15.6% of output, ramping over the fight (`ecd` 22→110/round). Corruption is a significant outgoing-DoT stat in long fights; per-point scaling and stack mechanics still unknown.

### 13. Does player level actually confound a death-streak baseline?

Every A/B in this workspace has been read as if hack-level growth inside the window inflates death streaks, so windows are kept short. The 27 July ledger is weak evidence against that: across 38 deaths in 14:00–20:00 UTC, hourly mean peak death streak ran 114.2 / 127.6 / 117.3 / 113.0 / 113.9 / 115.0 — **flat, while hack level rose 1,031 → 1,058 (+27)**. If enemy scaling tracks player level closely, level growth cancels out and long baselines are cheaper than assumed, which matters because the ledger needs ~41 deaths to resolve a +3 shift at 80% power (se 1.12, sd 6.9).

Not confirmed: n is 5–7 per bucket, the day also contains a zone change and the Analyzer/hardware/Router bundle, and enemy level at death ranged 1,673–1,843 without an obvious trend. Needs: peak death streak regressed on hack level within one zone and one gear configuration, over a window with no equipment change. Until then keep segmenting baselines at gear boundaries, but stop treating a multi-hour window as automatically spoiled by levelling.

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

**PARKED 27 July 2026 — the measurement window closed.** Resolving this needed fights above the cap, and the move to Corporate Network raises the cap to 200 while costing ~4 streaks of depth. Streaks will sit near 129 against a 200 cap, so no data above a cap will accrue again until depth roughly doubles. That is the right trade — the question is low-value and the transition case never depended on it (`mechanics.md` §15) — but it is the reason the ~34 fights banked above 120 on 27 July are the only such sample that will exist for a long time. If the question ever matters, those fights plus the 90–119 bands are the sample; compare drop rate, `drop_rarity` distribution and `chips_drop` per fight, normalised by enemy level.

General lesson worth more than the question: **a progression step can close a measurement window.** When a move changes the regime being measured, bank the observation first or accept losing it — and say which, rather than discovering it later.

### 17. Deep tier-ladder growth per affix family — OPEN, cheap to resolve (27 July 2026)

How much an affix gains per tier below T5 varies by family and is only measured for the families the inventory happens to cover. Observed deep steps span **1.146 (`suffix_attack`) to 1.417 (`suffix_adaptive_shell`)**, median 1.263 (n=25). Over a five-tier chase that is a 2.7× spread in the final value — larger than any other uncertainty in a craft verdict, and it silently decided the Driver verdict (`crafting.md` §12.1).

Unknown: whether the step is a per-family constant, decelerates toward T1 in some families and not others, or tracks something visible (effect count, stat type, affix rarity). `suffix_attack` decelerates monotonically (1.232 → 1.171 → 1.146); `suffix_adaptive_shell` and `suffix_regeneration` hold ~1.40 to T1. No hypothesis yet separates them.

**Resolution is cheap and self-densifying:** `value_min`/`value_max` in every capture are the tier's full range, so *one successful Version Upgrade* pins that family's next step exactly — no repeated sampling needed. Every craft already run therefore pays down this debt for the families it touches. `ihlib.fit_tier_steps` re-fits the two region constants from each capture automatically.

Immediate probe: `of Execution` T6→T5 on the Aegisbound Driver (`suffix_critdamage`, currently a **single** observation and the family with the most riding on it).


## Does tempo move the death ceiling? (opened 27 July 2026)

The 22 July law says it does not, and `current-state.md` treats output/tempo as "the deliberate cost". Session 8 measured fight cadence as a **fixed 4.872 s tick** (`mechanics.md` §14), which means attack speed cannot buy income — but the same measurement found rounds/fight down **−8.3%** at streak 106–130 and **−4.2%** at 86–105 after a +9.9% attack-speed equip. Fewer rounds at fixed wall clock = fewer enemy attacks per fight = less damage taken. That makes attack speed an **attrition** stat, which the 22 July law denies.

- Status: **the strict law is dead; the quantitative question is open.** Two closed windows now show ceiling moves with output/tempo in the bundle: `payload-ab-2026-07-30` (+14.8 streaks on an AtkDmg/Corrupt craft, closed KEEP 31 Jul) and `firewall-ab-2026-07-31` (+12.6 at 15/24, mitigation-led but with rounds/fight down 6–11%). Both bundle same-hour hardware packages, so the *size* of the pure tempo term is still unmeasured. `CRAFT_WEIGHTS_PCT[AtkSpd]` is 0.56 (mitigation-stat rationale, validated 27 Jul); the open question is whether that under- or over-prices the rounds-exposure channel.
- **New sub-question (31 Jul):** in the Firewall window, damage taken per round fell far more at shallow bands (−24% at 60–85, −44% at 24–42) than the −9% the Defense law predicts, while deep bands matched prediction (−10/−11%). Hypothesis: corruption-stack exposure scales superlinearly with fight length, so shorter fights cut incoming DoT disproportionately where fights are already short. Testable with paired Software Profiler arms at matched enemy levels (stack counts are in the round detail).
- Confounds: every live window bundles hardware; the profiler isolates single-fight mechanics but not streak depth.
- **CORRECTED 29 Jul 2026:** the gear-customised *full-streak* sim is the **CI/CD Pipeline**, which is a separate homelab upgrade gated at **homelab 12** (not 10) and still at level 0. The Hacking Simulator install (homelab 10, now owned) ships the **Software Profiler**, which simulates fights at a chosen enemy level — it can measure rounds/fight and damage taken per fight against a fixed enemy, which is the mitigation half of this question, but it cannot see streak depth. See `docs/simulator-protocol.md`.

## Unexplained 2.7% fight-cadence step (opened 27 July 2026)

Fight cadence read **5.000 s/fight** in the 17:00Z bucket (n=6, range 4.991–5.001) and **4.867** from 18:00Z onward (n=23). A one-time ~2.7% speed-up with no obvious cause. It is *not* attack speed — the +9.9% AtkSpd equip at 21:50Z produced no cadence change at all. Candidates: a homelab upgrade completing, a zone or enemy-class effect, or a client/server tick change. Low stakes (it is worth ~2.7% of all income) but it is the only known lever on a quantity otherwise believed constant, so it is worth identifying.


## Is Accuracy saturated at this build's level? (opened 27 July 2026)

Cutting Accuracy 7,595 → 7,265 (**−4.35%**) with the Driver equip produced **no hit-rate loss at matched streak band** — +0.89pp / +1.47pp / +1.69pp at bands 60–85 / 86–105 / 106–130 on 8,195 post-equip attacks, against a roughly-linear prediction of −1.7pp. Player levelling accounts for at most +0.3% of accuracy over the window.

- Status: **the loss is falsified; the rise is unexplained.** Each band is only z ≈ +1.2 to +1.9, but all three move the same way.
- Why it matters: `CRAFT_WEIGHTS_PCT` prices Accuracy at **1.0**, joint-highest with Defense and Evasion, and `current-state.md` still lists hit reliability as bottleneck #2. If accuracy is saturated in the 7.2–7.6K region against Corporate Network evasion, both are wrong and the Daemon verdict (+8.9, part of whose case is Acc +3.2%) is overstated.
- Constraint this puts on the unknown hit-chance formula (§7/§8): it is **flat in accuracy** across 7.2–7.6K at these enemy evasion levels — consistent with a ratio-based curve deep in diminishing returns, not a linear or additive one.
- Cheapest resolution: the **Software Profiler** (homelab 10) runs 100 sims against a chosen enemy level, which isolates hit rate from streak composition entirely. **Owned since 29 Jul 2026** and it returns the enemy's `effective_evasion` with every logged fight, so the hit-rate-vs-evasion curve is directly traceable — `docs/simulator-protocol.md` §5.


## Does realized regeneration scale with how depleted you are? (opened 28 July 2026)

The Resilient Firewall raised **listed** Regeneration +29.7% (388.5 → 504.0, later 520.8 with ECC L100→L110). Realized `prg`/round, matched on streak band over 323 detailed post-equip fights:

| band | pre | post | realized gain |
|---|---:|---:|---:|
| 60–85 | 220.3 | 221.1 | **+0.4%** |
| 86–105 | 264.9 | 277.3 | +4.7% |
| 106–130 | 306.8 | 342.2 | **+11.5%** |

Realization **rises monotonically with streak depth**, and this *understates* it — the ECC buy landed inside the window and added listed regen on top, so the true denominator is larger than +29.7%. Ratio at depth ≈ 0.39 against listed; ≈ 0 shallow. Every previous regen buy realized 0.57–0.91 (hardware +13.6% realized on +14.9% listed; Router +19.1% on +33.5%).

- **CONFIRMED FORMULA-LEVEL 29 July 2026 (evening) — overheal capping is exact:** `prg` is truncated to `max_hp − php` (288/288 profiler rounds, `mechanics.md` §17). A listed-Regeneration buy therefore realizes **nothing** near full HP and **1:1** once depleted, which is the whole band pattern below with no extra mechanism needed. The corruption suppression term (−1.5 × `ecd`) accounts for the rest. Original working model:

**Working model: overheal capping.** `data-dictionary.md` already suspects `prg` is under-reported at full HP. Shallow in a streak the player sits near full HP and surplus regeneration is discarded; deep, HP is depleted and it lands. The monotone band pattern is what that model predicts.
- **Why it matters:** `CRAFT_WEIGHTS_FLAT["Regen"] = 0.6` prices regeneration **flat**. If this holds, regen's value is concentrated at depth — which is where runs end, so the direction is favourable — but the *average* realization on a large buy is far below 1, and a second large regen buy on top of this one will realize less again. This is the first evidence of diminishing returns on the build's confirmed win condition, and it is the reason the standing chip advice caps ECC rather than pouring the whole budget in.
- **Confounds:** one window, ~23 minutes, bundled with ECC +10, Encryption +10, two player levels and Mechanical Keyboard L10.
- **Cheapest resolution:** segment realized `prg`/round by *starting-HP fraction* rather than by streak band — the ledger already has `starting_hp`/`max_hp` per fight, so this is an analysis, not a measurement. If the relationship is with depletion rather than streak, that separates the two directly. Do this before any further regen purchase.

## How much damage does Defense actually stop? (opened 28 July 2026)

`CRAFT_WEIGHTS_PCT["Def"] = 1.0` — joint-highest weight in the table — and Defense has **never been isolated**: every prior change arrived bundled with regeneration or barrier moving the same way. The Firewall equip gives the first usable read, because it cut Defense while raising regeneration, and `damage_taken` is **gross** intake (verified, `data-dictionary.md`) which regeneration does not touch.

Gross damage/round at streak 106–130: **349.0 → 368.6 (+5.6%)** against Defense −6.05% at equip. Roughly 1:1 elasticity.

- Status: **directional, single window, n=35 fights at depth.** Evasion also rose +4.4%, which pushes gross intake the other way, so Defense's own elasticity is probably slightly worse than 5.6/6.05.
- Why it matters: this is the only number bearing on a weight that decides Firewall/Kernel/Router verdicts. It is registered as `asserted` in `ih.py assumptions` for exactly this reason.
- Cheapest resolution: the **Software Profiler** (homelab 10) — fixed enemy, fixed level, vary Defense only. **Owned since 29 Jul 2026**; `gear_set_capacity` is 2, so a Defense-only gear set can be A/B'd against the live loadout without equipping either — `docs/simulator-protocol.md` §6.

## Why does realized regeneration under-perform against exactly three enemy classes? — **RESOLVED 29 July 2026 (evening)**

**Answer: it does not. `prg` is a NET figure and corruption is subtracted from it at exactly 1.5:1.**
`prg = clamp(Regeneration − 1.5 × ecd, 0, max_hp − php)`, verified 288/288 rounds on the first two Software Profiler runs (`mechanics.md` §17). Of the three hypotheses below, **(1) healing-reduction was right** — and it is exact, not approximate. (2) is wrong, (3) is wrong in sign as suspected. Incoming corruption costs **2.5× face value** (1.0 direct + 1.5 regen destroyed). The counter is **Isolated Sandbox** [Virtualization Cluster], homelab 11.

<details><summary>original question, kept for the method note</summary>


At streak 106–145 post-Kernel-craft, realized `prg` per round as a share of gross damage per round splits cleanly in two:

- **Trojan Wall 83%, Rootkit 85%, Stealth Worm 88%** — net drain positive, and these three caused **11 of 11** deaths in the window.
- Spike Router, Logic Bomb, Zero-Day, Glitch Phantom, Siege Daemon, Brute Force — **98–104%**, all net-negative.

n = 32–50 victorious fights per class, matched on streak band. Barrier absorption is flat across all nine classes (26–36/round), so this is specific to regeneration.

**It is not simply "they hit harder."** Spike Router has the *highest* gross damage per round (407) and realizes 99%; Trojan Wall hits for 380 and realizes 83%. Nor is it fight length (50–58 rounds across all classes) or outgoing damage (486–557).

Candidate explanations, none tested:
1. A **healing-reduction / regen-suppression** effect carried by those classes (or by a shared modifier — note "Mirrored" and "Silent" prefixes recur among the killers).
2. `prg` is **capped per round** by something correlated with their attack pattern — e.g. the cap binds when a single hit exceeds a threshold, or when HP is above some fraction.
3. An **overheal-capping artifact**: if `prg` is truncated at missing HP, classes that keep the player nearer full would report *lower* `prg` — but that predicts the opposite sign of what is observed, since the dangerous classes are the ones draining HP.

**Why it matters:** this single ratio decides the death ceiling. Closing the Trojan Wall gap needs ~+59 listed Regen (+11%) — out of reach by gear (every regen anchor is crafted) or hardware (~35 ECC levels, ~280K chips). If instead it is a *suppression* effect, the counter may be a different stat entirely and much cheaper.

**How to test:** the enemy record in each fight carries `enemy_stats`. Compare the stat vectors of the three lethal classes against the six safe ones and look for a field that separates them cleanly; then check whether it correlates with the `prg`-to-gross ratio fight by fight. Both are already in the ledger — this needs no new data collection.

</details>
