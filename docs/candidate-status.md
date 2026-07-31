# Candidate and Craft Status — 31 July 2026

> **Every ceiling number below the main-set table is stale and has been left in place only as history.** Two things invalidated them on 28 July: `COMPILE_FLOOR` moved 8 → 2 (every projection rises ~11–13 points, which is more than `UPGRADE_BAND` itself, so past *rankings* changed, not just scores), and the inventory went 9 → 45 items on a large drop. **Regenerate with `python3 scripts/ih.py potential` — do not read a number off this page.**
>
> Read `ih.py potential`'s new `from:` decomposition line, not just the score: two of the three top-ranked candidates on 28 July were artifacts of a Corruption weight fitted on n=1 and extrapolated 2.3× past its observed range, and an Accuracy weight measured as saturated.

## Main set (all eight slots)

| Slot | Item | Origin |
|---|---|---|
| Payload | **Vital Payload of Extinction** | crafted 30 Jul (realized **+64.7**, scale-corrected grade), A/B **closed KEEP 31 Jul** (+14.8 streaks, bundle) — revert path Bastioned Payload of Perfect Strike **released** |
| Firewall | **Predatory Firewall of Immortality** | crafted 31 Jul (realized +36.8, first in-interval craft), **A/B closed KEEP 31 Jul evening** (167.6 over 34 deaths, +12.5) — revert path Resilient Firewall of Perpetuity **released** |
| Shell *(pending)* | **Shielded Shell of Segmentation** — *craft approved 31 Jul evening, §10.1 contract in decision-log* | deepened contract mean +35.5 / p10 +24.8; replaces Citadel Shell of the Phoenix, which becomes the **locked revert path for `shell-ab-2026-07-31`** on equip. The Corrupt monsters (Analyzer +69.9, Kernel +63.0) are **held for the CI/CD Pipeline** (homelab 12) — their Δs rest on Corruption ~2× past the verified stat ~72 |
| Analyzer | Targeted Analyzer of Light Speed | crafted 27 Jul (+24.9), A/B KEEP |
| Shell | Citadel Shell of the Phoenix | crafted 23 Jul (+22.6), A/B KEEP |
| Driver | Aegisbound Driver of Cataclysm | crafted 27 Jul (**+16.7**), A/B **closed KEEP** 28 Jul (+6.4 death streaks) |
| Router | Titanic Router of the Undying | crafted 27 Jul (**+38.7**), A/B KEEP |
| Daemon | Shielded Daemon of Bastion | crafted 29 Jul (realized **+131.5**, best on record) |
| Kernel | Assault Kernel of Blight | crafted 29 Jul (realized +37.4) |

**All eight slots are now contract crafts** (Kernel and Daemon fell 29 Jul).

## Next craft — RESOLVED (both former contenders crafted 29 Jul; Vital Payload of Striking approved 30 Jul — see decision-log)

### (historical) Next craft — two contenders, deliberately held

Scores below are post-`COMPILE_FLOOR`-fix and "adjusted" strips the Corruption and Accuracy weights that `ih.py assumptions` flags as unreliable:

| candidate | raw Δ | adjusted Δ | case |
|---|---:|---:|---|
| Untouchable Payload of Lightning | +18.7 | **+19.9** | *gains* when adjusted — its −10.5 Accuracy penalty is fake. AtkSpd +19.0, AtkDmg +7.8. The output answer |
| Assault Kernel of Corruption | +26.0 | +7.6 | Def +9.1 with **no sustain cost** — the only candidate that spends nothing. The mitigation answer |

Rejected on the sustain guardrail regardless of score: **Targeted Router of Immortality** (+14.1, but Regen −20.9% at loadout) and **Deadeye Kernel of Containment** (Regen −14.7%).

**Held on purpose.** The Firewall's +34% regen may have moved the bottleneck from attrition to closing tank matchups, which changes *which* of the two is correct — the one case where sequencing is justified. Read `firewall-ab-2026-07-28` first.

## Inventory — all 9 items, ranked by ceiling delta vs equipped

Regenerate with `python3 scripts/ih.py potential`. Figures below are from the
21:07Z capture on **archive-wide tier ladders** (`crafting.md` §12.1.1, 58
captures / 582 tier observations), with the Snapshot Backups 10% Stability
preserve modelled. Three sidegrades were decompiled between 19:54Z and 20:57Z,
which is why the inventory is 9, not 12 — and one of them
(`Elusive Kernel of Regeneration`) held the only `suffix_adaptive_shell` T7
observation owned, which is what made the archive fix necessary. The `was`
column is the single-capture number and is **not** comparable.

| Δ | was | Slot | Item | ilvl | Stab | Status |
|---|---|---|---|---|---|---|
| **+9.8** | +4.6 | Firewall | Bastioned Firewall of Infection | 1032 | 28 | best ceiling, and now the best-*supported* one — `of Recovery` is observed at T1/2/3/6/7/8/9 archive-wide. Held on the sustain guardrail, see caveat |
| **+8.9** | +8.5 | Daemon | Sighted Daemon of the Storm | 1382 | 29 | craft base — locked. Nearest miss; low +8.4 |
| **+6.7** | +8.3 | Kernel | Elusive Kernel of Spikes | 1474 | 24 | craft base — locked, see caveat |
| — | — | Driver | Warmongering Driver of Extinction | 731 | 0 | **revert path for `driver-ab-2026-07-27` — keep locked** until the A/B closes |
| −8.6 | — | Payload | Targeted Payload of Perfect Strike | 1126 | 0 | spent alternate, releasable |
| −10.3 | — | Payload | Enduring Payload of Armageddon | 749 | 0 | Payload revert path (A/B concluded KEEP) — releasable |
| −22.6 | — | Shell | Overclocked Shell of the Monolith | 628 | 0 | Shell revert path (A/B concluded KEEP) — releasable |
| −24.9 | — | Analyzer | **Aligned Analyzer of Light Speed** | 406 | 0 | **revert path, A/B not formally closed — keep locked** |
| −38.7 | — | Router | **Aligned Router of the Undying** | 445 | 0 | **revert path — keep locked.** Two T1-maxed affixes (Regen +35, Def +18.05%); the only Defense-heavy Router owned |

**Before decompiling anything, check it is not a sole ladder anchor.** `Elusive Kernel of Regeneration` was released on 27 July as a +1.7 sidegrade and took the only `suffix_adaptive_shell` T7 observation with it (`crafting.md` §12.1.1). The archive fix means this can no longer *lose* an observation — every past capture still counts — but an item carrying a tier no capture has ever recorded is still worth one capture before it goes.

## Next craft: none approved — the Driver failed re-verification

**Aegisbound Driver of Execution is +3.8, not +14.1** (51.3 vs equipped 47.4, archive ladders). Its entire case was CritDmg reaching **+81.21%** at T1 — extrapolated five tiers at 1.4×/tier from a *single* observed point (`suffix_critdamage` T6, on the item itself). On the corrected region-aware ladder the same plan projects **+53.67%**, and the verdict drops into the sidegrade band. Corrected loadout effect of the full craft: crit damage 1.509 → 2.046 and crit factor 1.160 → 1.266 (**+9.1% damage**, not +22%), bought with **Accuracy −4.35%** and crit chance 0.315 → 0.254 — against a build whose #2 bottleneck is hit reliability.

The mechanism it was chosen for is still real: the 27 July zone readout found a **damage floor in tank matchups** (three Corporate deaths from ≥79% starting HP against 19–23K HP Trojan Wall / Rootkit enemies, losing not to burst but to fights the build could not close), and crit damage still has no gear contribution at all. Only the size of the fix changed, and it is no longer large enough to clear the band.

**Approved next action on this item: one measured step, not the chase.** Run `of Execution` T6→T5 alone (60% per attempt, cap 3, ~1.6 Stability of 26) and recapture. `value_min`/`value_max` are the tier's full range, so one *successful* promotion reveals the exact T5 midpoint and pins this family's deep step, which currently spans 1.15–1.42 across observed families — worth ±10 score on this verdict. Continue to the full contract only if the realized T5 midpoint implies a step ≥ ~1.33 (displayed CritDmg ≳ 19.3%).

Note the line is at a **99% roll** (0.1667 of 0.1231–0.1670), so the step is worth little as a stat — expected ~+1.7pp CritDmg, and a bottom-of-range T5 roll would be a small downgrade (`crafting.md` §12.2). It is bought for the measurement.

## Holds and caveats

- **Bastioned Firewall of Infection (+9.8)** is the highest ceiling owned and, on archive-wide ladders, the best-evidenced — `suffix_adaptive_shell` is observed at T1/T2/T3/T6/T7/T8/T9, so `of Recovery` T8→T1 plans almost entirely inside measured data. **Still held, on the sustain-anchor guardrail** — and now quantified rather than asserted. At loadout level the swap buys **Def +7.1% and Eva +4.3%** with **MaxHP −7.9% (14,956 → 13,778) and Regen −5.4% (379.4 → 358.9)**. Regeneration is this build's measured win condition: −5.4% of realized regen is ≈ **−12.5 `prg`/round against a measured net drain of −2.8/round**, so the craft flips net drain positive and hands back the +20.5 death streaks the 27 July package bought. ECC Memory L93→L99 covers only about a third of that loss (+2.05%). Directional on the regen → realized-`prg` proportionality, but the sign is not in doubt. Revisit when a Firewall base appears that does not spend Regen and MaxHP, or once the Hacking Simulator can measure it instead of arguing it.
- **Elusive Kernel of Spikes (+6.7)** projects MaxHP +38.47% but strips the Kernel's Defense and buys only +7 net Regen. At loadout level: **MaxHP +22.5% (14,956 → 18,325), Def −4.5% (1,090.7 → 1,041.5), Regen +2.8%, Acc −0.7%, AtkSpd −1.2%, Thorns 6 → 17.** This is close to the exact trade the 21 July Kernel A/B ran and **rejected** — the Defense loss is slightly *worse* (−4.5% vs −3.65% realized) and the Regen gain slightly *smaller* (+2.8% vs +4.2%); only the Max HP side is bigger, and Max HP is a buffer, not mitigation or recovery. **Craft the Firewall before any Kernel** — it puts Defense back first.
- **Sighted Daemon of the Storm (+8.9, low +8.4)** has no sustain cost and is the best-supported *direction* on the board: at loadout level **Eva +8.9% and Acc +3.2%** (bottleneck #2) for AtkSpd −8.7%, which the 22 July law says should not move the death ceiling. Held only because the ceiling discounts to ~+3.9 under a §10.1 contract. **Strongest candidate if one craft has to run before the Hacking Simulator lands** — but note the cost is worse than it first looked. −8.7% attack speed is **not** an income cost (fight cadence is a fixed 4.872 s/fight, invariant — see `mechanics.md` §14): it is a **depth** cost, because attack speed pays in rounds per fight and fewer rounds means fewer enemy attacks per fight. Giving up 8.7% AtkSpd buys evasion by spending attrition resistance, which is the opposite of what this build needs.
- Revert paths: keep **Aligned Analyzer of Light Speed** and **Aligned Router of the Undying** locked until both 27 July A/Bs are formally closed against the new Corporate Network baseline, and **Resilient Firewall of Perpetuity** locked until `firewall-ab-2026-07-31` closes. **Bastioned Payload of Perfect Strike released 31 Jul** (`payload-ab-2026-07-30` closed KEEP); it and the Shell revert path are releasable whenever inventory pressure appears — no pressure now.

## Safe to decompile now

**Nothing.** `Vital Daemon of Quarantine` was the last entry and was released on 27 July. All nine remaining items are either a live craft base, a locked revert path, or a spent alternate being held while inventory pressure is zero (9/102 slots).

**Do not reuse the pre-27-July safe-decompile lists.** They were built against an inventory that no longer exists and against ceiling verdicts computed under the old T3 tier cap and single-capture ladders.
