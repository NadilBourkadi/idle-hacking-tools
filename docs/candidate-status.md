# Candidate and Craft Status — 27 July 2026

> Rewritten from scratch. The 23 July version described an inventory that no longer exists: 43 of 52 items were decompiled on 27 July after an explicit audit, leaving 12. Every hold, safe-decompile list and ceiling verdict in the previous version is void.

## Main set (all eight slots)

| Slot | Item | Origin |
|---|---|---|
| Payload | Bastioned Payload of Perfect Strike | crafted 23 Jul, A/B KEEP |
| Firewall | Brutal Firewall of Perpetuity | original baseline — **the weakest slot**, ilvl 314 |
| Analyzer | Targeted Analyzer of Light Speed | crafted 27 Jul (+24.9), A/B KEEP |
| Shell | Citadel Shell of the Phoenix | crafted 23 Jul (+22.6), A/B KEEP |
| Driver | Warmongering Driver of Extinction | original baseline |
| Router | Titanic Router of the Undying | crafted 27 Jul (**+38.7**, best on record), A/B KEEP |
| Daemon | Targeted Daemon of the Storm | crafted 22 Jul, A/B KEEP |
| Kernel | Hearty Kernel of Decay | original baseline |

Five of eight are now contract crafts. The three baselines (Firewall, Driver, Kernel) are exactly where the remaining upgrades sit.

## Inventory — all 12 items, ranked by ceiling delta vs equipped

Regenerate with `python3 scripts/ih.py potential`. Figures below are from the
19:46Z capture, with the Snapshot Backups 10% Stability preserve modelled.

| Δ | Slot | Item | ilvl | Stab | Status |
|---|---|---|---|---|---|
| **+14.1** | Driver | **Aegisbound Driver of Execution** | 1605 | 26 | **next craft** — locked |
| **+11.5** | Daemon | Sighted Daemon of the Storm | 1382 | 29 | craft base — locked |
| **+9.5** | Kernel | Elusive Kernel of Spikes | 1474 | 24 | craft base — locked, see caveat |
| **+9.0** | Firewall | Bastioned Firewall of Infection | 1032 | 28 | craft base — locked |
| +1.7 | Kernel | Elusive Kernel of Regeneration | 1243 | 29 | new drop, sidegrade |
| +0.7 | Payload | Titanic Payload of Precision | 1591 | 30 | new drop, sidegrade — highest ilvl and full Stability, keep as a blank |
| −3.6 | Daemon | Vital Daemon of Quarantine | 1362 | 25 | new drop, decompile |
| −8.6 | Payload | Targeted Payload of Perfect Strike | 1126 | 0 | spent alternate, releasable |
| −10.3 | Payload | Enduring Payload of Armageddon | 749 | 0 | Payload revert path (A/B concluded KEEP) — releasable |
| −22.6 | Shell | Overclocked Shell of the Monolith | 628 | 0 | Shell revert path (A/B concluded KEEP) — releasable |
| −24.9 | Analyzer | **Aligned Analyzer of Light Speed** | 406 | 0 | **revert path, A/B not formally closed — keep locked** |
| −38.7 | Router | **Aligned Router of the Undying** | 445 | 0 | **revert path — keep locked.** Two T1-maxed affixes (Regen +35, Def +18.05%); the only Defense-heavy Router owned |

## Next craft: Aegisbound Driver of Execution

**+14.1 at ceiling** (61.5 vs equipped 47.4), 26 Stability, ilvl 1605 — the highest item level owned. Plan: `of Execution` T6→T1, `of Annihilation` T5→T3. Expected ~17.8 Stability / ~19 attempts.

Projection: AtkDmg +22.69%, AtkSpd +11.68%, **CritDmg +81.21%**, MaxHP +3.56%, Def +4.89%.

This is the right next craft for a reason beyond its score. The 27 July zone readout found a **damage floor in tank matchups** — three Corporate deaths from ≥79% starting HP against 19–23K HP Trojan Wall / Rootkit enemies, losing not to burst but to fights the build could not close before in-fight regen decayed. That is the day's crit sacrifice (51% → 31.5% crit chance) surfacing. Crit damage currently has **no gear contribution at all** (base 1.5 + 0.009 hardware); +81.21% would take crit damage to ~2.32 and the crit factor from 1.16 to ~1.42 — roughly **+22% damage** — while holding AtkDmg essentially flat (23.24% → 22.69%), so the multiplicative-AtkDmg guardrail does not bite.

Requires a full `crafting.md` §10.1 contract before spending.

## Holds and caveats

- **Bastioned Firewall of Infection (+9.0)** was the recommended next craft earlier on 27 July, before the Snapshot Backups preserve fix re-ranked the field. It is still the fix for the weakest slot (ilvl 314) and adds Def +13.8pp / Eva +9.1pp — but it costs **Regen −14 and MaxHP −11pp**, and regen is what is currently working (net drain per round is −2.8). Needs a fresh contract pass, not the stale +9.0 headline.
- **Elusive Kernel of Spikes (+9.5)** projects MaxHP +38.7% but strips the Kernel's Def and cuts Regen 53 → 37. Gear Defense is already down to 44.26% with none on the Router. **Craft the Firewall before any Kernel** — it puts 13.8pp back first.
- **Sighted Daemon of the Storm (+11.5)** is a clean tempo/evasion craft with no sustain cost, and the second-best base owned.
- Revert paths: keep **Aligned Analyzer of Light Speed** and **Aligned Router of the Undying** locked until both 27 July A/Bs are formally closed against the new Corporate Network baseline. The Payload and Shell revert paths are releasable whenever inventory pressure appears (currently 12/102 slots — no pressure).

## Safe to decompile now

`Vital Daemon of Quarantine` (−3.6). Everything else is either locked, a live craft base, or a sidegrade worth keeping as a blank while inventory is empty.

**Do not reuse the pre-27-July safe-decompile lists.** They were built against an inventory that no longer exists and against ceiling verdicts computed under the old T3 tier cap.
