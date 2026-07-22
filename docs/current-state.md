# Idle Hacking — Current State (interpretation)

**Last reviewed:** 22 July 2026
**Player:** the player

This file holds *interpretation only* — the reasoning behind the current setup and priorities. For numbers, always query the latest capture (`python3 scripts/ih.py loadout` / `stats` / `candidates`); do not copy stats into this file, they go stale with every capture.

## Intended main loadout and why

The main set is the original eight-slot baseline (see `ih.py loadout`). Its logic:

- **Sustain anchors — Brutal Firewall of Perpetuity and Hearty Kernel of Decay.** Both are low item level but carry dense HP/Defense/Regeneration packages that no candidate or craft has yet replaced without losing net sustain. The 21 July Kernel A/B trial (see `equipment-tests.md`) empirically vetoed trading Defense/Accuracy/Attack Speed for more HP/listed Regen.
- **Offensive core — Payload, Analyzer, Driver, Daemon** supply the accuracy/crit/speed/damage package; the Payload's Crit Damage implicit makes Crit Chance elsewhere unusually valuable.
- **Shell and Router** are the Defense/Barrier backbone.

Caveat now quantified: the Firewall's ilvl-314 malus is ~-31% on percentage stats and worse on flat Regen (scaling law, `static-analysis-2026-07-22.md`). A replacement *will* eventually win; it must preserve the HP/Def/Regen *package*, not just raw numbers.

## Bottleneck model

1. **Primary: accumulated HP attrition across long streaks** — losses consistently start well below full HP.
2. **Secondary: hit reliability / fight duration** against high-evasion (Mirrored) enemies.
3. **Tertiary: incoming burst** in some final matchups.

## Active project status

- **Citadel Firewall of the Bastion** — coherent defensive alternate; not a main-set upgrade (loses 33 Regen). Keep locked.
- **Aggressive Kernel of Renewal** — failed main-set combat trial; alternate/test material only.
- **Fortified Firewall of the Giant** — aborted after T9 Barrier Augment; decompile or use as disposable test mule.
- **Aligned Firewall of Bastion** — best speed/barrier alternate base; no blind craft.
- No candidate is currently approved for a blind full craft. Re-rank with `ih.py candidates --slot <slot>` against the current bottleneck before spending resources.

## Standing decisions

Recorded in `decision-log.md`; the empirical guardrails live in `CLAUDE.md`.
