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
