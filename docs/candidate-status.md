# Candidate and Craft Status — 23 July 2026

> **23 July note:** the 22 July inventory was mass-decompiled overnight (including previously locked items — Targeted Daemon of Quarantine, Vital Driver of the Hawk, the Firewall alternates); holds below that reference them are void. Current inventory is the ~17 fresh drops; re-rank with `ih.py potential`.

## Finished or spent projects

| Item | Status | Action |
|---|---|---|
| Citadel Shell of the Phoenix | **Crafted + equipped 23 Jul; A/B KEEP** (death mean +7.0, ceiling ~110, net drain and onset improved) | Main set |
| Overclocked Shell of the Monolith | Revert path for the above | Keep decompile-locked |
| Bastioned Payload of Perfect Strike | **Crafted + equipped 23 Jul; A/B KEEP** (+2.3 death depth, 77% vs 70% hit) | Main set |
| Enduring Payload of Armageddon | Revert path for the above | Keep decompile-locked |
| Citadel Firewall of the Bastion | Coherent alternate; not main streak upgrade | Keep locked as alternate/test item |
| Aggressive Kernel of Renewal | Failed main-set combat trial | Revert to Hearty; keep only for alternate/test |
| Fortified Firewall of the Giant | Failed Augment gate | Decompile or use as disposable mechanics-test base |
| Aligned Firewall of Bastion | Strong speed/barrier alternate base | Hold; no blind main-set craft |

## Remaining project holds

- Aggressive Kernel of Piercing: lower-priority offensive project. Existing high Armor Penetration is attractive, but it loses too much Defense, Regeneration, Accuracy, Attack Speed and Corruption unless Augment is exceptional.
- Warmongering Shell of Vengeance: high thorns/evasion alternate; current Shell's Defense is too valuable for main set.
- Immortal Driver of Velocity: speed/HP/barrier alternate; loses major damage and Accuracy.
- Vital Driver of Precision: speculative Accuracy/Crit project; needs a meaningful damage line.
- Intangible Daemon of Light Speed: zero-Stability speed alternate.
- Spectral Kernel of Perpetuity: zero-Stability full-HP alternate.

## Farming holds

- Overflowing Kernel of Blight — Drop Boost.
- Prolific Kernel of Piercing — Drop Boost.
- Coveted Kernel of Health — Item Rarity.

## Safe-decompile list from the 21 July full export

> **⚠ 22 July revision:** this list predates the post-craft ceiling model (`ih.py potential`). It was built from current rolls and is NOT safe as-is: **Resilient Analyzer of the Bulwark** ranks *above* the equipped Analyzer at ceiling, and **Keen Shell of Barbs**, **Vital Driver of Precision** and others rank as top ceiling bases in their slots. Re-run `ih.py potential --slot <s>` and keep anything within ~10 score of equipped before decompiling.

Payloads: Pinpoint Payload of Precision; Targeted Payload of Rending; Fortified Payload of Puncturing.

Firewalls: Hearty Firewall of the Fortress; Resilient Firewall of Hardening. Fortified Firewall of the Giant is now also decompile-eligible after the failed Augment unless retained as a test mule.

Analyzers: Resilient Analyzer of Bulwark; Reinforced Analyzer of Hardening; Stalwart Analyzer of Accuracy.

Shells: Reinforced Shell of Spikes; Assault Shell of Recovery; Leviathan's Shell of Retribution; Keen Shell of Barbs.

Drivers: Slippery Driver of Destruction; Bulwarked Driver of Unerring; Cataclysmic Driver of Precision.

Daemons: Keen Daemon of Wind; Fortified Daemon of Barbs.

Kernels: Aggressive Kernel of Recovery; Vital Kernel of Contagion; Pinpoint Kernel of Blight; Ghosted Kernel of Mending; Guided Kernel of Colossus.

Before decompiling, compare against a fresh inventory export because this list reflects the 21 July snapshot and subsequent known craft outcomes only.

## 22 July 2026 — post-calibration ceiling verdicts (21:32 capture)

From `ih.py potential` with calibrated weights (Corrupt 0.6, verdict bands ±5). Full output is regenerable; this records the decisions:

| Slot | Verdict | Notes |
|---|---|---|
| Daemon | **Targeted Daemon of the Storm +8.0 UPGRADE** — approved next craft project | Preserves AtkDmg density (18% at ceiling) while adding ~+31% AtkSpd; the tempo profile the loss analysis wants |
| Daemon | Intangible Daemon of Thorns +10.6 (top score) — **held, not approved** | Repeats the Hawk mistake shape: dumps AtkDmg 21→0.9 (~−12% output multiplicatively, which linear weights under-penalize) for Eva/HP/Thorns |
| Payload | **Targeted Payload of Deadliness +6.9 UPGRADE** — approved second project | Keeps AtkDmg 23%, adds CritCh 12.5/AtkSpd 11.4/ArmorPen 105; econ cost: −15% hack XP (slows level → heal_base) |
| Firewall | Aligned Firewall of Bastion +6.5 — **conditional**, guardrail-gated | Score driven by interpolated Corrupt T3~ + Barrier 314; loses Regen −31 / MaxHP −11 vs Brutal — sustain-anchor rule applies, craft only with explicit A/B test plan |
| Driver | Vital Driver of the Hawk (crafted, compiled) | Anti-evasion alternate; decompile-locked; also the designated hit-formula measurement instrument |
| Analyzer/Shell/Router/Kernel | No upgrades at ceiling | Equipped anchors hold; Resilient Analyzer of the Bulwark downgraded to sidegrade (+1.7) after calibration |
