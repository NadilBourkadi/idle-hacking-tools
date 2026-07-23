# Idle Hacking — Current State (interpretation)

**Last reviewed:** 22 July 2026
**Player:** the player

This file holds *interpretation only* — the reasoning behind the current setup and priorities. For numbers, always query the latest capture (`python3 scripts/ih.py loadout` / `stats` / `candidates`); do not copy stats into this file, they go stale with every capture.

## Intended main loadout and why

The main set is the original eight-slot baseline (see `ih.py loadout`). Its logic:

- **Sustain anchors — Brutal Firewall of Perpetuity and Hearty Kernel of Decay.** Both are low item level but carry dense HP/Defense/Regeneration packages that no candidate or craft has yet replaced without losing net sustain. The 21 July Kernel A/B trial (see `equipment-tests.md`) empirically vetoed trading Defense/Accuracy/Attack Speed for more HP/listed Regen.
- **Offensive core — Payload, Analyzer, Driver, Daemon** supply the accuracy/crit/speed/damage package. The Payload slot holds the crafted **Bastioned Payload of Perfect Strike** (23 July, second contract-crafted main-set item; A/B KEEP: death ceiling +2.3 with four consecutive 100–101 deaths, hit rate 76.9% vs 70.1% at higher evasion, at the cost of +14% rounds/fight — Enduring Payload of Armageddon is the locked revert path). The Daemon slot holds the crafted **Targeted Daemon of the Storm** (22 July, first contract-crafted main-set item; A/B: −5% fight length, −6.5% damage taken; its Quarantine revert path was decompiled 23 July — the keep is now permanent).
- **Shell and Router** — the Router remains the Defense/Regen backbone. The Shell slot changed profile on 23 July: the crafted **Citadel Shell of the Phoenix** (first craft to realize above projection, +22.6 score; **A/B KEEP**, death mean +7.0, new ~110 ceiling, attrition onset +~20 streaks, realized regen +28–36%) trades Def 28.4%/Barrier 221 for Eva +20%/Regen +46/Def 12.2% — recovery over mitigation, now the third contract-crafted main-set item. Old Overclocked Shell is the locked revert path. The build's gross intake is ~+10% at deep streaks; its net drain is much lower.

Caveat now quantified: the Firewall's ilvl-314 malus is ~-31% on percentage stats and worse on flat Regen (scaling law, `static-analysis-2026-07-22.md`). A replacement *will* eventually win; it must preserve the HP/Def/Regen *package*, not just raw numbers.

## Bottleneck model

1. **Primary: accumulated HP attrition across long streaks** — losses consistently start well below full HP. Substantially moved 23 July by the Phoenix Shell (attrition onset 60–76 → 78–90, ceiling ~101 → ~110); the residual form is deep-fight net drain (~2.2K/fight at streak 86–105) where prg decay outpaces even +46 gear Regen. Next levers are recovery *systems* (WAF Rules at homelab 9, Snapshot Rollback, the Hacking Simulator path at 10), not more gear regen.
2. **Secondary (partially addressed 23 July): hit reliability / fight duration** against high-evasion enemies — the Bastioned Payload lifted deep-streak hit rate 70→77%; hit rate held ~78% throughout the Shell test.
3. **Tertiary: incoming burst** against the thinner Def/Barrier flank (one 76%-start-HP death vs a Trojan Wall, eff. acc ~5,900, in the Shell A/B) — real but not dominant; watch its share as streaks now regularly reach 108–111.

## Active project status

- **Citadel Firewall of the Bastion** — coherent defensive alternate; not a main-set upgrade (loses 33 Regen). Keep locked.
- **Aggressive Kernel of Renewal** — failed main-set combat trial; alternate/test material only.
- **Fortified Firewall of the Giant** — aborted after T9 Barrier Augment; decompile or use as disposable test mule.
- **Aligned Firewall of Bastion** — best speed/barrier alternate base; no blind craft.
- No candidate is currently approved for a blind full craft. Re-rank with `ih.py candidates --slot <slot>` against the current bottleneck before spending resources.

## Standing decisions

Recorded in `decision-log.md`; the empirical guardrails live in `CLAUDE.md`.

## Prediction reliability roadmap (added 22 July 2026)

How craft/swap verdicts get more reliable, in order of arrival:

1. **Now:** `ih.py potential` verdict bands (upgrade needs Δ > +5), economy deltas, calibrated Corrupt weight. Every capture after a successful Version Upgrade also densifies the empirical tier ladders (fewer `~` interpolations).
2. **Cheap measurements:** the Hawk Driver is a clean instrument for the unknown hit-chance formula (+7.3% Acc, minimal other combat deltas) — any test streak with it doubles as a formula-fitting run (open questions §7/§8).
3. **The game's own simulators (the end state):** Homelab **Hacking Simulator** install (5B credits + 3 hackcoin, **gated: homelab level 10**, currently 8) unlocks **Software Profiler** (1B + 1 hackcoin/level: 100 combat sims vs a chosen enemy level/zone) and **CI/CD Pipeline** (10B + 1 hackcoin: full-streak simulations with gear customization, 5/day per level). These replace heuristic verdicts with measured ones. Sequence: Virtualization Cluster (available now, anti-attrition) → homelab 10 → Hacking Simulator → profile before every craft.
