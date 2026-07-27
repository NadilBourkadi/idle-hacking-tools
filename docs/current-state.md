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

1. **Primary: accumulated HP attrition across long streaks** — losses consistently start well below full HP (starting HP 17–65%, median ~30% across the 24–27 July deaths). Moved twice: the Phoenix Shell (23 July) lifted the ceiling ~101 → ~110 and attrition onset 60–76 → 78–90; player level then carried it to a settled 105–110. Residual form is deep-fight net drain (~2.2K/fight at streak 86–105) where `prg` decay outpaces gear Regen. The 27 July package attacks this from three sides at once — hardware Regen +14.9%, Defense +6.1%, and Barrier from **0 to 280** — and has not yet been read out.
2. **Secondary: hit reliability / fight duration** against high-evasion enemies — the Bastioned Payload lifted deep-streak hit rate 70 → 77%. Accuracy has since gone 6,260 → 7,414 (+18%) from the Analyzer craft plus hardware; expect hit rate to move again.
3. **Tertiary: incoming burst** against the thin Def/Barrier flank (one 76%-start-HP death vs a Trojan Wall in the Shell A/B). Barrier 0 → 280 is the first direct answer to this since the Shell traded it away.
4. **Output is the deliberate cost.** Crit chance fell 51.0% → 31.5% across the day (Analyzer craft plus Vulnerability Scanner cut to 17). Roughly −10% damage per landed hit, accepted because the 22 July law holds that tempo does not move the death ceiling while recovery and mitigation do. If depth does not improve, `damage_taken` **per round** is the diagnostic — a rise there would mean attack speed is a mitigation stat and the model needs revising.

Next levers are recovery *systems*, not more gear regen: WAF Rules, Snapshot Rollback, and the **Hacking Simulator** at homelab 10 (~600 progress points away), which replaces heuristic verdicts with measured ones.

## Active project status

- **Targeted Analyzer of Light Speed** — equipped 27 July, A/B not yet read. Expected mechanism: realized `prg`/round is unchanged by it (no Regen), so barrier soak appearing from zero is its signature; accuracy is bundled with the same day's hardware reallocation and is not separately attributable.
- Revert paths held decompile-locked: Aligned Analyzer of Light Speed, Overclocked Shell of the Monolith, Enduring Payload of Armageddon.
- No candidate is currently approved for a blind full craft. Re-rank with `ih.py potential --slot <slot>` against the current bottleneck before spending. The 27 July uncapping surfaced two candidates that the old T3 cap hid: **Titanic Router of Regeneration +22.8** (Regen 43 → ~98, but Def 19.33% → 0.83% — sustain-anchor rule applies) and **Bastioned Firewall of Infection +7.3** on the long-flagged ilvl-314 Firewall. Neither is approved; both need the §10 contract treatment.
- Stranded by design: ~1.47M shop-locked gathering resources after the reset. Worth ≈2.9M credits at market rate against an 11.1B balance; clearing them would cost ~90% of the chip budget. Leave them.

## Standing decisions

Recorded in `decision-log.md`; the empirical guardrails live in `CLAUDE.md`.

## Prediction reliability roadmap (added 22 July 2026)

How craft/swap verdicts get more reliable, in order of arrival:

1. **Now:** `ih.py potential` verdict bands (upgrade needs Δ > +5), economy deltas, calibrated Corrupt weight. Every capture after a successful Version Upgrade also densifies the empirical tier ladders (fewer `~` interpolations).
2. **Cheap measurements:** the Hawk Driver is a clean instrument for the unknown hit-chance formula (+7.3% Acc, minimal other combat deltas) — any test streak with it doubles as a formula-fitting run (open questions §7/§8).
3. **The game's own simulators (the end state):** Homelab **Hacking Simulator** install (5B credits + 3 hackcoin, **gated: homelab level 10**, currently 8) unlocks **Software Profiler** (1B + 1 hackcoin/level: 100 combat sims vs a chosen enemy level/zone) and **CI/CD Pipeline** (10B + 1 hackcoin: full-streak simulations with gear customization, 5/day per level). These replace heuristic verdicts with measured ones. Sequence: Virtualization Cluster (available now, anti-attrition) → homelab 10 → Hacking Simulator → profile before every craft.
