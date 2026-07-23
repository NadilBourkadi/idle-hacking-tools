# Idle Hacking Decision Log

## 20 July 2026

- Validated passive click-origin capture design.
- Established full eight-slot baseline.
- Current low-item-level Firewall, Analyzer and Router retained because their affix packages dominate raw item level.

## 21 July 2026 — crafting model

- Future candidate reviews will treat inventory items as crafting bases.
- Recommendations must include Augment gates, tier targets, attempt caps and Compile floor.
- Default serious-craft floor set to 8 remaining Stability (+4% Compile).

## 21 July 2026 — Citadel Firewall craft

- Crafted and compiled Citadel Firewall of the Bastion.
- Final useful package: Citadel T2, Bastion T5, Renewal T4, Giant T4, Targeted T7, +4% Compile.
- Decision: retain as alternate; do not replace Brutal Firewall for long streaks without better evidence.

## 21 July 2026 — Aggressive Kernel craft and test

- Crafted Aggressive Kernel of Renewal to +4% Compile.
- Tested in the main set.
- Two unique losses ended at streaks 89 and 90; duplicate Network Monitor export identified.
- Decision: reject as main streak item and prefer Hearty Kernel of Decay.
- Empirical guardrail: additional HP/Regeneration does not justify losing substantial Defense and fight tempo in the current build.

## 21 July 2026 — Fortified Firewall Augment

- Forced suffix Augment added `of Sandboxing` T9 (+25 Barrier), costing one Stability.
- Decision: abort main-set project. Do not attempt routine Prune/re-Augment salvage.

## 22 July 2026 — mechanics resolved from rich full-state capture

- Streak recovery law confirmed exact: `heal = base × 0.99^(streak−10)`, base 4,465 (36.9% max HP) for current build. Attrition = heal decay crossing rising per-fight damage (~streak 50 in sample).
- Snapshot Backups (crafting) and Snapshot Rollback (combat lethal-save) identified as distinct Homelab upgrades; both at level 0. Craft budgets need no backup adjustment.
- Zone catalog captured: Corporate Network (min 600) unlocked and unfarmed; 1.35× credits / 1.5× rarity vs Small Business.

## Current decision

- Main loadout remains the original baseline with Brutal Firewall of Perpetuity and Hearty Kernel of Decay.
- No remaining candidate is approved for blind full crafting; obtain a fresh export before the next resource commitment.

## 22 July 2026 — heal_base resolved (second rich capture, 20:44)

- `heal_base` = 5 × player hack level, confirmed via `statsBreakdown.post_combat_heal` (4,470 = 5 × level 894, all under the `level` component; earlier 4,465 sample = 5 × 893). Not max-HP- or equipment-scaled. Max HP therefore does not improve between-fight recovery at all — buffer only.
- New open question logged: in-fight `prg` decays to 0 within the streak-96 loss (steps of 33); if regen exhausts in long fights, tempo stats are undervalued by constant-regen models.

## 22 July 2026 — candidate evaluation corrected to post-craft ceilings

- Method error caught (user): equipped-vs-inventory comparisons were being made on current rolls. Equipped items are all at 0 Stability (final, uncompiled); inventory carries 25–30 Stability of headroom. Current-roll comparison understates every candidate.
- Empirical tier ladders extracted from the 22 July capture (per-tier normalized affix mids reproduce across items within ~1%; adjacent-tier ratio ≈1.09–1.67, mean ≈1.4). Encoded in `ihlib.tier_ladders` / `plan_craft`; new `ih.py potential` command ranks candidates by projected ceiling (T3 cap, Compile floor 8, greedy expected-Stability plan, heuristic weights `CRAFT_WEIGHTS_*`).
- Ceiling ranking reverses the picture for offensive slots: Daemon (+8 to +11 over equipped), Driver (+7), Payload (+7) have genuine craft-up candidates. Sustain anchors (Firewall, Kernel, Router, Shell) remain unbeaten even at ceiling — validates keeping Brutal Firewall / Hearty Kernel.
- Feasibility: Version Upgrade costs ~150–200k primary + half secondary per attempt. On-hand cycles (185k) and hashes (196k) gate every slot's craft; snippets (2.9M) and packets (50M) are plentiful. Crafting is resource-banking-gated, not credit-gated.
- 21 July safe-decompile list frozen pending re-review — it contains top ceiling bases (Resilient Analyzer of the Bulwark, Keen Shell of Barbs, Vital Driver of Precision). Warning added to `candidate-status.md`.

## 22 July 2026 — Vital Driver craft started; two planning corrections

- Correction (user): basic resources are marketplace-purchasable (~2 credits/unit; 5M Cycles = 10.2M credits). The earlier "crafting is resource-banking-gated" conclusion is withdrawn — credits are the effective crafting currency. Recorded in `crafting.md` §11 and CLAUDE.md.
- Correction (user): recommendations must state accessibility gates (homelab unlock_level, missing installs, zone min_level) and use display names, not internal slugs — gated upgrades can be invisible in the UI. Recorded as a CLAUDE.md analysis rule.
- Vital Driver of Precision Phase 1 Augment executed (21:25 capture): forced prefix rolled **Assault T8, Attack Damage +0.76% [roll 12%]** — Continue class (backfills the AtkDmg lost vs Warmongering). Stability 29/30. Item rarity flipped rare→epic on gaining its 6th affix (single observation; logged in open-questions).
- Cost-model spot-check passed live: augment credit ×1.03 after 1 Stability spent, VU resource cost flat, Compile cost down.

## 22 July 2026 — Vital Driver craft completed (now "Vital Driver of the Hawk")

- Executed per contract: of Precision→T3 (renamed of the Hawk, Acc +17.36%), of Assassination→T3 (renamed of Perfect Strike, CritCh +11.63%), of Haste→T5 (renamed of Lightning, AtkSpd +8.34%); compiled at exactly the 8-Stability floor (+4%). 21 Stability spent post-Augment; costs within budget. Affix display names change with tier — expect renames when tracking items across captures (match by id/`history`, not name).
- Verdict vs equipped Warmongering Driver: NOT a clear upgrade. Gains Acc +7.3 / CritCh +5.5 / AtkSpd +3.2; loses AtkDmg −22.5, Corrupt −8, credits −13.4%, global XP −13.4%. Rough output arithmetic is net-negative vs ordinary enemies and roughly neutral-to-positive only vs high-evasion; 9 of 10 recent deaths were NOT vs Mirrored-class enemies. Heuristic score 41.3 vs 43.3 equipped.
- Status: hold as the anti-evasion alternate (decompile-lock). A/B streak test optional under an abort criterion; no permanent swap on current evidence.

## 22 July 2026 — Storm Daemon craft completed; credit windfall

- Targeted Daemon of the Storm finished per contract: 13 VU attempts (15.1 expected), both build suffixes T3 above projected mids (of Cataclysm AtkDmg 18.40 [86%]; of the Storm evasive_threads Eva 11.85 [99%] / AtkSpd 8.47 [8%]), Refactor correctly blocked by the ≥60%-other-effect rule, Compiled at 16 remaining → +8%. Realized score ~59 vs equipped 49.8 — first craft whose UPGRADE verdict survived realization. A/B streak test pending.
- Version Upgrade roll behaviour: 6/6 observed rolls consistent with independent re-roll in the new tier (open-questions §2 working model).
- Credits jumped 758M → ~23.0B between 21:32 and 21:54 (source not captured; level 894→900, chips +24k). Homelab purchases previously treated as savings targets are now affordable outright.

## 22 July 2026 — Storm Daemon A/B result: KEEP (marginal positive)

Two test streaks (deaths at 98 and 96, enemy lvl 1383/1366) vs same-session old-daemon baseline (8 streaks, median ~96, range 84–104):

- Death streak: 96/98 — meets the ≥94 criterion, indistinguishable from baseline median (variance ±8 dominates a 2-streak sample).
- Rounds/fight at enemy lvl 1240–1357: mean 34.2 vs 36.1 (−5%); damage/round +8.1% (482 vs 446) — the tempo gain is real but half the naive +13% estimate (Acc −7.3 offset).
- Damage taken/fight same bracket: 7.35k vs 7.86k (−6.5%); attrition onset delayed ~5 streaks (starts ≥90% through streak ~91 vs decay from ~85).
- Hit rates at death 77–84% — no accuracy collapse.
- Decision: **keep equipped**. Quarantine daemon retained decompile-locked as revert path. Confounds noted: ids_signatures 2→3 completed mid-session, +8 player levels (def +1.9%, heal 4,470→4,510 — third exact confirmation of heal = 5 × level).
- Structural lesson reaffirmed: gear tempo moves fight length ~5%, but the death ceiling (~96 ± 8) is set by the heal-decay law — only recovery/mitigation systems (Snapshot Rollback — cluster install now building, Thermal Budget, WAF Rules) move it materially.

## 22 July 2026 — Payload craft completed: "Targeted Payload of Perfect Strike", shelved as alternate

- Final: of Perfect Strike T3 CritCh 12.62 [70%], of Thunder T4 (optional T3 push failed both capped attempts), of Rending T3 untouched, compiled at 11 → +5.5%. Score 40.8 vs equipped 39.1 = **+1.7 sidegrade**, inside the pre-declared +2±... range. Not equipped; decompile-locked as the crit-focused alternate. Total craft spend ≈ 14 VU attempts + compile ≈ 2.7M snippets, 1.3M cycles, ~6M credits equivalent.
- Root cause of the downgrade from projected +6.9: Phase-1 cap-out (20% tail) on the double-stat packet_burst line. Verdict-band discipline and the amended on-cap replan rule both originated here.
- Mechanic resolved during compile: explicit values multiplied in place, implicit excluded, ranges unchanged (open-questions §4). Post-compile roll% readings are inflated — ignore them.

## 23 July 2026 — Bastioned Payload of Perfect Strike: craft + A/B → KEEP

- Craft execution (morning): forced-prefix Augment rolled Ghosted T7 (Eva 1.48 [71%] / hack XP +5.68% [74%]) — between the declared outcome classes; re-ranked to +30.2, proceeded. VU phases ran unlucky: 21 Stability for 8 promotions (13 fails vs ~6 expected), of Targeting T8→of Unerring T4 (Acc 16.19 [60%]) and of Infection T9→of Decay T5 (Corrupt 11 [50%]), both short of the T3 targets; stopped at floor, no Refactor (blocked by roll rules), Compiled at 8 → +4%. Spend ≈ 6.9M resource units + 2.2M credits ≈ 18M credit-equivalent. Cost-model confirmations: Augment credit cost ×1.03 exact after 1 Stability; VU base cost ×1.03²¹ exact.
- A/B result (9 post-equip deaths, all before the VLAN +1% Def contamination boundary, vs 12 same-loadout-era baseline deaths): death-streak mean **98.6 vs 96.2 (+2.3)**; last four deaths **100/101/101/101** — a new consistent ceiling. Hit rate **76.9% (n=8,021 attempts) vs 70.1%** legacy deep-streak baseline, against enemies ~25% more evasive and ~200 levels higher. Costs confirmed: +14% rounds/fight at matched streak band (24–42); corruption contributes 1–18% of output (spiky).
- **Decision: KEEP equipped.** Enduring Payload of Armageddon retained as the revert path — decompile-lock it in-game if not already.
- Structural amendment to the 22 Jul lesson ("the death ceiling is set by the heal-decay law; gear only moves tempo"): **accuracy is the first gear lever observed to move the ceiling** (+2–5 streaks), plausibly because misses extend deep fights where regen already trails incoming damage.
- Process note: first A/B concluded on the cross-capture tracker (`ih.py ab` + combat-stream ledger): 347 fights banked, 213 with round detail, zero manual bookkeeping. Experiment closed in `ihlib` (ACTIVE_EXPERIMENT → None).
