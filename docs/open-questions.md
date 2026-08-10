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

> **`par.N` cross-references from code and from other docs address the
> numbering of *this* section.** The dated archive sections lower down
> ("static-analysis resolutions", "confirmed test outcomes") carry their own
> independent 12–17 series, so several numbers appear more than once in this
> file. §17 appears three times. Read `par.15` as §15 below (the Barrier
> weight), never as the archive's §15 (hackcoin deduction timing). Noted
> 7 Aug 2026 rather than renumbered, because renumbering would silently
> break every existing `par.N` reference in `ihlib.py` and `ih.py`.

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

### 14. CI/CD Pipeline — what is the ~+10 absolute offset made of? — **RESOLVED 6 Aug 2026 (evening): mostly the hardware package, real**

The pre-registered discriminator fired on the (b) branch: `driver-ab-2026-08-03`
closed at a live post mean of **189.2** — in the "~185+" region, not the
"176–178" region — so the +10 offset was **mostly the 5 Aug 290K-chip hardware
package being real**, not instrument bias. Residual sim-vs-live gap at matched
hardware ≈ −2 (sim old-arm 187.3 vs live 189.2 carrying the craft's ~+1.9),
inside noise, with some share owed to Snapshot Rollback procs (41 in 6,561
post fights) whose simulation status is still unknown. Recorded as an
instrument property in `simulator-protocol.md` §9.3: **the sim's absolute
scale is usable when its hardware matches the live era**; re-measure the
offset once per gear era per §9.4. Residual sub-question kept: whether the
sim models Rollback (run a with/without-Rollback pair if it ever becomes
uninstallable, or compare sim best/worst logs for a 25%-HP revive signature).

### 15. Does the Barrier weight over-price death-streak depth?

The +44.0-realized Driver craft (Barrier +54.4 carrying the weighted score)
measured **−0.58 ± 1.03 simulated streaks** on 15 paired CI/CD runs — a
score-vs-objective gap. Both inputs are individually measured (Barrier's
once-per-fight 1.00×-stat drawdown law; archive tier ladders), so the suspect
is the *conversion*: at the 180+ streak faces the enemy alpha may consume the
whole pool in ~1–2 rounds, making Barrier's marginal depth value shrink with
depth even though the drawdown law holds at every depth. Prior Barrier-carried
verdicts (Analyzer 27 Jul, Daemon 29 Jul) landed in shallower eras. **The live
close corroborates the sim (6 Aug): decomposing `driver-ab-2026-08-03`'s
+12.6 bundle against the sim's matched-hardware absolute leaves the craft's
own depth share at ~+1.9 ± 2 — a +44.0-score, Barrier-carried craft again
reading ~0 depth, now in live data.** Still open on mechanism (alpha-consumes-
the-pool is the suspect); next step is a dedicated CI/CD pair isolating
Barrier at matched depth. **Entered in `ihlib.PENDING_REFITS` 7 Aug 2026**
as the per-family score->depth conversion (applied as 1.0 everywhere), after
`hardware_plan` was found routing 96% of a 161K-chip balance into the Barrier
track over the Regen track purely on unconverted score; `ih.py hardware` now
marks depth-suspect rows and every weight-consuming command banners while the
row stands. Unblock: the pair below, full 15-run block. Until resolved, treat Barrier-carried score deltas
at deep streaks as optimistic on depth — they may still be real on economy
(shorter drawdown ⇒ fewer near-death fights; note the driver window's
damage-taken/fight at streak 24–42 *fell* 306 → 181 behind the bigger pool).

### 16. Contract carry-through — residual unknowns (mechanic in `mechanics.md` §20)

The active contract surviving the daily reset is player-observed (6 Aug 2026,
n=1). Still unobserved: (a) the **payout** of a carried contract completing
after reset — presumed normal (credits/chips/hackcoin) but no balance-delta
has been captured around one yet; (b) whether a **partially-progressed
inactive** contract survives reset (within one board day inactive progress is
retained — the 31 Jul Extended Harvest sat at 3/1,374 through hours — but
across a reset it has never been watched); (c) what the board looks like
while a carried contract runs — 7 fresh + 1 carried, or does the carried one
occupy a slot; (d) whether ASIC Subsystem's +1 hc-per-board-reset lands on
carried contracts. One capture taken while a carried contract is still
running, and one shortly after it completes, settles all four.

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

Corrected model (`version_upgrade_expected_stability` = `1 + ((1-p)/p) × (1-preserve)`), applied to every contract craft with the preserve level that was live at the time:

| Craft | promotions | expected Stability | actual | ratio |
|---|---|---|---|---|
| Bastioned Payload (23 Jul, 0%) | 8 | 11.8 | 21 | **1.78× worse** |
| Phoenix Shell (23 Jul, 0%) | 12 | 22.2 | 17 | 1.31× better |
| Targeted Analyzer (27 Jul, 10%) | 12 | 26.6 | 19 | 1.40× better |
| Titanic Router (27 Jul, 10%) | 12 | 24.5 | 20 | 1.22× better |

**Geometric mean 0.944 — 5.9% better than model across four crafts, well inside noise at ~12 promotions each. The documented chance table needs no revision.** The apparent trend was three favourable runs read without the one badly unfavourable run that preceded them, plus an un-modelled 6% discount. Snapshot Backups alone is worth −6.2% Stability on a T7→T1 chase, −4.3% on T8→T3, and the saving grows with depth because deeper steps fail more often.

Method note worth keeping: this was found because the player knew a game system the capture-derived model had silently outgrown. Any hard-coded "current level: N" in these docs is a decaying assertion — read levels from the capture.

### 17. What `reward_streak_soft_cap` actually caps — **RESOLVED 7 August 2026** (`mechanics.md` §22)

Every zone carries one (Small Business Server 120, Corporate Network 200). The community new-player guide advises moving zone once you can exceed the current cap by ~10%, which presupposes rewards stop scaling past it.

**Not visible in credits.** Across 5,325 winning fights, credits per enemy level are flat at 8.25 → 8.45 through every streak band 60–129, including the 120–129 band that sits past the cap. Either the cap applies to a different reward axis (drop chance, drop rarity, chips, contract progress — `rarity_multiplier` being a separate zone field points this way), or it softens gradually, or 34 fights past the cap is simply too few to see it.

**PARKED 27 July 2026 — the measurement window closed.** Resolving this needed fights above the cap, and the move to Corporate Network raises the cap to 200 while costing ~4 streaks of depth. Streaks will sit near 129 against a 200 cap, so no data above a cap will accrue again until depth roughly doubles. That is the right trade — the question is low-value and the transition case never depended on it (`mechanics.md` §15) — but it is the reason the ~34 fights banked above 120 on 27 July are the only such sample that will exist for a long time. If the question ever matters, those fights plus the 90–119 bands are the sample; compare drop rate, `drop_rarity` distribution and `chips_drop` per fight, normalised by enemy level.

**RESOLVED 7 August 2026 — it is a gradual reward taper keyed to the fraction of the cap.** The window reopened exactly as this entry predicted it would: depth roughly doubled (mean death streak 222.0 after the 7 Aug Kernel craft) and Corporate Network's cap is 210, so the deep end of every run now sits past it.

Measuring **median** credits per enemy level by streak band, in both zone eras:

| fraction of cap | Small Business (cap 126) | Corporate (cap 210) |
|---|---|---|
| 0.0–0.75 | 100% of peak | 100% of peak |
| ~0.8 | 100% | 97.8% |
| ~0.9 | — | 83.9% |
| ~0.95 | 88.9% | 83.9% |
| 1.05 | — | 83.5% |

The taper onset tracks the **fraction of the cap**, not any absolute streak — which is the discriminant this entry asked for, and it holds across a zone change that moved the cap 126 → 210. Rewards are flat to ~0.75–0.8 of the cap, then decay to ~84% of peak. It is a soft taper, not a cliff, and it does not zero out.

Two method notes, both of which bit during this analysis:

- **Use the median, not the mean.** The mean-per-band read showed erosion beginning around streak 140 (0.67 of cap) and decaying smoothly, which would have falsified the fraction-of-cap hypothesis. That was credit-drop skew, not signal. The median shows a flat plateau to 0.76 and a clean step down.
- The capture's cap values are **5% above** the ones recorded here on 27 July (126 vs 120, 210 vs 200) — exactly +5% in both zones. Something grants a streak-cap bonus; nothing in the workspace models it. Not resolved, and not load-bearing for the taper result, which is computed against the capture's own values.

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

## What steps the fight tick? (added 1 August 2026)

The death-clock cadence is tight within an era (sd ~0.01) but has **era-stepped
−4.5% across five days**: daily medians 4.873 → 4.750 → 4.788 → 4.605 → 4.641 →
4.666 over 27 Jul–1 Aug (`mechanics.md` §14 re-read). Ruled out so far:

- **Rounds/fight** — r = 0.42 across daily pairs, and 29 Jul (most rounds,
  39.1) sat at mid cadence while 30 Jul (31.9) is the lowest.
- **Attack speed** — the +9.9% equip test moved it 0% within-window (27 Jul).
- **The shell equip** — 4.644 pre vs 4.655 post across the 20:10Z boundary.

Candidates untested: a game patch, zone/enemy-class composition of the run,
homelab/hardware side effects, player level. The economic law is unchanged
(within-era the tick is fixed, AtkSpd buys no fights/hour), but
`FIGHT_CADENCE_S` is now **era-local** (4.65, re-fit 1 Aug) and its register
check reads a trailing 50-death window so the next step fires DRIFT. If a step
ever aligns with a single change-point, that change identifies the mover — the
daily-median table is one `fight_cadence()` group-by away.

### 17. Events — a player-reported income system nothing in the workspace models (added 6 Aug 2026)

The ~136K-chip inflow of 5–6 Aug came from an **Event**: mass-player
collaborative, limited-time, contributions via gathering or hacking, manual
queueing required (the player queued gathering). Nothing in any capture,
doc or audit check models these. Unknown: (a) payout structure — this one
paid chips; do events pay hackcoin or credits, and is pay proportional to
contribution or bracketed? (b) frequency/schedule — is there a calendar the
client exposes? (c) **is event state visible in the capture?** If a binding
exists, `audit` should price an open event exactly like the contract board
(it is the same shape: attention-gated, expiring income). (d) does event
gathering conflict with harvest-contract gathering (one active gather?).
One capture taken while an event is open and queueable settles (c) and
likely (a); the player noticing the next event's announcement settles (b).


**Lead, 6 Aug 2026 (found during the public-repo audit):** `currentPlayer` carries `game_tick_ms = 5000` / `tick_seconds = 5` — a server tick constant sitting 7% above the measured 4.65 s/fight cadence era. If fight cadence is derived from this tick minus some processing offset, the era-steps may be server-version steps (`server_version` is also in the capture and changes on deploys — check whether cadence era boundaries coincide with `server_version` changes across the capture archive).

### 18. Why did our hit rate fall in every matched streak band across the Router swap?

`router-ab-2026-08-06` (closed KEEP 7 Aug, +10.0) changed no Accuracy, yet our
per-attack hit rate fell in **all four** matched streak bands: 80.7→80.0 (24–42),
79.3→77.4 (60–85), 78.2→76.1 (86–105), 76.7→74.6 (106–130). A consistent
0.7–2.1pp drop across every band is not noise-shaped, and the fitted hit law
`logit(hit) = -0.164 + 1.420*ln(Acc/Eva)` predicts no move from this swap.
Candidate explanations, none tested: (a) enemy *composition* shifted within each
band as the build reached deeper streaks (band is streak, not enemy class — the
segment-by-the-natural-categorical rule applies and has not been run here);
(b) the same-window VLAN +1% Def / hardware changes carried an Accuracy-pool
side effect not read out of the capture; (c) enemy evasion scales with something
other than streak. Discriminant: re-segment the post window by **enemy class**
within one band and compare like-for-like; if composition explains it, the
per-class hit rates should be flat across the boundary. Until then, treat
pooled post-equip hit rates in this era as composition-contaminated.

**Evidence for (a), 7 Aug 2026 — the sign flipped.** `shell-ab-2026-08-07`
pre-registered prediction (6) as the discriminant for this question: Acc +4.2%
against Eva +5.8% makes the fitted law predict hit rate **down ~0.4pp** at
matched band. Observed within-band pre→post: 79.9→80.1 (24–42), 77.3→78.5
(60–85), 76.2→77.7 (86–105), 74.5→76.0 (106–130) — **up in all four bands,
by +0.2 to +1.5pp.** So the law missed by ~1–2pp here in the *opposite*
direction to the Router window's 0.7–2.1pp shortfall. Two windows deviating
by a similar magnitude with opposite sign is the shape of a band-composition
effect, not of a broken law, which promotes (a) and demotes (c). The
discriminant named above — re-segmenting one band by enemy class — is still
the test that would close it, and is now the cheapest open item here.

Note the pooled headline does *not* show this: `ih.py ab` printed 72.9% vs a
73.3% baseline, i.e. −0.4pp, appearing to confirm the prediction exactly. That
pooled figure compares against the **old-Payload** `baseline_hits`, not this
experiment's own pre window, and `experiment_mechanism` already carries the
comment explaining why pooled hit rates are confounded by streak composition
alone. Grade prediction (6) on the bracket table, never on that line.

### 19. Why did rounds per fight RISE across a swap that raised hit rate? (added 7 Aug 2026)

`shell-ab-2026-08-07` pre-registered prediction (5): rounds/fight flat within
±2% at matched band, offered as a discriminant against the Router window's
Attack Speed confound, since this swap changed no Attack Speed. It **missed**:
25.5→26.2 (+2.7%), 29.9→30.1 (+0.7%), 32.9→34.4 (+4.6%), 38.7→40.1 (+3.6%).

The miss is not a selection artefact — the obvious candidate was the mechanism
table conditioning on `victory`, but win rate is **100% in both arms in all
four bands** (deaths occur past streak 200, well beyond the deepest bracket at
106–130), so nothing is being selected away. Checked 7 Aug 2026.

What makes it interesting is that hit rate rose in the same bands (§18). More
hits per round with the same attack speed should *shorten* fights, so two
measured quantities are pulling opposite ways. The leading candidate is
**Thorns −40%** across this swap: if reflected damage is a non-trivial share of
kill throughput at these depths, losing 40% of it lengthens fights regardless
of hit rate. That is a hypothesis, not a fit — Thorns' offensive contribution
has never been measured, and `CRAFT_WEIGHTS` prices it as defensive.

Why it matters beyond bookkeeping: rounds/fight is currently used as an
AtkSpd discriminant, and this window shows it moving with no AtkSpd change, so
it is **not clean for that purpose**. It also bears on the live Router
candidate `Bulwarked Router of Thorns` (+19.5, with Thorns +10.6 carrying more
than half the delta) — if Thorns carries unpriced kill-speed value the weight
is low, and if the rounds effect is something else entirely it is unaffected.
Do not re-weight on one observation. Discriminant: a CI/CD pair differing only
in Thorns at matched depth, reading rounds/fight rather than streak depth.

## par.20 — Does the gear-flat homelab addend scale with the pool, or with hardware alone? (opened 8 Aug 2026)

`composed_stat_total`'s gear-flat branch was corrected on 8 Aug 2026 to
`(equipment_flat + homelab) × (1 + equipment_pct + hardware)` after the `MODEL`
self-check caught it at +0.35% on corruption (`mechanics.md` §13). The
correction is exact on the one observation available, but **corruption is the
only gear-flat stat that has ever carried a non-zero `homelab` across 159
captures, and its `equipment_pct` is 0** — so the data cannot separate

- `(flat + homelab) × (1 + equipment_pct + hardware)`  ← what is implemented, and
- `flat × (1 + equipment_pct + hardware) + homelab × (1 + hardware)`

which differ by under 0.01 corruption today and would only diverge if a
gear-flat stat ever picks up an `equipment_pct` term. Low stakes, recorded so
the regime is not forgotten if it stops being low.

**The bigger claim wanting a second observation** is the size, not the form:
the reading says the game credits the raw fraction as a flat addend, so
"Increases Corruption by 0.5% per level" delivers **+0.005**, ~90× less than
the description. If that is right, every gear-flat homelab upgrade is worth
buying for progress points and for nothing else.

**Discriminant, already queued as an action:** Malware Sandbox L2. It predicts a
corruption total of **90.3639**; the pool reading predicts **91.00**; a
description-faithful reading (0.5%/level of the realized stat) predicts ~90.80.
The next capture after that purchase settles it, and `validate_stat_totals`
re-checks it automatically on every capture, so a wrong form cannot stay quiet.

## par.21 — Is `CRAFT_WEIGHTS_FLAT["ArmorPen"]` ~35% too high relative to Regen? — **RESOLVED 9 August 2026: yes, ~34%. Refit 0.068 -> 0.045.**

The 12-run block below was run and read **-11.22 ± 1.76 streaks**. Pooled with
the 8 Aug craft pair the weight fits **0.045 ± 0.006**: the two pairs agree at
0.99σ and the applied 0.068 sits **3.58σ** outside. β_ArmorPen = 0.132
streaks/score-pt against Regen's 0.200.

**The independent corroboration matters more than the fit.** The 29 Jul
damage-law measurement — a different instrument entirely, `dmg = Atk*K/(K+Def-AP)`
— priced ArmorPen at **0.044–0.051**, and said so in the `assumptions` register
while the applied value read 0.068. Nothing read the two together for nine days.

**Still open:** both depth pairs ran in Data Center at our ArmorPen ~1,029, and
the damage law is convex, so value per point rises as ArmorPen approaches enemy
Defense. The fit is regime-local. The Corporate Network extension below is still
unrun and is still the cheapest test of whether any β generalises across zones.

### Original statement (8 Aug 2026)


The 8 Aug Analyzer pair (`decision-log.md`) is the second family-level
score→depth measurement in the archive. The bundle moved **+75.5 raw score
(+69.6 ex-suspect) for +9.95 ± 1.54 death streaks** — **7.6 score/streak raw,
7.0 ex-suspect** — against Regen's fitted **~5.0** and Barrier's **≥23**.

ArmorPen carries **81%** of that delta (+61.1 of +75.5), so if the remaining
terms convert at anything between Regen's rate and Barrier's, ArmorPen's own
conversion brackets to roughly **6–9 score/streak**. Needing ~1.5× more score
per streak than Regen means the 0.068 weight is **over**-valued relative to it
by something like a third.

**Deliberately NOT refitted.** One mixed bundle is not a fit, and the two worst
constants this workspace has shipped (`CRAFT_WEIGHTS_FLAT["Barrier"]`,
`CRAFT_WEIGHTS_PCT["Acc"]`) both came from confident numbers derived off thin
evidence. The observation is recorded so the next pair can extend it rather than
rediscover it.

**Discriminant:** a CI/CD pair differing ONLY in ArmorPen at matched depth, the
same design par.15 specifies for Barrier. Cheap to bundle — the two pairs share
a control arm, so a 15-run Barrier block plus one extra ArmorPen arm settles
both families in a single day's budget.

**Lever identified 9 Aug 2026, and it is better than par.22's Barrier one.**
`ihlib.probe_levers` ranks owned swaps by purity (target-family score movement
over *signed* other movement). The Analyzer slot supplies two clean arms
against the equipped `Shielded Analyzer of Disintegration`:

| arm | ΔArmorPen | signed other | abs other | purity |
|---|---:|---:|---:|---:|
| `Resilient Analyzer of Decay` | −61.1 | −6.6 | 61.8 | 9.3 |
| `Targeted Analyzer of Light Speed` | −61.1 | −9.2 | 27.8 | 6.6 |

**Run Light Speed as the primary arm despite its lower purity.** Decay's
signed −6.6 is 61.8 of absolute movement very nearly cancelling, so its
subtraction step depends on several families' βs all being right at once;
Light Speed cancels 27.8 → 9.2 and carries far less model dependence. Purity
ranks on the signed figure because that is what par.22 used, but the
cancellation is the thing to check before trusting it — which is why
`probe_levers` returns `other_abs` alongside.

**Power, in par.22's framing.** At β_ArmorPen = 0.200 (converting like Regen)
the swap predicts ≈ **−14.0** streaks; at par.21's reading β ≈ 0.13, ≈ **−9.7**.
Separation ~4.3 streaks against SE 1.17 at 6 runs/arm — **~3.7σ**, decisive on
a 12-run block. Both arms are now held by `RESERVED_PROBES`; before the fix
Light Speed was position 5 on the decompile list.

**Reserved in code as of 10 Aug 2026.** Both arms are held by name in
`RESERVED_PROBES` — `locks` listed them for decompile that morning, because
the ArmorPen reservation had concluded on the weight fit and this extension
was backed by nothing but the paragraph below. A replication is reserved by
NAME, not by family: re-ranking substitutes different arms and answers a
different question, and on that capture it would have picked
`Uncatchable Analyzer of the Bastion` — signed purity 50.8 off 67.3 of
absolute movement, exactly the cancellation case argued against above.

**Second, free reading already available:** re-run the same two Analyzer arms in
Corporate Network. The zones differ by ~30 streaks for this build, so if the
conversion is regime-local the two zones will disagree, and if it is a property
of the stat they will not. That is one extra pair of runs and it tests whether
any of these conversions generalise outside the regime they were fitted in.

## par.22 — The par.15 Barrier test was mis-specified and is respecified here (8 Aug 2026)

par.15 has stood since 7 Aug asking for "two arms differing ONLY in Barrier at
matched depth, full 15-run block". Pricing that design rather than restating it
shows **it could not have been satisfied by any number of runs**, which turned
the matching `PENDING_REFITS` row into a permanent home for a constant everyone
agrees is wrong.

**1. It asked for the wrong parameter.** A *conversion* (score per streak) is
`ΔS / Δdepth`. Under the working hypothesis — Barrier buys ~no depth — that is
division by zero: unbounded, and only ever a lower bound (hence "≥23", never a
value). Estimate the **reciprocal**: depth yield **β = streaks per unit score**,
which is finite and tightly estimable *especially* at zero effect. The weight
correction is `β_family / β_reference`, so **β = 0 ± small is the answer**, not a
failure to obtain one. This reparameterization applies to par.21 (ArmorPen) too:
β_Regen ≈ 0.20, β_ArmorPen ≈ 0.13 streaks per score point.

**2. Perfect isolation is not available and was never needed.** No owned gear
swap isolates Barrier — the purest is Daemon `Shielded Daemon of Bastion` →
`Immortal Daemon of Rending` at **Barrier −49.0 score against 11.9 of signed
other movement** (AtkSpd −6.6, Thorns −8.6, CritDmg +2.1, AtkDmg +2.1 …). The one
pure lever is **Packet Shield**, a `damage_barrier`-only hardware track at
+0.005 pool/level — but its next level costs 7.89K chips against a 6,095 balance
and hardware cannot be sold back outside the monthly reset. Subtract the other
families at their own βs and state the model dependence; that residual roughly
√2's the error and leaves the test decisive.

**3. The 15-run floor was sized on the wrong quantity.** It was justified as "a
near-zero effect fit, so it does not qualify for an 8-run tranche" — sizing the
block on the effect previously *observed* (~0) rather than on the separation
between the hypotheses being distinguished. **Power is about the difference you
need to detect, not the one you happened to see.** Measured per-run SD is **2.02
streaks** (df=44, arms grouped by stat vector — the 9.78 you get grouping by
`gear_set_id` is contamination, since that id is reused across blocks with
different gear).

**Respecified design — one 12-run block, 6 per arm:**

| hypothesis | predicted Δ (streaks) |
|---|---|
| Barrier converts like Regen (5.0 score/streak) | **−11.5** |
| Barrier converts at ~0 (par.15 working hypothesis) | **−1.7** |

SE at 6/arm is **1.17**, so the two sit **~8σ** apart. It is decisive at 8 runs
(6.8σ) and still decisive at 6 (5.9σ). β_Barrier lands with SE ≈ 0.024 streaks
per score point — about 12% of β_Regen — which is a tight enough bound to either
zero the weight or scale it, and **closes the `PENDING_REFITS` row either way**.

**Free extension, +2 runs:** re-run both arms in Corporate Network. The zones sit
~30 streaks apart for this build, so if β is regime-local they disagree and if it
is a property of the stat they do not. That tests the one assumption every β in
this workspace rests on.

### RE-OPENED 10 Aug 2026 — the block ran, and it ran off the end of the scale

The 12-run block above was executed on 7–8 Aug and closed the `PENDING_REFITS`
row at β_Barrier = 0.041 ± 0.024. **That row is re-opened**: the block was run
in Corporate Network at an enemy-level cap of **5,769**, and

| arm | Barrier / Regen | runs | loss enemy level | vs cap 5,769 |
|---|---|---|---|---|
| A (high Barrier) | 5,900.8 / 1,221.0 | 6 | 4,991–5,129 | clear |
| B (low Barrier) | 5,153.6 / 1,844.6 | 6 | 5,841–6,106 | **all six at or above** |

Past the cap the enemy stops getting harder, so arm B's 255.2 is a **lower
bound**, not a reading. The censoring is perfectly asymmetric and it binds on
the arm carrying *less* Barrier — so it understates how well low Barrier does
and therefore **overstates Barrier**. `β = 0.041` is a **ceiling**, the applied
weight 0.0088 is a ceiling, and the true value may be zero. The information the
truncation destroyed is not recoverable from the banked runs.

**Why it was invisible:** `final_streak` and `enemy_level_cap` travel in the
same sim payload and nothing read them together until `cicd_rows` gained a
headroom check on 10 Aug. It found this on its first run.

**Re-run design — unchanged except for the zone.** Same two arms, 6 runs each,
in a zone whose cap clears their loss levels. `ih.py sims` now prints the
headroom per zone for the newest pair; **check it before spending the runs**,
because the cap tracks the player and a zone that was clear last week may not
be. Read arm B's uncensored mean against 255.2 — the gap between them is the
size of the bias, and it also calibrates `SIM_CAP_HEADROOM_WARN`, which is
asserted.

**Supporting, not a fit:** the 10 Aug Daemon pair dropped **2,604.8 Barrier**
and 74.9 Thorns and *gained* +6.83 ± 0.91 streaks, uncensored, in the current
regime. Many stats moved, so it isolates nothing — but it is hard to reconcile
with Barrier being worth much.

## par.23 — What is `post_combat_heal` worth? (opened 10 Aug 2026)

**Nothing prices it, and it is the only stat in that position.** Sweeping every
homelab effect key against `statsBreakdown`, exactly one names a stat the game
tracks and `CRAFT_WEIGHTS` does not: `post_combat_heal`. Every value carried
under the `combat_stat` schema is priced, which is why this stayed invisible —
the gap is in effects that deliver a stat without using that key at all.

**It is not a rounding error.** `post_combat_heal` sits at **14,655** against a
Max HP of **52,585** — the build already restores ~28% of its health bar after
every fight, from player level alone. **Thermal Budget** (Power & Cooling Rack,
L0/25, +1% of Max HP per level, **~200M credits and zero hackcoin**) would add
+526 per level, or +13,146 at L25 — roughly doubling it.

**Why it matters more than its score suggests.** The standing bottleneck model
has attrition across long streaks as #1, and `current-state.md` already names
recovery *systems* rather than more gear regen as the next lever. Post-combat
healing is the purest form of that: it acts between fights, so unlike gear
Regen it is not competing with in-fight drain and is not subject to the
overheal capping that produced the 28 Jul diminishing-returns amendment.

**Do not fix this by inventing a weight.** `CRAFT_WEIGHTS_FLAT["Barrier"]` and
`CRAFT_WEIGHTS_PCT["Acc"]` were both confident numbers off thin evidence and
are the two worst constants this workspace has shipped. `ih.py homelab` now
prints `UNMODELLED[post_combat_heal]` instead of `0.000` and never truncates
the row out of the QUEUE list.

**Unblock.** A live before/after on Thermal Budget levels, read as beta
(streaks per point of post-combat heal) per par.22. The CI/CD Pipeline cannot
run it — it customises gear and zone, not the homelab — and the Software
Profiler cannot see it either, since it runs single full-HP fights and this
stat only pays across a streak. So it is a live pre-registered window, and the
buy is credit-only, which makes it cheap to start and impossible to undo.

**Discriminant before spending 25 levels:** buy L1, and check whether the
`post_combat_heal` total moves by +526 (1% of Max HP, description-faithful) or
by +0.01 (the raw-fraction addend that Corruption turned out to be — incident
#26). `validate_stat_totals` re-checks the composition on every capture, so a
wrong form cannot stay quiet; but the two readings differ by ~52,000x and only
one of them is worth a queue slot.
