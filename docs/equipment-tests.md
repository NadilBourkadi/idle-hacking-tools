# Equipment Test Results — last updated 27 July 2026

**Purpose:** Preserve exact measured evidence from equipment trials without converting noisy A/B data into invented formulas.

## Test 1 — Aggressive Kernel of Renewal versus Hearty Kernel of Decay

### Item delta

| Stat | Hearty Kernel | Aggressive Kernel | Delta |
|---|---:|---:|---:|
| Max HP | 6.93% | 12.46% | +5.53% |
| Regeneration | 53 | 64 | +11 |
| Defense | 10.02% | 2.56% | -7.46% |
| Evasion | 0 | 3.46% | +3.46% |
| Accuracy | 1.57% | 0 | -1.57% |
| Attack Speed | 2.09% | 0 | -2.09% |
| Attack Damage | 0 | 0.80% | +0.80% |
| Corruption | 4 | 0 | -4 |
| Thorns | 0 | 5 | +5 |

The swap increased observed maximum HP from roughly 9,980-9,993 in the prior baseline losses to 10,510-10,524, approximately +5.3%.

### Unique post-swap losses

The two Mirrored Network Monitor exports describe the same fight and were deduplicated.

| Metric | Mirrored Network Monitor | Rooted Backup Daemon |
|---|---:|---:|
| Enemy level | 1163 | 1170 |
| Streak ended | 89 | 90 |
| Starting HP | 4,075 / 10,524 (38.7%) | 7,044 / 10,510 (67.0%) |
| Rounds | 23 | 33 |
| Player hits | 31 | 28 |
| Miss events (`pm=true`) | 5 | 15 |
| Modelled hit rate | 86.1% | 65.1% |
| Player direct damage | 11,573 | 9,873 |
| Total player `prg` | 2,072 | 2,719 |
| `prg` per round | 90.1 | 82.4 |
| Enemy direct damage | 4,628 | 7,899 |
| Player thorns/corruption damage taken | 1,229 | 1,183 |
| Enemy HP remaining | 1,389 / 14,031 (9.9%) | 1,808 / 12,673 (14.3%) |

Working hit-rate model: `sum(ph) / (sum(ph) + count(pm=true))`. Exact event semantics remain unknown.

### Prior high-level baseline losses

| Enemy | Level | Streak | Starting HP | Rounds | Modelled hit rate | `prg` / round |
|---|---:|---:|---:|---:|---:|---:|
| Explosive Network Monitor | 1163 | 90 | 3,031 / 9,993 (30.3%) | 13 | 77.8% | 140.5 |
| Fortified VPN Endpoint | 1180 | 92 | 2,092 / 9,980 (21.0%) | 19 | 73.1% | 153.9 |
| Mirrored VPN Endpoint | 1179 | 92 | 4,923 / 9,967 (49.4%) | 34 | 56.1% | 93.4 |

These are not matched enemies/modifiers, so they cannot establish a Defense or Regeneration formula. They do show that the post-swap sample did not improve the observed streak range and that +11 listed Regeneration did not guarantee higher realised `prg` per round.

### Decision

Reject the Aggressive Kernel as the main streak item and restore/prefer Hearty Kernel of Decay.

### Durable learning

- Defense, Accuracy and Attack Speed protect sustain indirectly through lower damage per hit and shorter fights.
- Max HP is a buffer, not recovery.
- Listed Regeneration must be validated using combat-log `prg`; its realised value varies by encounter and round state.
- A trade of +11 Regeneration and +5.53% Max HP for -7.46% Defense, -1.57% Accuracy and -2.09% Attack Speed is empirically unfavourable in the current build.
- Confidence: directional, not formula-level, because the sample is small and enemies/modifiers were not matched.

## Test 2 — Fortified Firewall forced-suffix Augment

### Before

- Rare, item level 859;
- 3 prefixes / 2 suffixes;
- 26/26 Stability.

### After

- Epic, 3 prefixes / 3 suffixes;
- 25/26 Stability;
- added `of Sandboxing` T9: +25 Damage Barrier;
- an existing `of Sandboxing` suffix remained, so duplicate affix families are directly observed.

### Main-set comparison against Brutal Firewall of Perpetuity

| Stat | Delta |
|---|---:|
| Max HP | +3.32% |
| Evasion | +8.60% |
| Accuracy | +1.20% |
| Damage Barrier | +47 |
| Defense | -15.23% |
| Regeneration | -52 |
| Attack Damage | -2.01% |

### Decision

Abort. The Augment did not supply Regeneration, the item is now full, and further tier work cannot repair the missing sustain package. Random Prune/re-Augment is not resource-efficient.

## Testing methodology learnings — 22 July 2026 (Storm Daemon A/B)

- **Death streak is a low-power metric.** Session variance was ±8 streaks (84–104 over 8 baseline runs); a 2-streak test only detects revolutionary changes. Judge *crafts* on mechanism metrics — rounds/fight and damage/round at matched enemy level, damage taken/fight, attrition-onset streak (first start <90%) — which moved detectably (−5%, +8%, −6.5%, +5 streaks) while the death streak showed nothing.
- **Baselines must be same-session.** Player levels (+8 = +40 heal, HP/def growth) and completing homelab jobs shift stats within hours; compare against streaks from the same session and log completed jobs as confounds.
- **Model components validated so far:** tier-midpoint landing assumption (4/4 lines at/above mid), independent re-roll on Version Upgrade (6/6), ilvl scaling and cost model (exact). Weakest link: unknown hit-chance formula — the naive +13% output estimate realized as +8% largely through the unmodeled Accuracy interaction. The Hawk instrument streak (open questions §7) is the cheapest fix; the Hacking Simulator (homelab 10) is the real one.

## Test — Bastioned Payload of Perfect Strike A/B (23 July 2026)

**Swap:** Enduring Payload of Armageddon (Acc +3.7%, AtkDmg +28.2%, AtkSpd +6.2%, CritDmg +7.4% implicit, ArmorPen +51) → crafted Bastioned Payload of Perfect Strike (Acc +25.4%, CritCh +9.8%, Corrupt +11, AtkDmg +7.5% implicit). Player Accuracy 5,057 → 5,816.

| Metric | Old Payload | New Payload |
|---|---|---|
| Death streak, mean (same-loadout window) | 96.2 (n=12) | **98.6 (n=9), delta +2.3** |
| Death streaks, last four | — | 100, 101, 101, 101 |
| Deep-streak hit rate | 70.1% (n=164, eva ~2,500) | **76.9% (n=8,021, eva ~2,700–3,700)** |
| Rounds/fight, streak 24–42 | 18.1 | 20.7 (+14%) |
| Corruption share of output | — | 1–18% per fight |

**Decision: KEEP.** Evidence quality: the strongest A/B to date — cross-capture tracker, all 9 deaths pre-contamination (VLAN Rules +1% Def completed after the last death). Durable learnings: hit rate is measurable at scale via the Detailed Logs checkbox; accuracy moves the death ceiling where raw tempo does not; the (acc, eva → hit%) dataset now spans two accuracy levels for hit-formula fitting (open questions §7/§8).

## Test — Citadel Shell of the Phoenix A/B (23 July 2026)

**Swap:** Overclocked Shell of the Monolith (Def +28.4%, Barrier +221, MaxHP +7.26%) → crafted Citadel Shell of the Phoenix (Eva +20.0%, Regen +46, Def +12.21%, MaxHP +8.06%). A deliberate mitigation→recovery trade targeting the primary attrition bottleneck.

| Metric | Old Shell (payload era, n=14) | New Shell (n=10) |
|---|---|---|
| Death streak, mean | 97.3 | **104.3 (+7.0)** |
| Death streaks, last four | 98, 97, 95, 92 (declining) | **108, 109, 110, 111** |
| Attrition onset (first start-HP <90%) | streak 60–76 | **streak 78–90** |
| Realized regen, streak ≥60 | 130.6 prg/round | **167–177 prg/round (+28–36%)** |
| Gross damage in/fight, streak 60–85 | 4,749 | 5,154–5,353 (+8–13%) |
| Net drain/fight, streak 60–85 (≈) | ~690 | **~155–450** |
| Hit rate (control — Shell touches no Acc) | 77.9% | 77.6% |

**Decision: KEEP.** Confounds: VLAN Rules +1% Def landed mid-test (5/10 deaths after; segmented, conclusion holds either way); player level 955→963; Malware Injector +15 levels pre-boundary. Methodology notes: (1) `damage_taken` is **gross** incoming (verified) and Σ`pbs` is probably per-round barrier absorption (working model; the full accounting identity does not close exactly — see data-dictionary) — never compare `damage_taken` across a mitigation↔recovery trade without netting out prg and absorption (keep-rule clause amended at 4/10, logged pre-outcome); (2) the tracker banked 1,051 post-equip fights with full round detail, zero manual bookkeeping; (3) one burst-shaped death (76% start-HP, Trojan Wall eff_acc 5,899) shows the thinner Def/Barrier flank exists but did not dominate.

## Test — 27 July bundle: hardware reallocation + Analyzer + Router (27 July 2026)

Four changes shipped in ~2 hours with no staging, by explicit player priority (progression over attribution). The death record still segments cleanly at the equip boundaries, all in **Small Business Server**, same player level band.

| Window | Deaths | Mean |
|---|---|---|
| Pre-bundle (14:50–15:36) | 110, 108, 114, 110, 109, 112 | **110.5** |
| Post hardware + Analyzer (15:46–16:38) | 121, 113, 122, 124, 123, 131 | **122.3 (+11.8)** |
| Post Router (16:49–17:00) | 133, 129 | **131.0 (+20.5)** |

**+20.5 death streaks — by far the largest measured gear effect in the project** (previous best: Citadel Shell of the Phoenix at +7.0).

Mechanism, 2,079 fights with round detail at streak ≥60:

| | pre | post hw+Analyzer | post Router |
|---|---|---|---|
| Realised `prg`/round | 171.3 | 194.7 (+13.6%) | **231.8 (+35.3%)** |
| `damage_taken`/round | 205 | 208 | 229 |
| **Net drain/round** | **33.7** | **13.3** | **−2.8** |

**Net drain went negative** — regeneration now exceeds incoming damage per round in the deep-streak band. That is the whole explanation for a 20-streak ceiling move.

Calibration notes: the hardware step tracked its listed regen gain almost exactly (+13.6% realised vs +14.9% listed); the Router step realised +19.1% against +33.5% listed, at least partly because its window sits at deeper streaks where in-fight regen decays harder (open-questions §11). **Listed Regeneration ≠ realised `prg`** — guardrail holds. Gross intake rising 11.7% post-Router is the deeper streak band, not a mitigation failure: Defense finished the day flat (1,064.3 → 1,067.3) because the hardware reallocation offset the Router's Defense loss almost exactly.

**Decision: KEEP all three.** Revert paths (Aligned Analyzer of Light Speed, Aligned Router of the Undying) stay decompile-locked until re-confirmed against the Corporate Network baseline.

## Test — zone transition, Small Business Server → Corporate Network (27 July 2026)

Not a gear test, but the same measurement discipline and the source of the current baseline.

| | Small Business (post-Router) | Corporate |
|---|---|---|
| Mean death streak | 131.0 (n=3) | **113.1 (n=16)** |
| Credits per enemy level | 8.81 | **11.47 (+30%)** |
| Credits/hr | 9.78M | 11.08M (+13.3%) |
| XP/hr | 35.6M | 33.0M (−7.3%) |
| Chips/hr | 3,207 | 2,889 (−9.9%) |
| Deaths starting >60% HP | 0 of 14 | **3 of 16 (19%)** |

Cost **−17.9 streaks against a predicted −4** — see `mechanics.md` §15 for why the prediction failed (`level_offset` is not additive on enemy level, and enemy level is not a sufficient statistic for difficulty across zones). Reward side beat expectations: zone rewards scale by more than the stated `credit_multiplier` ratio.

**Decision: keep the move.** Caveat: the Small Business baseline is 15 minutes / 204 fights / 3 deaths — only the credits-per-enemy-level figure is solid.

**New standing baseline: 113.1 mean death streak, Corporate Network** (n=16, 17:10–19:30Z). Nothing here compares to a Small Business figure; `ih.py audit` flags any death window spanning a zone change.

**New failure mode logged:** 3 of 16 Corporate deaths start above 60% HP (89%, 100%, 79%), all against 19–23K HP Trojan Wall / Rootkit tanks whose attack damage is *lower* than the attrition-death enemies. Not burst — the build cannot close those HP pools before in-fight regen decays. This is the day's crit sacrifice (51% → 31.5%) appearing as a damage floor, and it is why the next craft target moved from the Firewall to the Aegisbound Driver (CritDmg +81.21%).

## A/B — Resilient Firewall of Perpetuity, `firewall-ab-2026-07-28` (closed 30 July 2026: KEEP)

Pre-declared keep rule: KEEP if mean death streak ≥ 117.8 (baseline 119.8 − 2, n=16 same-loadout deaths); REVERT ≤ 114.8.

| | pre-equip (n=16) | post-equip (n=89) |
|---|---|---|
| Mean death streak | 119.8 | **140.2 (+20.4)** |
| Hit rate | 81.0% (deep-streak baseline) | 79.7% |
| Realized regen/round, streak ≥60 | 260.5 | 284.6 |

**KEEP, decisively — the mean cleared the gate by +22.4 and every one of the last 40 deaths individually exceeds the old baseline mean.** The readout is a **bundle**, stated per the standing rule rather than corrected for: 87 of 89 deaths fall after the VLAN Rules +1% Def homelab segment boundary, and the window contains the 29 Jul Kernel (Assault Kernel of Blight, +37.4) and Daemon (Shielded Daemon of Bastion, +131.5) crafts. Attribution among the four is not possible from this window and does not matter for the decision — no component has a plausible negative sign. The 1.3pp hit-rate drift is consistent with the Kernel/Daemon equips moving Accuracy composition, not with the Firewall's +0.30% Acc.

Consequences: **Brutal Firewall of Perpetuity (ilvl 314) released for decompile** (last pre-craft Firewall, no sole ladder anchors — `of Perpetuity` T1 and `of Immortality` T2 are both archive-covered). **New standing baseline: mean death streak 140.2, Corporate Network** — `ih.py ab` output, 30 Jul capture.

## A/B — Vital Payload of Extinction, `payload-ab-2026-07-30` (open)

Declared 30 July ~21:00Z, before any post-equip data existed. Baseline: the full post-Firewall window (mean **140.2**, n=89, Corporate Network). **KEEP if post mean ≥ 138.2; REVERT if ≤ 135.2** (n=24 deaths). The window is a **declared bundle** with the same-hour 287K-chip hardware package (Packet Shield 14→88, ECC 110→119).

The equip trades Acc −26.4pp affix and CritCh −10.1pp for AtkDmg +34.6pp, CritDmg +17.4pp and Corrupt 16→66 gear-flat — roughly +10–15% net output for worse hit reliability. It is the strongest test yet of the 22 Jul "output does not move the death ceiling" law.

Pre-registered treatment predictions (diagnostics, not gates):

1. **Hit law out-of-sample:** Accuracy stat 10,350 → ~9,186 (−11.2%) predicts per-attack hit rate at the streak-120–159 faces down ~3.8pp (65–68% → 62–64%); pm-flag pooled rate ~79.7% → ~76%.
2. **Corruption law extension:** corruption stat 17.4 → ~71.6 predicts max outgoing corruption ≈ 6 × stat ≈ **430/round** at full stack (was ~104). Confirming extends the verified linear range 50 → ~72; a miss flags non-linearity above 50.
3. **Rounds/fight** at matched streak band down ~10–13%.

Requires **Detailed Logs enabled** in the Hacking panel for round-level data. Revert path: Bastioned Payload of Perfect Strike, decompile-locked until close.

**Profiler pairing (added on the player's point that the Hacking Simulator can A/B directly):** the three mechanism predictions do not need to wait for 24 live deaths. Paired Software Profiler runs — same enemy levels, both Payloads — read them in minutes, and because both arms run under the *post-chip-spend* hardware, the pair **isolates the craft from the hardware bundle**, which the live window cannot. Recipe: **pre-arm with the Bastioned still equipped, 5 runs each at enemy level 1800 / 2100 / 2500, Corporate Network; equip Vital Payload of Extinction; post-arm, same 5×3 runs** (~30 runs, ~3 min against the 5 s cooldown; the userscript banks them automatically, read with `ih.py sims`). The profiler remains blind to attrition (full-HP single fights), so the **death-streak keep rule still gates on the live ledger** — the profiler pair settles the *laws*, the streaks settle the *depth*.

### `payload-ab-2026-07-30` — profiler readout, 30 July ~21:44Z (post-arm only)

10 runs banked (5 × enemy 2100, 5 × 2500; the pre-arm was skipped — the equip happened first, so single-fight deltas vs the 29 Jul runs include the same-day hardware package). Against the pre-registered predictions:

1. **Hit law: HOLDS out-of-sample.** At Accuracy 9,198 (−11.2%), pooled per-attack hit rate (2-attack estimator, n=195) = **63.6% vs ~64% predicted**, and per-face observed rates track the per-face predictions computed from each logged enemy's `effective_evasion` (52–70% range).
2. **Corruption law: LINEAR, range extended 50 → 72 — but my 430/round max was wrong in size.** Avg `pcd`/round per stat point: 5.19× at stat 17.36 vs 4.95× at 71.61 (within 5% — linear). Max tick 611 = 8.5× stat, not the predicted 6×: the full-stack multiple is **side-dependent** (stacks sustained ∝ attacks landing/round; enemy side ~6×, ours 8.5–9×). Per-stack tick ≈ 0.95× stat. Provenance note updated in `ihlib`.
3. **Rounds/fight: −39 to −41%** at matched levels (2100: 56 → 32.8; 2500: 76 → 46.4) — far beyond the predicted −10–13%, because corruption at stat 71.6 is ~46% of total output. Consistent with the Corrupt weight (+50 score ≈ +51% output; observed ≈ +60%): the weight is right-to-slightly-conservative at this stat level.

**Win rate: 1,000/1,000 — zero losses**, including 5×100 at enemy 2500 where the 29 Jul arm won 70–81%. The tank damage-floor failure mode (Trojan Wall / Rootkit / Siege Daemon closing) is gone at these levels in single fights. Regime caveat: all full-HP single fights — **attrition and the death ceiling remain unread; the live-streak keep rule (≥138.2 over 24 deaths) still governs KEEP/REVERT.**

### `payload-ab-2026-07-30` — clean paired profiler readout, 30 July ~21:54Z (pre-arm re-run at matched hardware)

The player re-equipped the Bastioned and re-ran the pre-arm (5×2100 + 5×2500), so both arms now share the post-chip-spend hardware and the pair isolates the Payload swap. This **corrects the attribution in the previous entry**, which compared against the 29 Jul pre-hardware arm:

| level | metric | pre (Bastioned) | post (Vital) | craft-only Δ |
|---|---|---|---|---|
| 2100 | win rate | 500/500 | 500/500 | — |
| 2500 | win rate | **485/500 (97.0%)** | **500/500** | +3.0pp, losses (Trojan Wall ×2, Stealth Worm ×3 logged) → zero |
| 2100 | rounds/victory | 56.8 | 32.8 | **−42%** |
| 2500 | rounds/victory | 70.4 | 46.4 | **−34%** |
| both | avg `pcd`/round per stat pt | 5.06–5.41× (stat 17.4) | 4.57–5.48× (stat 71.6) | linear — re-confirmed within the matched pair |

**Hit law: holds on both arms.** Attack-weighted per-face predictions vs pooled observed: pre **66.2% pred / 66.4% obs** (n=500), post **63.9% pred / 63.6% obs** (n=195). Pooled per-level cells look inverted (post 70.3% at 2100) — that is enemy-class composition, not a law violation; per-face is the honest read.

**Win-rate decomposition at 2500** (correcting the earlier "looks mostly craft" lean): 29 Jul pre-hardware ~76% → **97% from the hardware package alone** (Packet Shield barrier + ECC regen) → **100% with the craft**. The hardware did most of the single-fight survival lift; the craft eliminated the remainder by closing fights ~35–40% faster.

**Ledger note:** the pre-arm re-run put the Bastioned back on inside the live post window (~20:45Z onward; still equipped at the 20:53:50Z capture). The segment is marked in the experiment for exclusion at grading — boundary markers are the Corruption 71.61↔17.36 stat-change records in the stream.

---

### `payload-ab-2026-07-30` — CLOSED: KEEP, 31 July (mean 155.0 over 29 deaths vs gate ≥138.2)

Pre-declared n=24 reached (first-24 mean 154.6); all 29 pre-Firewall-equip deaths counted: mean **155.0, +14.8 streaks over the 140.2 baseline**. Contamination clean: no zone change, cadence held ~4.872 s. Treatment predictions: hit law **held** (pooled 77.5% vs ~76 predicted), corruption law **held** out-of-sample (linearity extended to ~72, 30 Jul profiler), rounds/fight −39–41% at matched levels (profiler; bundles the same-hour hardware package). The 22 Jul "output does not move the death ceiling" law survives only as "this **bundle** moved it" — attribution between craft and hardware not attempted by policy. **New standing death-streak baseline: mean 155.0, Corporate Network — retire 140.2.** Revert path **Bastioned Payload of Perfect Strike released**.

### `firewall-ab-2026-07-31` — DECLARED, equip pending (Predatory Firewall of Immortality)

Crafted 31 Jul, realized **+36.8** vs projected +39.1 — error −2.3, smallest on record, **first craft ever to land inside p10–p90** (era coverage 1/4), on the first projection recorded after the deepen-scale bug fix. Replaces Resilient Firewall of Perpetuity, now **decompile-locked as the revert path**. Baseline = the 29-death post-Payload window (mean 155.0, n=29). **KEEP ≥ 153.0 / REVERT ≤ 150.0 over 24 deaths**; contamination checks: no zone change, cadence ~4.872 s. Pre-registered treatment predictions (full text in `ihlib.FIREWALL_AB_2026_07_31`): incoming direct per landed hit −~9% (Def stat +11.4%), enemy hit rate on us +1.3–1.8pp (Eva stat −4.4%), our per-attack hit +~0.7pp (Acc +3.75pp affix), realized prg/round +2–6% at streak ≥60. The −7.8% MaxHP side makes this window the **first live test of the unmeasured MaxHP weight (0.5)**: KEEP is evidence the weight is not grossly under-priced; REVERT with the mitigation predictions landing means Max HP is worth far more than 0.5. Declared bundle: the pending 112.8K-chip equal-marginal spend lands inside the window.

---

### `firewall-ab-2026-07-31` — CLOSED: KEEP, 31 July evening (mean 167.6 over 34 deaths vs gate ≥153.0)

Pre-declared n=24 passed (first-24 mean 168.1); full window: **mean 167.6, +12.5 streaks over the 155.1 baseline**, window minimum (154) just under the old mean. Contamination clean: no zone change, cadence held. **All four pre-registered predictions landed**: (1) per-round gross damage −10/−11% at the deep bands vs −9% predicted for the direct channel (bundled with the 107K-chip package); (2) deep-band hit rate +0.7pp — the hit law's prediction to the decimal; (3) realized regen/round 244.2 → 263.0 (+7.7%, top of the +2–6% band); (4) the −7.8% MaxHP side never bit — **the first live MaxHP-weight test resolves: 0.5 is not grossly under-priced in a mitigation-compensated trade**. Logged anomaly (not predicted): shallow-band gross fell 24–47%, far beyond the Defense law — stack-exposure-vs-fight-length hypothesis in `open-questions.md`. Revert path **Resilient Firewall of Perpetuity released**. **New standing death-streak baseline: mean 167.6, Corporate Network — retire 155.0.**

### `shell-ab-2026-07-31` — DECLARED **before the craft ran** (Shielded Shell of Segmentation)

Strongest pre-registration yet: predictions written before any craft roll existed. Contract (deepened): of Rejuvenation T6→T1 → of Segmentation T5→T1 → of Reprisal T4→T3 → Vital T9→T8; **mean +35.5, p10 +24.8, p90 +44.6, P(Δ>+5) 99.9%, worst −1.35** vs the equipped Citadel Shell of the Phoenix (41.5). Baseline = the 34-death post-Firewall window (167.6). **KEEP ≥ 165.6 / REVERT ≤ 162.6 over 24 deaths.** Pre-registered: Barrier drawdown +1.00× the crafted affix per fight; `ptd` +0.97× the Thorns affix per enemy landed hit; enemy hit rate on us +2.5–3pp (Eva −7.4% stat — the priced cost); and the **reverse MaxHP probe** (+7% max_hp after the last window's −7.8%). Declared bundle: the 110.7K-chip equal-marginal spend. The crafted item renames on promotion — match the Shell-slot stat-change markers in the stream and update the experiment's `item` at grading. Citadel Shell of the Phoenix becomes the locked revert path on equip.
