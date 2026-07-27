# Idle Hacking — Current State (interpretation)

**Last reviewed:** 27 July 2026
**Player:** the player

This file holds *interpretation only* — the reasoning behind the current setup and priorities. For numbers, always query the latest capture (`python3 scripts/ih.py loadout` / `stats` / `candidates`); do not copy stats into this file, they go stale with every capture.

## Intended main loadout and why

The main set is the original eight-slot baseline (see `ih.py loadout`). Its logic:

- **Sustain anchors — Brutal Firewall of Perpetuity and Hearty Kernel of Decay.** Both are low item level but carry dense HP/Defense/Regeneration packages that no candidate or craft has yet replaced without losing net sustain. The 21 July Kernel A/B trial (see `equipment-tests.md`) empirically vetoed trading Defense/Accuracy/Attack Speed for more HP/listed Regen.
- **Offensive core — Payload, Analyzer, Driver, Daemon** supply the accuracy/crit/speed/damage package. The Payload slot holds the crafted **Bastioned Payload of Perfect Strike** (23 July; A/B KEEP: death ceiling +2.3, hit rate 76.9% vs 70.1%, at +14% rounds/fight — Enduring Payload of Armageddon is the locked revert path). The Daemon slot holds the crafted **Targeted Daemon of the Storm** (22 July; A/B: −5% fight length, −6.5% damage taken; revert path decompiled, keep permanent). The Analyzer slot changed profile on 27 July: the crafted **Targeted Analyzer of Light Speed** (fourth contract-crafted main-set item, **+24.9 at ceiling — the largest craft delta on record**) trades CritCh 23.10% → 8.54% for Acc +19pp, Eva +5.5pp, AtkSpd +4.7pp and **Barrier 0 → 269**, restoring the mitigation the Phoenix Shell gave up. Aligned Analyzer of Light Speed is the locked revert path. Not yet A/B-read.
- **Shell and Router** — the Router remains the Defense/Regen backbone. The Shell holds the crafted **Citadel Shell of the Phoenix** (23 July, first craft to realize above projection, +22.6; **A/B KEEP**, death mean +7.0, ceiling ~110, attrition onset +~20 streaks, realized regen +28–36%), trading Def 28.4%/Barrier 221 for Eva +20%/Regen +46/Def 12.2% — recovery over mitigation. Old Overclocked Shell is the locked revert path.
- **Hardware is now part of the loadout, not a side system.** The 27 July free reset re-cut 821 levels into 418 better ones: Tracking Algorithm / TOR Node / Encryption Module at 100 and ECC Memory at 85, with Overclock/Vulnerability Scanner/Buffer Overflow cut to near-zero and Packet Shield / Exploit Framework abandoned entirely (their gear-flat multiplicand was zero — 81K chips doing nothing). Hardware, homelab and equipment percentages share one additive pool (`mechanics.md` §13), so hardware levels are directly comparable to gear affixes and belong in every loadout judgement.

Caveat now quantified: the Firewall's ilvl-314 malus is ~-31% on percentage stats and worse on flat Regen (scaling law, `static-analysis-2026-07-22.md`). A replacement *will* eventually win; it must preserve the HP/Def/Regen *package*, not just raw numbers.

## Bottleneck model

1. **Primary: accumulated HP attrition across long streaks** — losses consistently start well below full HP (starting HP 17–65%, median ~30% across the 24–27 July deaths). Moved twice: the Phoenix Shell (23 July) lifted the ceiling ~101 → ~110 and attrition onset 60–76 → 78–90; player level then carried it to a settled 105–110. Residual form is deep-fight net drain where `prg` decay outpaces gear Regen. The 27 July package attacked this from three sides at once — hardware Regen +14.9%, Defense +6.1%, and Barrier from **0 to 280** — and **read out at +20.5 death streaks with net drain per round now negative (−2.8)**. Regeneration is therefore the confirmed win condition for this build, which is why candidates that spend Regen or Max HP for Defense are held even at a positive ceiling delta. **Settled ceiling as of 27 July 20:50 UTC: mean peak death streak 116.2, sd 6.9, median 114.5 over 38 stream-ledger deaths** — quote this, not the older 105–110. Deaths still start at a median 37% HP (attrition); only 5/38 start above 70% (burst/matchup).
2. **Secondary: hit reliability / fight duration** against high-evasion enemies — the Bastioned Payload lifted deep-streak hit rate 70 → 77%. Accuracy has since gone 6,260 → 7,414 (+18%) from the Analyzer craft plus hardware; expect hit rate to move again.
3. **Tertiary: incoming burst** against the thin Def/Barrier flank (one 76%-start-HP death vs a Trojan Wall in the Shell A/B). Barrier 0 → 280 is the first direct answer to this since the Shell traded it away.
4. **Output is the deliberate cost.** Crit chance fell 51.0% → 31.5% across the day (Analyzer craft plus Vulnerability Scanner cut to 17). Roughly −10% damage per landed hit, accepted because the 22 July law holds that tempo does not move the death ceiling while recovery and mitigation do. If depth does not improve, `damage_taken` **per round** is the diagnostic — a rise there would mean attack speed is a mitigation stat and the model needs revising.

Next levers are recovery *systems*, not more gear regen: WAF Rules, Snapshot Rollback, and the **Hacking Simulator** at homelab 10 (~600 progress points away), which replaces heuristic verdicts with measured ones.

## Active project status

- **Analyzer + hardware + Router bundle — read out 27 July, decision KEEP** (`equipment-tests.md`): +20.5 death streaks, the largest measured gear effect in the project. Mechanism: realized `prg`/round 171.3 → 231.8 (+35.3%) took **net drain per round negative (−2.8)**. Revert paths held decompile-locked: Aligned Analyzer of Light Speed, Aligned Router of the Undying, Overclocked Shell of the Monolith, Enduring Payload of Armageddon.
- **No craft in flight.** The standing next craft (Aegisbound Driver, +14.1) failed re-verification on 27 July when the tier-ladder model was corrected — it is +3.8, a sidegrade (`crafting.md` §12.1, `candidate-status.md`). Best remaining ceilings on archive-wide ladders are **Firewall +9.8, Daemon +8.9 (low +8.4), Kernel +6.7**, all inside the sidegrade band once discounted for §10.1 contract conservatism. The Firewall additionally fails the sustain guardrail on a quantified basis: its −5.4% realized Regen is ≈ −12.5 `prg`/round against a measured net drain of −2.8/round, i.e. it flips the sign of the thing that bought +20.5 death streaks.
- **Craft verdicts are currently the weakest instrument in the workspace.** Four of them turned on model defects found in two evenings, and the ~5-point contract discount was itself calibrated against a ladder that is now known to have been biased. Treat any ceiling delta under ~+10 as unresolved until the **Hacking Simulator** (homelab 10, 905 points away) can measure instead of argue.
- **Craft ladders are now fitted archive-wide** (`ihlib.tier_ladders_archive`, 58 captures, 582 tier observations). Before this, decompiling an item deleted its tier observations and moved live verdicts by up to 4.4 points with no game state change — see `crafting.md` §12.1.1. Ceiling numbers quoted before 27 July 21:00 UTC were computed on single-capture ladders and are not comparable to these.
- Re-rank with `ih.py potential --slot <slot>` against the current bottleneck before spending.
- Stranded by design: ~1.47M shop-locked gathering resources after the reset. Worth ≈2.9M credits at market rate against an 11.1B balance; clearing them would cost ~90% of the chip budget. Leave them.

## Standing decisions

Recorded in `decision-log.md`; the empirical guardrails live in `CLAUDE.md`.

## Prediction reliability roadmap (added 22 July 2026)

How craft/swap verdicts get more reliable, in order of arrival:

1. **Now:** `ih.py potential` verdict bands (upgrade needs Δ > +5), economy deltas, calibrated Corrupt weight. Every capture after a successful Version Upgrade also densifies the empirical tier ladders (fewer `~` interpolations).
2. **Cheap measurements:** the Hawk Driver is a clean instrument for the unknown hit-chance formula (+7.3% Acc, minimal other combat deltas) — any test streak with it doubles as a formula-fitting run (open questions §7/§8).
3. **The game's own simulators (the end state):** Homelab **Hacking Simulator** install (5B credits + 3 hackcoin, **gated: homelab level 10**, currently 8) unlocks **Software Profiler** (1B + 1 hackcoin/level: 100 combat sims vs a chosen enemy level/zone) and **CI/CD Pipeline** (10B + 1 hackcoin: full-streak simulations with gear customization, 5/day per level). These replace heuristic verdicts with measured ones. Sequence: Virtualization Cluster (available now, anti-attrition) → homelab 10 → Hacking Simulator → profile before every craft.
