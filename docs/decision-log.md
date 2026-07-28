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

## 23 July 2026 — Citadel Shell of Recovery craft approved and started

- Advisory approved the craft on the 09:44 capture: **+17.9 UPGRADE at ceiling** (59.1 vs equipped Overclocked Shell of the Monolith 41.3), widest margin to date; targets the primary attrition bottleneck (proj. Regen +40, Eva +24–26%) at the cost of the equipped Shell's Def 28.4% and Barrier 221. Verdict directional; keep/revert to be decided by A/B with a strict criterion (revert if damage taken/fight +>5%, death mean −>2, or high-accuracy burst deaths dominate). Full §10.1 contract in the 23 Jul advisory; base decompile-locked.
- Phase-A Augment executed (10:00 capture): forced prefix rolled **Spectral T5 (Eva +2.26% [45%] / gathering XP +13.04% [58%])** — Conditional class per contract; re-rank rose to **+20.2 UPGRADE** (61.5), gate passed, proceeding to VU phases (of the Phantom T5→T3 cap 7, of Recovery regeneration T8→T3 cap 12). Stability 25/26.
- Cost-model confirmations (fourth live pass): VU base cost 220,091→226,693 = ×1.03 exact after 1 Stability; Augment credit fee ×1.03; Compile cost fell to 990,406.
- Rarity flipped rare→epic on gaining the 6th affix — second observation (open-questions §12 now 2/2, still a working model).
- A/B contamination boundary declared in advance: baseline = post-VLAN-Rules-L10 deaths with the current Shell (≥6), then swap; during the test no combat-stat homelab jobs, no combat-track hardware buys, no hardware reset.

## 23 July 2026 — Shell craft completed: "Citadel Shell of the Phoenix", equipped, A/B open

- Craft completed per contract with two deviations, both favourable: (1) the adaptive_shell "of Recovery" line was promoted T8→T3 in place of the same-named regeneration line (display-name ambiguity; renamed "of the Phoenix", Def +7.40%/Regen +17 — backfills Def); (2) the regeneration line then also reached T3 (Regen +29) inside the replanned floor-8 budget. 17 VU attempts for 12 promotions (~22 expected — lucky run), no Refactor, Compiled at 8 → +4%. Spend: 26 Stability, ≈7.3M resource units + 3.0M credit Augment fee ≈ ~18M credit-equivalent.
- **Realized score 63.8 vs old Shell 41.3 (+22.6) — above the +20.2 projection; first craft to realize above plan.** Final: MaxHP +8.06%, Def +12.21%, Eva +20.00%, Regen +46, +32.4% gathering resources, +13.7% gathering XP. Trade vs Overclocked Shell of the Monolith: Def −16.2 pts, Barrier −221, Acc −1.2, AtkDmg −1.7.
- Equipped immediately (10:26Z est.) — ahead of the contract's post-VLAN baseline plan, so the baseline is the payload-era window instead: 14 deaths 08:30–10:26Z, mean 97.3. Experiment **shell-ab-2026-07-23** registered in `ihlib` (ACTIVE_EXPERIMENT); keep rule: mean ≥ 96.3 AND damage taken/fight ≤ +5% AND attrition onset not earlier; revert if mean < 95.3, damage taken > +5%, or high-accuracy burst deaths dominate. VLAN Rules L10 (+1% Def) completes ~11:11Z mid-test — segment_ms set; treat pre/post-VLAN test deaths separately.
- Confounds logged: player level 955→958 (+15 heal_base); Malware Injector hardware track +15 levels (~4.7K chips) bought around the equip window — per-level value 0.07, minor, favours the test config; Snapshot Backups → L1 queued (1B cr + 1 hc, non-combat).
- Test-window freeze while the A/B runs: no combat-stat homelab jobs (Packet Trace Analyzer, Honeypot VM, Macro Pad, Mechanical Keyboard, Traffic Mirror, further VLAN), no further combat-track hardware buys, no hardware reset, no other equipment swaps. Economy-only homelab queue.

## 23 July 2026 — shell-ab interim readout at 4/10; keep-rule damage clause amended

- Interim (all four test deaths pre-VLAN — clean window): death streaks **99, 110, 102, 101, mean 103.0 (+5.7)**; the 110 is an all-time record (wider 50-death context mean 96.0). Attrition onset (first fight starting <90% HP, per run) moved from ~60–76 pre to ~78–88 post. Realized in-fight regen **130.6 → 166.6 prg/round (+28%)** at streak ≥60 — the craft's mechanism confirmed in logs. Hit rate stable (78.2% vs 77.9%) — no contamination signal.
- Gross damage taken/fight rose (+1% at streak 24–42, +8.5% at 60–85, +13.6% at 86–105): the Def −16.2/Barrier −221 loss is real and visible. All four deaths remain attrition-shaped (starting HP 27–37%), not burst; two killers were high-accuracy Stealth Worms but at streaks 101/110, past the old ceiling.
- **Rule amendment (pre-outcome, at 4/10):** the pre-declared "damage taken/fight ≤ +5%" clause measured *gross* intake, which mechanically must rise under a mitigation→recovery trade and additionally over-credits the pre era (accounting check: `damage_taken` is gross and includes ~300–700/fight of old-Shell barrier soak that never touched HP). Clause replaced with **net drain/fight (damage_taken − in-fight prg − barrier soak) ≤ +5%** at matched bracket; current reading: net drain ~690 → ~473 at streak 60–85 (**improved**). Depth and onset clauses unchanged. Amendment made with 6 deaths still to bank; logged here before any final verdict.

## 23 July 2026 — shell-ab CONCLUDED: KEEP. Citadel Shell of the Phoenix is main set

- Final at 10/10 deaths: **[99, 110, 102, 101, 101, 92, 108, 109, 110, 111], mean 104.3 vs baseline 97.3 (+7.0)**; the last four (108–111) form a new consistent ceiling ~110, +9–10 over the Bastioned-Payload-era ceiling of ~101. Five deaths post-VLAN (+1% Def confound, favours test config, mean 106.0) — segmented, conclusion unchanged without them.
- Amended keep rule passes on all clauses: death mean 104.3 ≥ 96.3 ✓; net drain/fight (gross − in-fight prg − barrier soak, streak 60–85) ≈ 690 → ≈ 450 pre-VLAN / ≈ 155 post-VLAN ✓ (gross intake rose +8–15% as expected from Def −16.2/Barrier −221, but realized regen rose 130.6 → 167–177 prg/round); attrition onset 60–76 → 78–90 ✓; deaths remain attrition-shaped (7 of 9 autopsied start ≤45% HP; one 76%-start burst death vs a Trojan Wall, not dominant) ✓. Hit rate stable 77.6% vs 77.9% — no contamination.
- **Decision: KEEP equipped.** Overclocked Shell of the Monolith retained decompile-locked as the revert path (precedent: Enduring Payload). Experiment closed in `ihlib` (ACTIVE_EXPERIMENT → None); second A/B concluded fully on the cross-capture tracker (1,051 post-equip fights, all with round detail).
- Ceiling-law refinement: the +7 ceiling move from a recovery-package craft **confirms** the 22 Jul law (recovery/mitigation systems move the death ceiling; tempo does not) — regen is the second gear lever after accuracy to move it, and the largest so far. New residual bottleneck at streak ~110: deep-fight net drain (~2.2K/fight at 86–105) as prg decay outpaces even +46 Regen; next levers are recovery *systems* (WAF Rules at homelab 9, Hacking Simulator path at 10) rather than more gear regen.
- Test-window freeze lifted: combat-stat homelab jobs, hardware combat buys (ECC Memory next at 0.23/1K chips), and hardware-reset planning all unblocked. Caveat: prg/round per-bracket figures use pooled ≥60 means — directional, not formula-level.

## 27 July 2026 — Standing priority set: progression over experimental purity

- Player directive (27 Jul): **in-game progression is the primary objective; methodology and mechanics research are explicitly secondary.** Triggered by an advisory that staged the homelab refill, hardware reset and Analyzer craft across a full day so each would get a clean A/B window.
- Rules now binding on every advisory: recommend everything worthwhile **in one session**; never stagger independently-good actions for attribution; never insert a "bank N deaths for a baseline" step; never freeze the homelab or hardware queue to protect a test; never defer a genuine upgrade because it perturbs a metric. Sequence two actions only when one changes the *correct choice* for the other, otherwise order by what starts a real-time clock soonest.
- Confounded windows are accepted: state that the period measures a **bundle**, keep the passive ledger running (free), attribute later or not at all. A/B metric discipline (`crafting.md` §14) still governs how a test is *read*, never whether progress waits for one.
- Encoded in `CLAUDE.md` (Analysis rules, first bullet) and `.claude/skills/advise/SKILL.md` (Priority order section, overriding the judgement rules).

## 27 July 2026 — Open-questions §13 resolved: one additive stat pool; hardware cost curve decoded

- `hardwareInfo.stats_breakdown` (27 Jul 14:48Z capture) closes exactly on every stat. Hardware %, homelab % and equipment % share **one additive pool**; three stat families (scaling / direct-multiplier / gear-flat). Full statement and verifications moved to `docs/mechanics.md` §13; §13 marked resolved in `open-questions.md`.
- Immediate consequence: a track whose gear-flat multiplicand is 0 yields **exactly 0**. Packet Shield (L40, damage_barrier) and Exploit Framework (L41, armor_penetration) were producing nothing — 81,295 chips dead. The three 0.001-per-level tracks (Overclock / Vulnerability Scanner / Buffer Overflow, 198 levels, 353,163 chips) return one fifth of the pool per chip of the 0.005 tracks.
- Hardware chip cost curve fitted and validated: `cost(L) = 27.97 × L^1.177` (combat), `10.97 × L^1.082` (economy); whole-build cumulative predicts 1,012,105 chips vs the game's own reset refund of 1,002,284 (**+1.0%**). Worth encoding in `ihlib` beside the crafting cost model.
- `ihlib.hardware_track_value` bug found: for gear-flat stats it uses the stat *total* as multiplicand instead of `equipment_flat` (Regen 240.56 vs 194), overstating ECC Memory ~24% (prints 0.72; true ≈0.47–0.58). Ranking unaffected — ECC stays in the top group — but the optimal ECC:Acc:Def:Eva split shifts.

## 27 July 2026 — Targeted Analyzer of Light Speed: best craft on record (+24.9)

- Contract executed from the 15:25Z Augment gate. Augment forced prefix → **Ravaging T7** (gathering XP +8.56% [93%], AtkDmg +1.15% [21%]) — the pre-declared *Conditional* class; re-rank rose 65.0 → 65.8 (+13.5 vs equipped), clearing the > +7 gate, proceeded. Rarity flipped rare→epic on the 6th affix (**3/3**, open-questions §12).
- All three suffix targets **overshot the contract's T3 cap to T2**: of Focus T6 → **of Inevitability T2** (Acc +23.55%); of Lightning T5 → **of Light Speed T2** (Eva +15.29% / AtkSpd +14.00%); of Hardening T7 → **of Containment T2** (Barrier +269 / Acc +11.13%). 19 VU attempts for 12 promotions against ~28 expected — luckier than the Phoenix Shell run. Compiled at exactly the floor-8 target, `compiled_bonus_pct` 0.04.
- **Realized 77.3 vs equipped 52.4 = +24.9**, beating the +13.5 projection by +11.4 and the previous best (Phoenix Shell +22.6). Fourth contract-crafted main-set item. Lesson recorded in `crafting.md`: `potential` caps its plan at T3, so it systematically under-projects the upside tail of a lucky run.
- Item totals: Acc +35.93%, AtkSpd +14.00%, Eva +15.29%, **Barrier +269**, MaxHP +2.59%, AtkDmg +1.19%, CritCh +8.54% (implicit), plus global XP +7.12% / gathering XP +8.90%. Trade vs the old Analyzer: CritCh 23.10 → 8.54.
- Aligned Analyzer of Light Speed retained decompile-locked as the revert path.

## 27 July 2026 — Hardware reset executed; refund lock discovered

- Free monthly reset taken and rebought to plan: Tracking Algorithm 90, TOR Node 90, Encryption Module 90, ECC Memory 85, Overclock 21, Vulnerability Scanner 17, Malware Injector 16, Buffer Overflow 9; Packet Shield, Exploit Framework and Feedback Loop left at 0 (zero multiplicand); CPU/RAM/GPU/Network deliberately **not** rebuilt. 418 levels held vs 821 before, for strictly more combat value.
- **Mechanic discovered the hard way: reset refunds are locked to the Hardware Shop** (`locked_resources`) and can never be spent elsewhere. Full statement in `mechanics.md` §14. This invalidated the previous advisory's claim that the reset's +8 hackcoin would fund the install gates — it cannot. Material cost: nil, since 14 *free* hackcoin still covers Hacking Simulator (3) and Power & Cooling Rack (3) with 8 spare. The advisory rule now reads the install reserve off free hackcoin only.
- Locked after rebuy: 89,900 chips, 665,832 snippets, 126,811 cycles, 725,401 hashes, 169,536 packets, 8 hackcoin. At the ~2 cr/unit marketplace rate the 1.69M locked resource units are worth ≈3.4M credits — 0.03% of the 11.25B balance — while clearing them via CPU/RAM/GPU/Network would cost ≈169K chips, ~90% of the remaining chip budget. **Decision: leave them stranded; chips go to combat tracks.** Player raised the question; the arithmetic confirms it.
- Next free reset 1 Aug 2026; a paid all-hardware reset is available now for 346.6M credits, so allocation errors are cheap to undo.

## 27 July 2026 — Session retrospective: audit-first, and tooling changes

- **Standing rule added: `ih.py audit` runs before any modelling** (`CLAUDE.md` Analysis rules; `/advise` gather step 0). All three of the day's largest wins came from neglected capture fields, not better models: 4 homelab build slots idle 3.5 days (`active_jobs: []`), `stats_breakdown` closing exactly (§13 resolved), and two hardware tracks multiplying a zero gear-flat (81K dead chips). Two of the three were invisible because no `ih.py` command printed the field — **the CLI's summarisation is where the blind spots live**.
- **New `ih.py audit`** — idle slots/queue places, zero-multiplicand hardware tracks, unspent or shop-locked chips/hackcoin, finished crafts left unequipped, install-gate hackcoin reserve (free hc only), stale lazy panels. Verified retroactively: run against the 14:48 capture it flags the idle homelab and both dead tracks; against 15:44 it flags the stale panel and the unequipped Analyzer. Current capture: no anomalies.
- **Panel staleness is now detectable exactly.** `homelabInfo.server_time_ms` vs `capturedAt` gave ages of 106s / 206s / **1,348s** / 17s across the day's captures — the 1,348s one is the stale block spotted by eye. `hardwareInfo` carries no clock, so a second detector compares the `credits` each panel reports (they disagreed by 3.5B in the 15:25 capture). Both in `ihlib.panel_freshness` / `stale_panels`.
- **`ihlib` gained the models that were being hand-derived each session:** `stat_total` (three stat families; reproduces every live stat exactly), `hardware_cost_family` / `hardware_cost_curve` / `hardware_cumulative` / `hardware_plan` (equal-marginal-value chip allocation). The curve is fitted live off `next_cost` and self-validates to ~1.3–1.5% against the game's own reset refund. Fitting across cost families gave spread 13x; splitting by cost shape and excluding tracks below L10 (a low-end cost floor) brought it to 1.008.
- **Bug fixed:** `hardware_track_value` returned 0.0 rather than None for `combat_stat` effects CRAFT_WEIGHTS does not model (`item_rarity`, `drop_boost`), so Loot Filter and Drop Rate Amplifier read as "worth exactly zero" instead of "not modelled" — which the new audit surfaced immediately as two false DEAD flags.
- **New rule: before an irreversible or once-monthly action, check the fields it will *write*, not only those it reads.** `locked_resources` was all-zero pre-reset and read as inert; the reset filled it and permanently bound the refunded hackcoin to the shop, invalidating advice already given.
- Performance is a non-issue and needs no restructuring: every `ih.py` command runs in 0.03–0.06s at 23MB RSS, and `ab` aggregates 46 captures plus the 33MB stream ledger in 0.7s.

## 27 July 2026 — `potential`'s T3 tier cap removed (it was inverted)

- Player challenged the cap as arbitrary. It was worse than arbitrary: **gain per expected Stability point rises monotonically down the ladder and peaks at exactly the excluded step.** Affix value compounds ~1.4× per tier while expected attempts only grow as 10/tier, so the index runs T9→T8 0.360, T7→T6 0.549, T5→T4 0.768, T4→T3 0.861, **T3→T2 0.904 (peak)**, T2→T1 0.843. The cap removed the single best purchase available and kept the worst ones.
- The cap was also redundant: `plan_craft` is already a budget-constrained greedy that stops when the next step's expected cost exceeds remaining Stability. Depth was already limited by the thing that should limit it.
- Measured across all 50 candidate plans in the 15:57 capture: uncapping raised the best candidate in **every** slot, and flipped three verdicts — Firewall sidegrade → **UPGRADE +7.3**, Kernel inferior → **UPGRADE +5.7**, Daemon inferior → sidegrade. Titanic Router of Regeneration went +8.3 → **+22.8** (Regen 43 → ~98 projected). The expected objection — "no ladder data that deep" — is empirically false: reliance on interpolated points was **43/50 at every cap**, and some uncapped plans use *fewer* estimated points (Vital Payload of Targeting: score 47.3 → 48.3, expected spend 18.8 → 18.3, `estimated` True → False).
- **Changed:** `plan_craft(tier_cap=1)` and `ih.py potential --cap` default 1 (the game's own max). `--cap 3` reproduces pre-27-Jul numbers. `potential` now labels its output "depth set by Stability budget" and prints the contract-discount caveat in its header.
- **Calibration consequence, stated so it is not forgotten:** the cap was a systematic *under*-projection that had been partly cancelling the contract-conservatism *over*-projection (a §10.1 contract with attempt caps and a hard floor is deliberately less ambitious than the optimal plan). With the cap gone the remaining bias points one way, so the ~5-point discount matters **more**, not less. Every row of the realized-vs-projected ledger predates this change and its projected-Δ column is not comparable going forward; re-derive the discount and `UPGRADE_BAND` after the next two or three crafts.
- Two candidates surfaced by the change and now recorded in `current-state.md`, neither approved: **Titanic Router of Regeneration** (+22.8, but Def 19.33% → 0.83% — sustain-anchor rule applies to the Defense/Regen backbone) and **Bastioned Firewall of Infection** (+7.3, on the long-flagged ilvl-314 Firewall).

## 27 July 2026 — Titanic Router of the Undying: new best craft (+38.7)

- Contract executed per the 16:00 advisory. Augment (forced prefix) rolled **Elusive T9** (credits +3.08% [67%], Eva +0.60% [7%]) — weak, the Conditional class, taken as near-free upside; rarity flipped rare→epic on the 6th affix (**4/4**, open-questions §12).
- Every phase overshot its contract target. `of Regeneration` completed the **full T7→T1 chase** — `of the Undying` T1, **Regen +92 [79%]** against a projected ~78. `of Alacrity` went T8→**T3** where the contract said T6 — `of the Storm` T3, **AtkSpd +17.47% [105%]**. `of Barbs` T9→T8 as planned (Thorns +6 [100%], Eva +1.37%). Compiled at exactly the floor-8 target, `compiled_bonus_pct` 0.04. 12 promotions on ~20 attempts against ~25.8 expected.
- **Realized 85.2 vs equipped 46.5 = +38.7**, against a +22.8 projection — +15.9 above plan and 14 points past the previous best (Targeted Analyzer +24.9). Fifth contract-crafted main-set item, and the first planned under the uncapped planner.
- Swap effect: Regeneration **276.4 → 369.1 (+33.5%)**, Defense 1163.9 → 1067.3 (−8.3%), attack speed +10.6%, Max HP +2.3%, Evasion +0.6%, Accuracy −0.3%. Aligned Router of the Undying retained decompile-locked as the revert path.
- **The sustain-anchor guardrail concern did not materialise at loadout level.** The contract was approved knowing it guts the Router's Defense half; across the whole day, the morning hardware reallocation (Encryption Module 65→100) offsets it almost exactly — Defense **1064.3 → 1067.3, +0.3% net**. The guardrail should be read whole-loadout and cross-system, not per slot: a Defense loss on gear is acceptable when a hardware or homelab pool is simultaneously covering it. Recoverability asymmetry (no homelab regeneration track exists; gear is the sole regen multiplicand that ECC Memory multiplies) remains the reason to spend the slot on regen.
- Day arc, 14:48 → 16:29 (four stacked changes, deliberately unattributable): Regeneration **+53.4%**, Accuracy **+18.3%**, Evasion **+13.9%**, Barrier **0 → 279.8**, Max HP +4.3%, attack speed +10.8%, Defense +0.3%, crit chance **−38.2%**. Estimated net DPS ≈ **+5.7%** (crit factor −10.0%, offset by hit-rate gain and attack speed), so the build got both tankier and faster — the crit loss was bought back by the Alacrity overshoot.

## 27 July 2026 — Craft cost model corrected: Snapshot Backups was never modelled

- Player identified the cause of the "three lucky crafts" pattern: **Snapshot Backups is at level 2**, granting a **10% chance that a failed Version Upgrade costs no Stability** (`tier_promotion_stability_preserve` 0.05/level). `open-questions.md` §1 still recorded it as level 0 with the note that "the conservative no-backup craft budgets are exact" — written 22 July, stale by the 23rd, and every Stability budget since has been ~6% over-conservative.
- **Fixed:** `ihlib.vu_expected_stability(tier, preserve)` = `1 + ((1-p)/p) × (1-preserve)`; `ihlib.stability_preserve_chance(capture)` reads the level from the homelab definition rather than any hard-coded constant; `plan_craft` now budgets in **Stability** where it previously budgeted in **attempts**, and returns both. `ih.py potential` passes the capture-derived preserve, prints it in the header, and shows `stab ~X/~Y att`. Immediate effect: Bastioned Firewall of Infection re-ranked +7.3 → **+9.0** as the deeper plan became affordable.
- **§16 resolved, and my own reading of it was wrong.** With preserve modelled at the level live for each craft, the four contract crafts run 1.78× worse / 1.31× better / 1.40× better / 1.22× better — **geometric mean 0.944, i.e. 5.9% better than model, well inside noise at ~12 promotions each.** The documented chance table needs no revision. I had flagged "three consecutive favourable runs" as a possible mechanic while ignoring that the first craft was the worst outlier in the set; the residual after Snapshot Backups is nothing.
- **Standing lesson: a hard-coded "current level: N" in these docs is a decaying assertion.** The model was correct when written and rotted silently as the homelab advanced. Anything that reads a game system's level must read it from the capture. Applies equally to install presence, zone gates and hardware levels.

## 27 July 2026 — Bundle readout: largest ceiling move on record (+11.8, still climbing)

- The day's four stacked changes were deliberately unattributable as a set, but the death record segments cleanly at the equip boundaries:
  - **pre-bundle (14:50–15:36, n=6):** 110, 108, 114, 110, 109, 112 — **mean 110.5**
  - **post hardware + Analyzer (15:46–16:38, n=6):** 121, 113, 122, 124, 123, 131 — **mean 122.3 (+11.8)**
  - **post Router (16:49, n=1):** **133**
- **+11.8 already beats the Phoenix Shell's +7.0**, the previous record, with the Router contributing only one death so far. The ceiling has not settled.
- **Mechanism confirmed** (2,079 fights with round detail, streak ≥60): realised `prg`/round **171.3 → 194.7 → 231.8 (+35.3%)**. The hardware step tracked its listed gain almost exactly (+13.6% realised vs +14.9% listed); the Router step realised +19.1% against +33.5% listed — but the post-Router window sits at deeper streaks where in-fight regen decays harder (open-questions §11), so the shortfall is at least partly a streak confound. The `CLAUDE.md` guardrail holds: **listed Regeneration ≠ realised `prg`.**
- **Net drain per round went negative.** `damage_taken` − `prg`: **33.7 → 13.3 → −2.8** per round at streak ≥60. Regeneration now exceeds incoming damage per round in the deep-streak band; that is why the ceiling moved so far. Gross intake rose +11.7% post-Router, but that is the deeper streak band (higher-level enemies), not a mitigation failure — Defense ended the day flat.
- Both open A/Bs (Analyzer, Router) resolve **KEEP** on this evidence. Revert paths stay decompile-locked pending a settled ceiling.

## 27 July 2026 — Zone transition to Corporate Network approved

- `hackingZones` decoded into `mechanics.md` §15. **Measured:** credits per fight track enemy level at a near-constant ≈8.3–8.45 credits per enemy level across every streak band 60–129 (5,325 fights); enemy level rises ≈12 per streak. A zone's `level_offset` is therefore a **reward** multiplier as much as a difficulty one.
- Move **Small Business Server → Corporate Network** (unlocked: min level 600, player 1,037). Offset 50 → 100, soft cap 120 → 200, credits ×1.20 → ×1.35, rarity ×1.30 → ×1.50. Cost ≈ **4 streaks of depth** (50 enemy levels ÷ 12 per streak); gain ≈ **+17% credits per fight** (+12.5% multiplier, +4% from the higher enemy level) and **+15.4% drop rarity**, which matters now that the inventory has been cleared to 9 items and craft bases are the constraint on further gear gains.
- Timing agrees with the community guide's "+10% over the soft cap" rule (120 → 132) — the last two deaths were 131 and 133 — but the case does not depend on it, since the soft cap's effect is unmeasured (open-questions §17).

## 27 July 2026 — Zone change executed: Small Business Server → Corporate Network

- Player confirmed the guide's rule as "consistently reach 10% above the soft cap" = streak 132; last two deaths were 131 and 133. Independent analysis agreed (`mechanics.md` §15): cost ≈4 streaks of depth, gain ≈16% credits per fight and +15.4% drop rarity. Moved.
- **All death-streak baselines are now segmented at this change.** A zone's `level_offset` shifts enemy level at equal streak, so streaks before and after are not comparable — the pre-move ceiling of ~133 in Small Business should read as roughly ~129 in Corporate for the same build. Death records carry `zone_id`/`zone_name`; `ih.py audit` now flags any death window spanning more than one zone so a baseline cannot silently mix them.
- Side effect logged: this **closes the measurement window on open-questions §17** (what `reward_streak_soft_cap` caps). It needed fights above the cap; the new cap is 200 against streaks near 129. §17 parked, with the 34 fights banked above 120 on 27 July noted as the only sample that will exist for a long time. Accepted knowingly — progression outranks the question.

## 27 July 2026 — Crafting operation names and costs decoded; a docs-lookup failure

- Player asked whether Stabilizers are the Bias Reroll currency. They are not — **Stabilizers pay for Lock** (1 per Lock, plus `lock_cost` Credits), which `docs/crafting.md` §7 has recorded since 21 July. **I answered "I've got nothing on them" without checking our own documentation.** The workspace knew; I didn't look. Query-first applies to the docs, not only to the captures.
- The question was still worth asking — chasing it through `vendor/game-js` turned up four things the docs did not have:
  - **UI button names differ from the `crafting_preview` keys**: PRUNE is `EQUIPMENT_ANNUL`/`annul_cost`, and **REFACTOR is `EQUIPMENT_MASTERWORK`/`masterwork_cost`**. Both fields sit in every capture and would have been mis-read as unknown operations.
  - **`bias_essence_cost` = 5 × (affix count − 1)** — 20 at 5 affixes, 25 at 6, measured across all 17 items in the capture. The docs recorded a flat "20 Essence" from a 0.6.1 snapshot, which was a 5-affix observation generalised too far.
  - **Refactor's button is disabled when every effect is already at `value_max`** — independent confirmation of within-tier reroll semantics (§5).
  - **Stabilizers come from decompiling and nothing else consumes them**, so the balance is a count of remaining Locks (94).
  - The essence → affix-category mapping is server-side; the client passes only the essence name, so it cannot be decoded statically. Open-questions §3 updated to say so and now notes the test is cheap (Essence and Stabilizers are both abundant).
- `ih.py item` now prints Refactor, Prune, Bias (primary/credit/essence) and Lock costs alongside the ones it already showed, with the Stabilizer requirement and the held balance.

## 27 July 2026 — Corporate Network readout: move holds, but my cost model was wrong

- **Measured (same build either side).** Small Business post-Router: mean death streak **131.0** (n=3). Corporate Network: **113.1** (n=16). **−17.9 streaks — 4.5× the −4 I predicted.**
- **Both halves of that prediction were wrong** (`mechanics.md` §15 corrected): `level_offset` is not a simple additive term on enemy level — fitted per zone, intercept *and* slope both differ and the relationship is non-linear in streak, so the ~12 levels/streak figure taken from a handful of high-streak Small Business fights did not generalise. Worse, **enemy level is not a sufficient statistic for difficulty across zones**: Corporate deaths occur at enemy level ~1,730 against ~1,880 in Small Business, i.e. the player dies to weaker-on-paper enemies. At matched streak (≥80) Corporate enemies carry ~6% more HP, fights run ~7% longer, and the class mix differs.
- **Reward side held, and then some.** Credits per enemy level **8.81 → 11.47 (+30%)** against a `credit_multiplier` ratio of only 1.125 — zone rewards scale by more than the stated multiplier. Throughput: **credits/hr 9.78M → 11.08M (+13.3%)**, xp/hr 35.6M → 33.0M (−7.3%), chips/hr 3,207 → 2,889 (−9.9%). **Caveat: the Small Business post-Router baseline is 15 minutes / 204 fights / 3 deaths** — thin enough that only the credits-per-enemy-level figure should be trusted.
- **Verdict: keep the move.** Credits up, other axes roughly neutral, and the streak now sits at 113 against a 200 soft cap, so reward scaling is unconstrained where it was being clipped at 120 before.
- **New baseline for all future A/Bs: 113.1 mean death streak in Corporate Network** (n=16, 17:10–19:30Z). Not comparable to any Small Business figure.
- **New failure mode, minor but watch it.** 3 of 16 Corporate deaths start above 60% HP (89%, 100%, 79%); Small Business today had none above 56%. All three are high-HP tanks — Trojan Wall and Rootkit classes at 19–23K HP with 930–1,080 defense. Not burst damage (their attack is *lower* than the attrition-death enemies): the build cannot close a 23K-HP pool fast enough before in-fight regen decays (§11), so it loses from near-full HP. This is the crit sacrifice (51% → 31.5% today) showing up as a damage floor in tank matchups. Still a minority — 13 of 16 deaths remain attrition-shaped at median 38% start HP.

## 27 July 2026 — "Fill the queue" is not an action

- Player pulled me up for flagging an empty homelab queue place without saying what to put in it. Correct: a bare imperative with no object is not advice, and this workspace exists to produce actions.
- **Fixed in the tooling so the vague form is not reachable:** `ihlib.homelab_fill_suggestions(capture, limit, allow_hackcoin=False)` returns concrete jobs — name, target level, points, duration, cost — excluding gated, already-queued, unaffordable and hackcoin-costing upgrades. Both `ih.py audit` and `ih.py homelab` now print a **FILL NOW** block naming exactly what to queue.
- **Ranking rule encoded: total progress points, not points per slot-hour.** For a slot that will run unattended, the idle time after a short job costs more than its better nominal rate — a 1.0h/95pt job beats a 0.5h job rated 110pts/h outright if nobody refills at the 30-minute mark. The pts/slot-hour ordering remains in the browse list below it, where comparing rates is what you want.
- Recorded in `CLAUDE.md` (Analysis rules, first bullet) and `.claude/skills/advise/SKILL.md`.

## 27 July 2026 — UI section is part of the action, not a nicety

- Player: the recommended upgrade must **always** carry the section it sits under. The rule was already in memory ("attach the UI section/panel to every purchasable", 23 Jul) and I was following it in prose while the tooling emitted bare names — so it survived only as long as I remembered.
- `ihlib.homelab_fill_suggestions` now resolves each job's install to its display name and returns it as `section`; `ih.py audit` prints `Virtual Desktops [Command Workstation] -> L3 (…)` and `ih.py homelab`'s FILL NOW block prints `under [Command Workstation]` with the effect description.
- General form recorded in `CLAUDE.md` and the advise skill: an action is name + target + cost + duration + **where it lives**. A name without its panel still means hunting.

## 27 July 2026 — `hardware_plan` budget bug fixed

- Running the planner against a real 37,443-chip balance returned a plan costing **108,575 chips**. Cause: the bisection solved an *unconstrained* marginal-value optimum, which wants to rebalance down over-levelled tracks (Tracking/TOR/Encryption 100 → ~90) and spend the proceeds on ECC Memory. Levels cannot be sold back, so the output clamped those to their current level while the budget arithmetic had already counted the notional refund.
- Fixed: the bisection now costs only **incremental purchases** with a `max(level, target)` clamp inside the objective, so a track already above its optimum contributes zero rather than a refund. Targets also **floor** instead of rounding — rounding a fractional optimum up left the plan ~3% over budget, and a plan you cannot afford is not a plan.
- Verified across budgets: 37,443 → 32,790 spent; 100,000 → 93,286; 500,000 → 483,836, all within budget and rebalancing sensibly at the larger sizes.
- The bug was latent because the planner had only ever been run at a full-reset budget (~1.08M chips), where the unconstrained optimum sits above every current level and the clamp never binds. **Any optimiser validated only at one budget scale should be re-run at a small one before it is trusted.**
- Note the model tracking reality: ECC Memory's value/level rose 0.41 → **0.55** after the Router craft, because the hardware regen pool multiplies gear flat regen and that went 194 → 259. The planner picks it up automatically.

## 27 July 2026 — Session close: the recurring failure shape

Three separate errors today shared one cause — **a model used outside the regime it was fitted in**, each producing plausible-looking output that nothing flagged:

| Model | Fitted in | Used in | Cost |
|---|---|---|---|
| `plan_craft` T3 tier cap | never tested at all | every craft verdict since 22 Jul | excluded the two highest value-per-Stability steps on the ladder; hid a +22.8 Router and a +9.0 Firewall |
| Zone transition cost | a handful of high-streak Small Business fights | across a zone boundary | predicted −4 streaks, actual **−17.9** |
| `hardware_plan` | a ~1.08M-chip full-reset budget | a 37K-chip balance | returned a plan costing 108,575 chips |

A fourth, adjacent: Snapshot Backups recorded as "level 0" in `open-questions.md` §1 was correct when written on 22 July and rotted silently as the homelab advanced, leaving every Stability budget ~6% over-conservative for five days.

**Mitigations now standing** (`CLAUDE.md`, Analysis rules):

1. State the regime a model was fitted in; re-validate before applying it elsewhere.
2. Prefer models that **self-validate against a game-provided ground truth**. `hardware_cost_curve` checks its whole-build cumulative against the game's own reset refund figure (±1.5%) and would surface its own drift; nothing else in the toolkit has that property yet, and adding it where possible is worth more than another heuristic.
3. Read levels and state from the capture, never hard-code them — a "current level: N" in prose is a decaying assertion.
4. Exercise optimisers at both ends of their input range before trusting them.

The session's other repeated pattern: three fixes took the form **"make the tooling emit it"** rather than "remember to do it" — the FILL NOW block, the UI-section field, and `ih.py audit` itself. Standing preference confirmed: when a rule depends on the assistant remembering, move it into the tooling.

## 27 July 2026 — Session 2: the standing next craft failed re-verification

Three model defects found before spending anything. All three are the same shape the session close already named — **a model used outside the regime it was fitted in** — which means the mitigation written this morning did not yet bite. Each is now a tooling check rather than a thing to remember.

**1. Tier ladder growth is not one constant (the expensive one).** `DEFAULT_TIER_STEP = 1.4` was fitted on shallow tiers and applied at every depth. Measured within-family across all percentage affixes in the 19:54Z capture: **1.398 above T5 (n=50), 1.263 at or below it (n=25)**. Over a T6→T1 chase that is a 1.90× over-projection.

- **This reversed the advisory.** `Aegisbound Driver of Execution`, the standing "next craft" at **+14.1**, is **+4.4 — a sidegrade**, because its whole case was CritDmg reaching +81.21% at T1, extrapolated five tiers from a *single* observation (`suffix_critdamage` T6, on the item itself). Corrected projection: **+53.67%**. It would have cost ~18 Stability and the best base owned (ilvl 1605) for a sidegrade.
- Corrected field: Firewall **+9.0** (unchanged — its ladder is measured where it plans to go), Daemon +11.5 → **+8.6**, Kernel +9.5 → **+8.4**, Driver +14.1 → **+4.4**.
- Deep steps are strongly family-dependent (`suffix_attack` 1.232→1.171→1.146; `suffix_adaptive_shell` ~1.41 throughout), so an unmeasured family's deep ladder spans ~1.15–1.42 — a 2.7× spread over five tiers. `plan_craft` now returns `score_low` (same plan at the p25 deep step) and `deep_reliance`; `ih.py potential` prints both and flags verdict flips. `ihlib.fit_tier_steps` re-fits both constants from each capture so the law cannot rot. Full detail: `crafting.md` §12.1.
- **The morning's uncapping defence was wrong on its own terms.** It argued reliance on interpolated points was "unchanged at 43/50" — counting interpolated points without checking their *bias*, which was the entire problem. Uncapping to T1 stands; it just had to be priced on the correct ladder.

**2. `ihlib.stat_total` did not reproduce `attack_damage`** — it returned 0 against a real 2,050, because `attack_damage` was in none of the three stat families and fell through to the gear-flat branch (its `equipment_flat` is 0). `post_combat_heal` and the five economy stats were wrong the same way. The docstring asserted "verified against every stat in the 27 Jul 2026 capture" and had never been run against it. **This is the stat the multiplicative-AtkDmg guardrail is about.** Fixed (`mechanics.md` §13, now four families); `ihlib.validate_stat_totals` checks every stat against the game's own `total` and `ih.py audit` raises a `MODEL` flag on any miss.

**3. Chip balance was read from a stale panel.** `hardwareInfo.chips` is a snapshot from whenever the Hardware tab was last opened; `currentPlayer.chips` is live. They read **37,443 vs 44,582 — 16% low**, so the hardware plan was under-budgeted by 7,139 chips (ECC Memory L91 instead of L93). Neither existing staleness detector fired: the panel carries no clock, and cross-panel credits differed by only 0.26% because credits are 11 figures and spent in lumps while chips are small and accrue continuously. Added `ihlib.panel_currency_drift` — cross-checks every panel currency against the live `currentPlayer` values, the one ground truth available — plus `ihlib.chip_budget`, which all planning now uses. Re-run across today's captures it correctly flags five stale ones and passes the two clean ones.

**Standing lesson, sharpened.** Two of the three defects were caught by *checking a model against a number the game already provides* (`total`, `currentPlayer`). The third needed re-fitting a constant against the data it was supposed to describe. All three had been reviewed and none looked wrong in output. **Where a ground truth exists in the capture, assert against it in code; where one doesn't, re-fit rather than re-read.**

## 27 July 2026 — Session 2: actions

- **Hardware: ECC Memory L85 → L93**, 44,302 chips (x5 batch 26,932 + three singles) + ~48M credits, against a live 44,582 balance. +4.0pp regeneration pool → realized Regen 369.1 → 379.4 (+2.81%). Equal-marginal-value planner puts every spendable chip here; the next-best track is 10% worse per chip. Free hardware reset is 1 Aug (monthly UTC) and refunds chips in full, so buying now costs nothing against it.
- **No craft approved.** Corrected best candidates all land inside the sidegrade band after the ~5-point §10.1 contract discount, and the best-scoring one (Firewall +9.0) fails the sustain-anchor guardrail at loadout level: Def +6.75% / Eva +4.32% bought with **MaxHP −7.88% and Regen −5.42%**, against a build whose measured win condition is regeneration (net drain −2.8/round) — the opposite direction to the Shell A/B that this build already ran and kept.
- **Approved instead: a single measured VU step on the Aegisbound Driver's `of Execution` (T6→T5, 60%, cap 3 attempts, ~1.6 Stability of 26).** `value_min`/`value_max` are the tier's full range, so one *successful* promotion reveals the T5 midpoint exactly and pins `suffix_critdamage`'s deep step — collapsing a 1.15–1.42 spread that is worth ±10 score on the Driver verdict. Continue the full chase only if the realized T5 midpoint implies a step ≥ ~1.33 (displayed CritDmg ≳ 19.3%); otherwise stop and re-plan. Noted against `crafting.md` §12.2: the line sits at a 99% roll, so this one step is worth little as a *stat* (~+1.7pp expected) — it is bought for the measurement and for being step 1 of a chase we would run anyway.
- Homelab: 4/4 build slots and 4/4 queue places full — no action available. In-flight work lands at 9,095 points, still **905 short of homelab 10** (Hacking Simulator gate).

## 27 July 2026 — Session 3: the capture itself can be stale, and nothing checked

**The ECC Memory buy had already been made.** Session 2's headline hardware action (ECC Memory L85 → L93, 44,302 chips) was executed at ~20:44 UTC. The newest capture is 19:54Z, so it still shows 44,582 chips unspent — and `ih.py audit` duly flagged them as idle. The next advisory was one step from re-recommending a purchase already made against a balance already spent.

- Confirmed executed from the stream ledger, not the capture: **chips 45,307 → 4,140** and **Regeneration 369.1 → 379.4 (+2.79%)** across the 20:12→20:44 stats records. Session 2 predicted +2.81%. The `hardware_cost_curve` fit also self-validated on the way through: modelled cost of L85→L93 is **44,592 chips against an actual 44,302 spend (+0.65%)**.
- Every staleness detector in the toolkit compares a capture **against itself** — panel clock, cross-panel credits, panel-vs-`currentPlayer`. A capture whose panels all agree reads as clean no matter how old the whole file is. `panel_currency_drift` did fire here, but only on `hardwareInfo` being 16% behind `currentPlayer`; `currentPlayer` was itself an hour out of date and nothing could see that.
- **The auto-stream is the missing ground truth.** It keeps running after the last capture click, so its newest `stats` record post-dates the capture by construction. Added `ihlib.latest_stream_player` / `ihlib.capture_stream_drift` and an `OUTDATED` flag in `cmd_audit`: `capture is 53 min behind the combat stream (chips 44,582 -> 4,222; hack_level 1,054 -> 1,058) — recapture before spending anything`. The IDLE-chips line now carries the streamed correction on the same line, because a "spend these chips" flag off an outdated capture is exactly how a spent balance gets re-recommended.
- Discrete counters (`hack_level`, `current_zone`) compare exactly rather than on a relative tolerance — 1,054 → 1,058 is four levels of scaling, and a 1% band swallowed it.
- Exercised at both ends per the standing rule: 53 min of lag on the newest capture, 321 min on a 15:25Z one (which correctly surfaces a zone change, `small_business → corporate_network`), and `(None, [])` for a capture newer than every ledger record or carrying no timestamp.

**This is the fourth instance of the same failure shape in two days, with a new twist.** The previous three were models used outside their fitted regime. This one is a *detector* used outside its scope: three staleness checks, all sound, none of which ever claimed to validate the capture as a whole — so their collective silence read as "the capture is fine". **A sweep of internal-consistency checks cannot certify freshness; that needs a clock outside the file.**

## 27 July 2026 — Session 3: combat baseline restated

38 deaths in today's ledger: **mean peak death streak 116.2, sd 6.9, median 114.5**, no trend across the 14:00–20:00 UTC hourly buckets despite hack level rising 1,031 → 1,058 (+27). `current-state.md` still quoted a "settled 105–110" and has been corrected.

- Hourly means 114.2 / 127.6 / 117.3 / 113.0 / 113.9 / 115.0 are flat against +27 player levels, which is weak evidence that **enemy scaling tracks player level closely enough that level growth is not the death-streak confound it was assumed to be**. Not confirmed — n is 5–7 per bucket. Logged to `open-questions.md` rather than `mechanics.md`.
- Resolution floor for the ledger: se 1.12, so **~41 deaths to resolve a +3 streak shift at 80% power**. The ECC step is worth perhaps +1. Its boundary (20:44 UTC) is recorded for later segmentation, but no action is gated on reading it and no formal A/B was opened.
- Attrition remains the primary death mode: median start-HP at death 37%, with 5/38 above 70% (burst/matchup).

## 27 July 2026 — Session 4: two model defects, both found by ground-truth checks

`ih.py audit` opened with five `MODEL` flags and a `STALE` hardware panel. Both defects were in the analysis toolkit, not in the game state, and both had been silently wrong for as long as they had existed.

**1. The economy stat family is not purely additive.** `stat_total` summed every component of `credits`/`cycles`/`hashes`/`packets`/`snippets`, under-reading all five by 11–23% against the game's own `total`. `participation_bonus` (0.5) and `firewall_cache` (0.15 on gathering resources, 0 on credits) **multiply** the additive bracket:

    credits  (1 + 0.46825) × 1.5 × 1.00 = 2.20238   (game: 2.20238)
    snippets (1 + 0.06 + 0.99026) × 1.5 × 1.15 = 3.53670   (game: 3.53670)

The same capture carrying both a `firewall_cache = 0.15` case and a `firewall_cache = 0` case is what makes the two terms separately identifiable — every additive reading fails one of them. Fixed via `ihlib.ECONOMY_MULT_KEYS` / `economy_multiplier`; **all five stats now close to <1e-9 across all 58 captures in the archive**, not just the newest. Recorded in `mechanics.md` §13. Practical impact was small (econ deltas are ratios, so the error nearly cancels) — the point is that a stat family had been wrong since it was written and only the game's own `total` ever said so.

**2. Ladder amnesia — decompiling was deleting craft evidence.** Detail in `crafting.md` §12.1.1. Session 3 decompiled `Elusive Kernel of Regeneration` as a +1.7 sidegrade; it carried the only `suffix_adaptive_shell` **T7** observation owned, which is the family the Bastioned Firewall's entire plan runs through. **The Firewall verdict fell +9.0 → +4.6 with no game state changed at all** — same item, same Stability, same loadout, same hardware. A 4.4-point swing, comparable to the whole `UPGRADE_BAND`, purely from the model forgetting.

- Fixed: `ihlib.tier_ladders_archive()` unions every capture; `ih.py potential` and `fit_tier_steps` use it. **150 → 582 tier observations, 83 → 97 affix families.** `of Recovery` goes from T1/2/3/8 to T1/2/3/6/7/8/9.
- Corrected board: **Firewall +9.8** (best, and its deep plan is now inside measured data), Daemon +8.9 (low +8.4), Kernel +6.7, Driver +3.8.
- **Fifth instance of the same failure shape in three days, with a new twist: the regime moved on its own.** Nobody changed the model — a routine inventory action threw away the data underneath it. Any model fitted on *currently-owned* state carries this risk; prefer archive-wide fits wherever the underlying quantity is a game constant.

## 27 July 2026 — Session 4: actions

- **Hardware: ECC Memory L93 → L99**, ~36.2K chips (x5 batch 29,896 + one single ~6,270) + ~35M credits, against a live 36,747 balance. +3.0pp regeneration pool → realized Regen 379.4 → 387.2 (+2.05%). Equal-marginal-value planner puts the whole budget here; a greedy alternative that sprays the last ~6.6K across Overclock/Vulnerability Scanner/Buffer Overflow/Malware Injector scores identically (3.18 vs 3.18) and was rejected on direction, not size — those are output stats, and regeneration is the measured win condition. Curve self-validated: modelled 5-level cost 30,069 vs the game's own x5 batch price 29,896 (+0.6%).
- **No craft approved — third advisory running.** Firewall +9.8 is the best and now the best-*supported* ceiling on the board, and is still held on the sustain guardrail: at loadout level it buys Def +7.1% and Eva +4.3% with **MaxHP −7.9% and Regen −5.4%**. Quantified this time — −5.4% of realized regen is ≈ −12.5 `prg`/round against a measured net drain of **−2.8/round**, so the craft would flip net drain positive and give back the +20.5 death streaks the 27 July package bought. Directional (the regen → realized-`prg` proportionality is a working model, not a confirmed law), but the sign is not in doubt.
- Daemon +8.9 (low +8.4) is the nearest miss: no sustain cost, and it buys Eva +8.9% and Acc +3.2% at loadout level. Held at ~+3.9 after the §10.1 contract discount, and its unpriced cost is real — AtkSpd 30.78% → 14.92% is **−8.7% attack speed = −8.7% fights/hour**, i.e. credits, xp and chips per hour.
- Homelab: 4/4 build slots and 4/4 queue places full — no action available, unchanged from Session 2. In-flight work lands at 9,095 points, **905 short of homelab 10**.
- Still outstanding from Session 2 and not yet executed: the single measured VU step on the Aegisbound Driver's `of Execution` (T6→T5, 60%, cap 3, ~1.6 Stability of 26). The item is still at T6. With archive ladders the Driver reads +3.8, so this step is now purely a measurement buy.

## 27 July 2026 — Session 5: the Driver measurement step, and a stale rationale

**Executed:** three Version Upgrades on the Aegisbound Driver's `of Execution`. All three landed — **T6 → T3**, the affix renaming to `of Cataclysm`. Path probability 0.6 × 0.5 × 0.4 = **12%**. Stability 26 → 23 (3 spent against ~6.2 expected). Displayed CritDmg **16.67% → 32.66%**; the item's ceiling delta went **+3.8 → +9.1** (low +9.0).

**The pre-registered gate passes, by a hair.** Session 2 set it at "continue only if the realized T6→T5 step is ≥ ~1.33 (displayed T5 mid ≳ 19.3%)". Measured across the archive: `suffix_critdamage` T6→T5 = **1.3313**, displayed T5 mid **19.29%**. The family decelerates smoothly (1.400 / 1.371 / 1.377 / 1.331 / 1.307 / 1.308 from T9 down), which is why the *three-tier* geometric mean is a lower 1.315 — the gate was about the T6→T5 step specifically and that is the number to read.

**The measurement was not needed, and the advisory that recommended it was reasoning from a stale premise.** The archive-wide ladder fix made one hour earlier (Session 4) already carried `suffix_critdamage` at **T4, T5, T6, T7, T8, T9** — the family was resolved before the first click. Session 2's "buy one tier to pin the family" rationale was written under single-capture ladders, where only the item's own T6 was visible, and it was carried forward into the Session 4 advisory without re-checking it against the fix that had just invalidated it. **The action was right by accident** — 3 Stability bought +5.3 of ceiling — but the stated reason was void, and the same class of error (a conclusion outliving the model it was derived from) is the one this workspace keeps logging.

**What the +9.1 is actually made of.** Pricing the concrete contract outcomes rather than applying the blanket ~5-point discount:

| Contract | Δ vs equipped | exp. Stability | Compile left |
|---|---:|---:|---|
| A — compile now, no further VU | **−5.7** | 0.0 | +11.5% |
| B — `of Annihilation` T5→T3 only | +0.1 | 4.2 | +9.4% |
| C — B + `of Cataclysm` T3→T2 | +2.8 | 7.3 | +7.8% |
| D — C + `of Haste` T9→T4 (tool plan) | **+9.5** | 14.6 | +4.2% |

**+6.7 of the +9.5 is `of Haste` — attack speed** (CRAFT_WEIGHTS 0.9, second-highest). Crit damage, the entire reason this item was ever a project, is worth **+2.7** (C − B). The 22 July law says tempo does not move the death ceiling, so most of this score is progression rate, not depth.

**Verdict: hold — reason sharpened, not merely repeated.** At contract D and equipped, the loadout effect is **Acc −4.4% (7,568 → 7,238)**, AtkSpd +4.6%, crit factor +6.8% (CritCh 31.5% → 25.4%, CritDmg 1.509 → 1.942), Def +2.4%, MaxHP +1.5%, Corruption −34.8%, **Regen unchanged**. Net ≈ +8–9% damage throughput and +4.6% fights/hour, bought with a direct hit to bottleneck #2. It is the only top candidate with **no sustain cost** — but it is also the one whose score leans hardest on the stat this build's own law discounts, which makes it the *least* defensible of the three 8–10 band candidates to spend 15 Stability on ~5 hours before the Hacking Simulator can measure all of them. Nothing decays by waiting: the item holds T3 and 23 Stability indefinitely.

**Board after the step:** Firewall +9.8 (sustain cost), Driver +9.1/+9.0 (accuracy cost, tempo-weighted), Daemon +8.9/+8.4 (fights/hour cost), Kernel +6.7 (Defense cost). No craft approved.

## 27 July 2026 — Session 6: Driver craft APPROVED, equip deferred

**Reverses the Session 5 hold.** The hold was reasoned on the point estimate (+9.1, below the ~+10 bar, 70% attack speed). Simulating the actual contract instead of discounting it changes the answer:

| | value |
|---|---|
| mean Δ | **+8.41** |
| median Δ | +9.63 |
| p10 / p90 | +6.09 / +10.72 |
| worst observed | −5.05 |
| **P(Δ > +5, UPGRADE_BAND)** | **90.8%** |
| P(Δ > 0) | 98.5% |

100,000 runs, budget 15 Stability (23 held, floor 8), 10% Snapshot Backups preserve, per-step VU chances from the capture. Phase order matters: **Haste → Annihilation → Cataclysm** is optimal (p10 +6.09, P(>+5) 90.8%); putting Cataclysm anywhere but last costs 6–10 points of P(>+5), because it is a single 30% step and should absorb the leftover risk. All six orderings were simulated.

**Three facts the point estimate hid.**

1. **The phases are not separable.** Stability spent reduces Compile, which multiplies every explicit affix, so each phase run *alone* is worth far less than in combination — `of Cataclysm` alone is **−2.8**, `of Annihilation` alone **+0.1**, `of Haste` alone **+1.6**, all three **+9.5**. There is no hedged partial contract; the fixed Compile loss has to be cleared by the full package. The corollary is that the simulated p10 is high precisely *because* runs that stall early also spend less and keep more Compile.
2. **Stability on this item has no alternative use.** It cannot be moved to another base. Holding it earns nothing, so "wait and see" is not a free option — it is an option with zero premium and zero payoff.
3. **The downside is optional, not realized.** Δ is the crafted Driver *versus* the equipped Warmongering Driver. A bad outcome is simply not equipped; the loss is 15 Stability and ~11–19M credits (0.1–0.2% of an 11.09B balance), not combat performance.

**Crafting does not foreclose the measurement — it enables it.** The Hacking Simulator's Software Profiler runs sims against gear you own, so the crafted Driver has to exist before it can be profiled. The correct split is therefore: **craft now, equip later.**

- **Approved:** the §10.1 contract below, run now. It consumes no build slot and no real-time clock, so it does not compete with the homelab push to level 10.
- **Deferred:** the equip decision. `Warmongering Driver of Extinction` stays equipped throughout and afterwards. When homelab 10 lands (~905 pts) and the Hacking Simulator + Software Profiler are bought, profile both Drivers and equip the winner. This is a legitimate sequencing under the progression-first rule — the Simulator *changes the correct choice*, it is not being used to protect attribution.
- Unchanged holds: Firewall +9.8 (−5.4% Regen, flips net drain positive), Daemon +8.9 (−8.7% fights/hour), Kernel +6.7 (−4.5% Defense). All three spend something this build's measured model says it needs; the Driver is the only one that does not.

**Contract (locked):** Lock first (563,664 cr + 1 Stabilizer — Lock's credit price escalates 3% per Stability spent, so it is cheapest before phase 1). Phase 1 `of Haste` T9→T4, cap 12 attempts. Phase 2 `of Annihilation` T5→T3, cap 8. Phase 3 (conditional, Stability ≥ 11) `of Cataclysm` T3→T2, cap 5 — the only extrapolated step in the contract, T2 unobserved. Hard Stability floor 8. Compile last. Recapture after each phase.

Expected loadout effect at full completion, **if it later profiles well**: Acc −4.4%, AtkSpd +4.6%, crit factor +6.8% (CritCh 31.5% → 25.4%, CritDmg 1.509 → 1.942), Def +2.4%, MaxHP +1.5%, Corruption −34.8%, **Regen unchanged** — net ≈ +8–9% damage throughput and +4.6% fights/hour.

## 27 July 2026 — Session 7: Driver craft realized +16.7 — well above projection

**Executed and compiled.** `Aegisbound Driver of Cataclysm`, Stability 0/27. Realized ceiling delta **+16.7** (64.1 vs equipped 47.4) against a contract projection of **+9.5** — and above the best of 100,000 simulated runs (+11.27). Also executed: **ECC Memory L93 → L99** (chips 38,019 → 3,129, hardware levels 1,290 → 1,296, **Regen 379.4 → 387.2**, exactly the +2.05% predicted).

**What the contract said vs what happened.**

| Phase | Contract target | Landed | Roll |
|---|---|---|---|
| 1 `of Haste` | T9 → T4, ~12.3% | **T2 → `of Light Speed`, AtkSpd +22.40%** | **97%** |
| 2 `of Annihilation` | T5 → T3, ~20.7% | **T2 → `of Armageddon`, AtkDmg +25.12%** | 72% |
| 3 `of Cataclysm` | T3 → T2, ~41.5% | T3 unchanged, CritDmg 33.48% | 56% |
| Compile floor | 8 Stability (+4.0%) | **5 Stability (+2.5%)** | — |

**Why it beat projection, decomposed honestly.** Roughly two-thirds of the overshoot is *two extra tiers on the two best lines* (Haste T4→T2, Annihilation T3→T2) — the run went deeper than contracted rather than stopping at target. The rest is roll luck: the planner values a promoted affix at the tier **midpoint**, and these landed at 97% and 72%. It was paid for by **breaching the declared Stability floor** — compiled at 5, not 8, costing −1.5% Compile on every affix. Phase 3 never ran, which is exactly the trade the extra tiers bought.

**Calibration.** The standing ~5-point *downward* discount for §10.1 contract conservatism **inverted here**. That discount is fundamentally about contracts *stopping early*; when a craft does not stop early it does not apply, and the deeper tiers compound. Second craft to realize above projection (Citadel Shell, +22.6, was first) and both overshoots have the same cause. **This is not licence to drop the floor** — a run with this luck profile is rare, and at 5 Stability there is no Compile buffer left if a phase stalls. The floor stays at 8 in future contracts.

**Loadout effect on equip** (from `statsBreakdown`, formula-level):

| Stat | Before | After | Δ |
|---|---|---|---|
| Attack speed | 1.819 | 1.999 | **+9.90%** |
| Crit factor | 1.1605 | 1.2142 | **+4.62%** (CritCh 31.5%→25.4%, CritDmg 1.509→1.844) |
| Attack damage | 2,078.6 | 2,117.2 | +1.85% |
| Defense | 1,094.8 | 1,120.7 | **+2.36%** |
| Max HP | 15,011.9 | 15,224.1 | +1.41% |
| **Regeneration** | 387.2 | 387.2 | **unchanged** |
| Accuracy | 7,595.3 | 7,264.7 | **−4.35%** |
| Corruption | 24.8 | 16.2 | −34.78% |

Damage throughput **+17.1%** before the hit-rate effect, ≈ **+15%** after; fights/hour **+9.9%**.

**Decision: EQUIP — reverses the Session 6 "craft now, equip after the Simulator" split.** That deferral was reasoned at a projected +9.5 whose value was ~70% attack speed, where it was genuinely unclear whether the gain converted. At +16.7 the case changed in kind, not degree: the item is **mitigation-positive** (Def +2.4%, MaxHP +1.4%, Regen untouched — the only top candidate with no sustain cost at all), it clears `UPGRADE_BAND` by more than 3× even at a full 5-point discount, and +9.9% fights/hour is certain economic value independent of the death ceiling. The Hacking Simulator would sharpen the estimate; it would not change the sign. Progression-first: ship it.

**A/B opened: `driver-ab-2026-07-27`** (`ihlib.DRIVER_AB_2026_07_27`, now `ACTIVE_EXPERIMENT`).

- Baseline: post-package deaths, Corporate Network, streak ≥ 50, 27 Jul 17:00–21:47Z. **n=29, mean 113.8, sd 5.3, median 113, se 0.98.** Resolution ~24 deaths for +3 at 80% power.
- Baseline hit rate **80.21%** (131,725 / 32,504 over 3,304 detailed fights). **Unlike the Payload and Shell tests this is a treatment metric, not a contamination check** — this craft spends 4.35% Accuracy, so hit rate is *expected* to fall to ~78.5%. Falling materially further is the failure signal.
- **KEEP** if mean death streak ≥ 111.8 **and** fights/hour up ≥ +5%. **REVERT** if mean ≤ 108.8, or hit rate undershoots the accuracy-implied ~78.5%, or deaths starting above 70% HP rise above the baseline 5/29 (17%) — that flank is precisely what the throughput gain was bought to close.
- Revert path: `Warmongering Driver of Extinction` (ilvl 731, 0 Stability), keep locked until the A/B closes.
- Window measures a **bundle**: homelab jobs (Mechanical Keyboard L8 +1% AtkDmg, VLAN Rules L11 +1% Def, Traffic Mirror L8 +1% Eva, IDS Signatures L7) land through it, each ~+0.5% of a realized stat. Stated, not staggered.

## 27 July 2026 — Session 8: CORRECTION — fight cadence is constant; attack speed is not income

**Raised by the player, and they were right.** Several entries above priced attack speed as fights per hour. That is wrong and every instance of it is withdrawn:

> ~~"−8.7% attack speed is −8.7% fights/hour, i.e. credits, xp and chips per hour"~~ (Sessions 4–7)
> ~~"+9.9% fights/hour is certain economic value"~~ (Session 7)

**Measured from game-supplied death timestamps** (death-to-death elapsed ÷ `streak_ended`+1, Corporate Network, 27 Jul):

| hour | n | median s/fight |
|---|---|---|
| 17:00Z | 6 | 5.000 |
| 18:00Z | 6 | 4.867 |
| 19:00Z | 7 | 4.869 |
| 20:00Z | 5 | 4.872 |
| 21:00Z | 5 | 4.877 |

**n=29, median 4.872 s/fight, sd 0.053, range 4.858–5.001 → 739 fights/hour, invariant.** The Driver equip at 21:50Z raised attack speed 1.819 → 1.999 (**+9.9%**) and the next death clocked **4.87 s/fight** — no change whatsoever. Fight cadence is a fixed real-time tick; rewards per hour are set by streak depth (enemy level scales rewards), not by tempo. (A single ~2.7% step from 5.000 → 4.867 sits between the 17:00 and 18:00 buckets and is *not* attributable to attack speed — it did not recur at the 21:50 equip. Unexplained; logged to `open-questions.md`.)

**Where attack speed actually pays: rounds per fight, and it grows with depth.**

| streak band | pre-equip | post-equip | Δ |
|---|---:|---:|---|
| 60–85 | 32.7 (n=754) | 33.1 (n=26) | +1.1% (noise) |
| 86–105 | 42.0 (n=578) | 40.2 (n=20) | **−4.2%** |
| 106–130 | 50.7 (n=264) | 46.5 (n=14) | **−8.3%** |

At a fixed wall clock, fewer rounds = fewer enemy attacks = **less damage taken per fight**. Attack speed is therefore a **mitigation stat via fight-shortening**, not an economy stat. Early net-drain agrees: streak 60–85 went +69 → **−339**, streak 86–105 +770 → **+505** (confounded with the ECC regen buy in the same window).

**Consequences.**

1. **The `driver-ab-2026-07-27` keep rule was unsatisfiable and has been amended** — before any post-equip death was scored, so no rule was changed after seeing an outcome. "fights/hour up ≥ +5%" → "rounds/fight at streak ≥ 86 down ≥ 4% vs pre-equip (42.0 at 86–105, 50.7 at 106–130)". Rounds/fight is the real mechanism and is already measurable.
2. **The Daemon hold's stated cost was wrong, and the correction makes it stronger, not weaker.** Losing 8.7% attack speed is not lost income; it is lost attrition resistance. `Sighted Daemon of the Storm` buys evasion by spending fight-shortening — the wrong direction for an attrition-bound build. Hold stands on better grounds.
3. **The 22 July "tempo does not move the death ceiling" law is now in question.** If rounds/fight falls 8.3% at depth and damage taken scales with rounds, tempo *is* an attrition stat. `CRAFT_WEIGHTS_PCT` gives AtkSpd 0.9, which this would vindicate — the Session 5 complaint that the Driver's score "leaned on a stat the build's own law discounts" was arguing from a law that may itself be wrong. **Not confirmed**: n is small at depth (14–20 fights) and the ECC regen buy is inside the same window. Logged to `open-questions.md`; the running A/B tests it directly.

**Standing lesson, sixth entry.** This one was not a model used outside its regime — it was a **quantity never measured at all**. "Attack speed → fights per hour" was asserted, propagated through four sessions of advice, priced into two craft verdicts and written into an A/B keep rule, and the ledger had the data to falsify it the whole time. **Before a quantity enters a verdict, check whether anything has ever measured it.**

## 27 July 2026 — Session 9: the Accuracy cut cost nothing, and the keep rule is mis-specified

**`driver-ab-2026-07-27` at 2/24 deaths: 119, 120** (baseline mean 113.8) → **+5.7**. Far too early to read, but both post-equip deaths sit above all but four of the 29 baseline values.

**Finding: −4.35% Accuracy produced NO hit-rate loss.** Matched on streak band, so enemy-evasion composition is controlled:

| streak band | pre n | pre hit | post n | post hit | Δ | z |
|---|---:|---:|---:|---:|---:|---:|
| 60–85 | 38,626 | 80.37% | 3,144 | 81.27% | **+0.89pp** | +1.23 |
| 86–105 | 37,348 | 78.11% | 2,723 | 79.58% | **+1.47pp** | +1.84 |
| 106–130 | 20,425 | 76.71% | 2,328 | 78.39% | **+1.69pp** | +1.87 |

Accuracy went 7,595 → 7,265. A roughly linear hit model predicts **−1.7pp**; every band moved *up* instead, consistently, on 8,195 post-equip attacks. Player levelling explains at most +0.3% of accuracy over the window — nowhere near enough.

**Consequence: accuracy is in heavy diminishing returns at this build's level, and "bottleneck #2 = hit reliability" is stale.** `CRAFT_WEIGHTS_PCT` prices Acc at **1.0**, joint-highest with Def and Eva. If accuracy is saturated that weight is too high, and two live verdicts lean on it — the Daemon (+8.9, case partly Acc +3.2%) and any future Payload work. Not yet confirmed (the *rise* is unexplained and only marginally significant); logged to `open-questions.md`. The 22 July note that "the exact hit-chance formula has not been established" now has a concrete constraint: it is flat in accuracy in the 7.2–7.6K region against Corporate Network evasion.

**Rounds/fight: directionally right, smaller than first measured.** With the sample grown from 14–20 fights to 61/40/20/9:

| band | pre | post | Δ | z |
|---|---:|---:|---:|---:|
| 60–85 | 32.7 | 31.1 | **−5.0%** | −2.27 |
| 86–105 | 42.0 | 41.0 | −2.3% | −0.99 |
| 106–115 | 49.8 | 47.9 | −3.7% | −1.21 |
| 116–130 | 53.9 | 52.7 | −2.3% | −0.50 |

The **−8.3% at 106–130 reported in Session 8 was small-sample noise**; the real effect looks like −2% to −5%, significant only in the shallowest band. `mechanics.md` §14 is amended accordingly — the *direction* (attack speed shortens fights in rounds) holds, the magnitude was overstated.

Net drain improved substantially over the same window: streak 60–85 **+69 → −273**, streak 86–105 **+770 → +488**; realized regen/round 234.2 → 262.9. Confounded with the ECC Memory buy and homelab jobs landing inside the window.

**The keep rule I wrote is mis-specified, and I am NOT amending it again.** It reads "KEEP if mean death streak ≥ 111.8 **AND** rounds/fight at streak ≥86 down ≥ 4%". That makes a *mechanism* metric a necessary gate on a *primary outcome* metric — so an item delivering +5.7 death streaks via some other mechanism would score REVERT. That is wrong, but the rule was set before data and amending it now, with the primary metric running strongly positive, is exactly the goalpost-move A/B discipline forbids. **Standing resolution: at readout the primary (mean death streak) governs; the rounds/fight clause is recorded as a diagnostic that was mis-declared as a gate.** Stated in advance, in writing, before the result.

**Lesson for future keep rules:** a keep rule may gate on the outcome and on contamination checks. It must not gate on the *mechanism you guessed*, because being right about the effect and wrong about why is the normal case.

## 27 July 2026 — Session 10: learnings folded into the library

Everything below was living only in prose from Sessions 4–9. It is now code, so it applies automatically rather than by remembering to apply it.

**New in `ihlib`.**

- `tier_ladders_archive()` — unions affix-tier observations over **every** capture (150 → 582 observations, 83 → 97 families). `ih.py potential` and `fit_tier_steps` use it. Kills the ladder-amnesia class of bug entirely: decompiling can no longer delete evidence.
- `economy_multiplier()` / `ECONOMY_MULT_KEYS` — `participation_bonus` and `firewall_cache` multiply the economy additive bracket. All five economy stats now close to <1e-9 across all 63 captures; `ih.py audit` is clean of `MODEL` flags.
- `score_tiers(item, ladders, tiers, stability_left)` — prices a **specified** tier assignment (companion to `plan_craft`, which *chooses* one greedily). Correctly excludes the implicit from Compile, which the ad-hoc script used for the Driver decision got wrong by ~0.35 points.
- `simulate_contract(...)` — Monte-Carlos a §10.1 contract and returns the outcome distribution, including `p_upgrade` and `p_complete`. **Validated against the Driver decision it was extracted from**: `p_complete` 65.6% vs 65.6%, `P(Δ>+5)` 90.6% vs 90.8%.
- `best_contract_order(...)` — permutes phases. Reproduces the finding that an expensive low-probability step belongs last (90.6% vs 80.9% on identical phases).
- `fight_cadence()` — s/fight from the game's own death clock. Deliberately does **not** use the stream's `seen_ms`, because pooling those gaps re-measures the 150 s polling interval — which is exactly how this nearly went wrong a second time.

**New in `ih.py`.** `contract ITEM [--phase 'of Haste:4'] [--order] [--floor N]` and `cadence`. `MECH_BRACKETS` gains **106–130** — deaths land at 113–120, so every bracket stopping at 105 was blind to the band where runs actually end. `ab` now prints **hit rate per bracket**, because the pooled comparison measures streak composition, not accuracy; that per-band readout is what falsified the accuracy prediction and it took three hand-rolled scripts before it became tooling.

**`CRAFT_WEIGHTS_PCT` annotated, values deliberately unchanged.** `AtkSpd 0.9` (right number, wrong reason — mitigation via fight-shortening, not income) and `Acc 1.0` (probably too high — saturated). Moving weights mid-A/B would break `driver-ab-2026-07-27`'s comparability with its own baseline. Resolve with the Software Profiler, then re-weight.

**Four standing lessons added to `CLAUDE.md`.**

1. Before a quantity enters a verdict, check whether anything has ever measured it.
2. A model fitted on *currently-owned* state rots when the inventory turns over — prefer archive-wide fits for game constants.
3. An A/B keep rule may gate on the outcome and on contamination checks, never on the mechanism you guessed. Amend only for impossibility, never after a favourable result.
4. Judge a close craft by simulating the contract, not by discounting it.

**A/B at 3/24: mean 120.3 vs 113.0 (+7.3).** Watch the new 106–130 bracket — it is the only one that looks *worse* post-equip (net drain 1539 → 1789, rounds 49.6 → 50.1 flat) while every shallower bracket improved. n=46, and it is exactly the band where the run ends, so it is the number that decides this test.

## 28 July 2026 — Session 11: the Compile floor was the bug, and credits were never scarce

**Firewall crafted and finished: `Resilient Firewall of Perpetuity`** (base: Hearty Firewall of Immortality, ilvl 1384, epic). Contract approved at ceiling +16.8 with `simulate_contract` P(Δ>+5) 99.4%, P(Δ>0) 100%, mean +15.1, p90 +18.9. **Realized +44.6** — more than double the p90, and the largest craft delta on record (previous best: Titanic Router of the Undying, +38.7).

The overshoot was not luck alone. The contract was written to the standing **Compile floor of 8**; the player crossed it and ran to 1 Stability, landing `of the Undying` T1 (Regen +77), `of Perpetuity` T1, `Aegisbound` T3 and `Spectral` T5 against planned T3/T1/T6/T7, plus an Augment (`of Piercing` T9, ArmorPen +10). Loadout effect on equip: **Regen 388.5 → 504.0 (+29.73%)**, MaxHP +2.96%, Eva +4.39%, **Def −6.05%**, AtkDmg −1.21%.

**The floor-8 rule was wrong and has been replaced (`ihlib.COMPILE_FLOOR = 2`).** Compile pays 0.5%/point across all affixes; one deeper tier step multiplies one affix by 1.26–1.40×, and affix value is concentrated in one or two lines. A floor sweep over three live candidates found lower better on **mean, median, p10 and p90 in every case**, worst case flat: Assault Kernel +14.9 → +26.3, Titanic Firewall +15.5 → +28.3, Untouchable Payload +11.0 → +19.0. Compile's resource price also falls with the floor (49,999 at 1 Stability vs 1,249,951 at 25). See `crafting.md` §3.

This suppressed **every** craft verdict in the workspace by ~11–13 points — more than `UPGRADE_BAND` itself — so pre-28-July sidegrade rejections were mis-ranked, not merely mis-scored. Re-ranked board: Assault Kernel of Corruption +26.0, Bulwarked Driver of Velocity +22.4, Untouchable Payload of Lightning +18.7, Deadeye Kernel of Containment +19.8, Targeted Router of Immortality +14.1, Sighted Daemon of the Storm +14.0.

**Standing lesson, seventh entry.** `floor=8` was a plausible default written once, never exercised at either end of its range, and then inherited by `plan_craft`, `simulate_contract`, `ih.py potential` and every verdict for six days. Identical shape to the T3 tier cap and to "attack speed → fights per hour". **A default is a model. Exercise it at both ends before trusting anything built on it.**

**Corruption measured, not assumed.** `CRAFT_WEIGHTS_FLAT["Corrupt"] = 0.6` was fitted on one fight at 12 points claiming ~1% of output per point. The ledger (9,000+ detailed fights; Corruption naturally varying 12.06 → 23.11 → 24.84 → 16.20 across 22–28 July) gives **~0.5%/point in the deep bands, and the response is not linear** — a 35% stat cut moved corruption's share of output by 0–36% depending on band. The weight lands near-right *relative to AtkDmg* by luck ("deliberately conservative"), but its stated rationale is ~2× off and it must not be applied above ~25 points. Two candidates scored as upgrades purely on it (Vital Firewall of Mending +22.1 → −1.1 ex-Corruption; Deadeye Kernel of Containment +16.2 → −1.3, and it costs −14.7% Regen). Logged to `open-questions.md`.

**Credits were never the constraint — hackcoin is, and it converts.** The credit balance fell 22.99B → 5.74B in six days against ~12M/hr fight income, which read as a depleting stock with ~1 day of runway; on that basis this session initially recommended **deferring the Hacking Simulator** and switching the homelab to credit-efficient jobs. The player then supplied the missing fact: **hackcoin sells at ~8,332,642,927 credits each**, and 28 are held. That is a ~233B credit budget. The recommendation was withdrawn the same session.

Consequences recorded in `CLAUDE.md`: price everything in **hackcoin-equivalents** (`ihlib.hackcoin_equivalent`), spend credits freely, and rank by hackcoin cost. The Hacking Simulator is 0.60 + 3.00 = **3.60 hc**; Software Profiler L1 is 1.12 hc; homelab 10→13 is ~0.60 hc. The whole roadmap is ~10.6 hc of 28 — there is no XOR. Newly visible at this rate: **ASIC Subsystem [GPU Rig]** at 10B cr + 1 hc = **2.20 hc** for +1 hackcoin per board reset per level, which was invisible while 10B looked prohibitive.

**Two audit checks added** (`ihlib.contract_board`, `ihlib.credit_runway`, `ihlib.hackcoin_equivalent`). The sweep had no contract check at all: the live board held an Extended Elimination at 658/1,424 worth **4 hackcoin** with 2.5h before a hard UTC reset that destroys unfinished progress, and contracts are the only observed repeatable hackcoin source. `credit_runway` counts hackcoin at the exchange rate and the audit now flags the **hackcoin** reserve against install gates rather than the credit balance.

**`driver-ab-2026-07-27` closed: KEEP.** 13/24 deaths, mean 120.2 vs baseline 113.8 → **+6.4**, Welch t ≈ 3.8; keep threshold ≥111.8. Per the standing resolution logged 27 July the primary metric governs; for the record the mis-declared rounds/fight clause would have failed (40.0 vs 40.5 at streak 86–105; 50.4 vs 49.6 at 106–130, i.e. up). Hit rate 80.8% vs 80.2% — no Accuracy damage, consistent with saturation. **Stopped at 13/24, not 24**: the pre-registered n was powered for +3 and the observed effect is 2×, and the Firewall craft makes every further death uninterpretable as a Driver test. Reason recorded before the craft, not after. Releases `Warmongering Driver of Extinction` from decompile-lock.

### Session 11 meta: every error was in an inherited number

Worth separating from the findings above, because the pattern recurred four times in one evening and all four look identical in hindsight.

**The three defects this session — `floor=8`, `Corrupt=0.6`, "credits ≈ unlimited" — plus the near-miss on chips, were all numbers inherited rather than measured.** Each was written once by a previous session, looked reasonable in output forever after, and was then relied on by everything downstream. This is the same shape as the T3 tier cap (Session 8), the zone transition cost (Session 8) and "attack speed → fights per hour" (Session 8). The workspace keeps rediscovering it because the lesson is recorded as prose to remember rather than as a check that runs.

Three specific process failures, recorded so they are not repeated:

1. **Topic-scoped vigilance.** The session's entire theme was "two of the three top-scoring candidates are artifacts of untested weights" — written while passing the untested `floor=8` into the same `plan_craft` call. Auditing one class of assumption produced blindness to a structurally identical one in the same line of code. **When auditing any inherited constant, audit every constant in that call.**

2. **A decision-critical unknown was recorded as a caveat instead of resolved.** The advisory stated that the unexplained +22.25B credit windfall "decides whether the Hacking Simulator is ever affordable" — and then shipped a recommendation that assumed an answer. The correct move was to ask. See the new `CLAUDE.md` rule.

3. **A spend was recommended without its denominator.** 133,530 chips went into an advisory with no measurement of chip income (~5,584/hr — i.e. 24 hours of it). The player's "chips are also scarce" forced the measurement, and the measurement changed the answer: ECC out-earns every other track until L130, so under a constraint the correct allocation is all-ECC, not the split that had been recommended to hedge an unsized Defense risk.

**What went right, and is worth repeating.** The two weight defects were caught by looking for **natural variation already present in the archive** rather than by reasoning about the weights. Corruption had run 12.06 → 23.11 → 24.84 → 16.20 across six days with the ledger recording throughout — a free natural experiment nobody had run. The method: segment by the stat's own change-points, match on streak band, normalize against a co-scaling quantity so player growth cannot masquerade as effect. **Score decomposition** (splitting a ceiling Δ into per-stat contributions) is what made the artifacts visible at all; a single scalar hides which weight is carrying it, and `ih.py potential` should arguably print it.

**And the contract was beaten by the player.** The §10.1 contract is a floor, not a ceiling. the player crossed the Compile floor against written instructions and produced the best craft on record (+44.6 against a p90 of +18.9), which is what exposed the defect. **Treat deviations from a contract as experiments, and check what they reveal about the model before treating them as protocol errors.**

**Register built, same session (`ih.py assumptions`).** The meta-lesson above said the workspace keeps rediscovering the inherited-number failure "because the lesson is recorded as prose to remember rather than as a check that runs" — and was then itself about to be filed as prose. `ihlib.assumptions()` now registers all 24 tunable constants with provenance (`measured`/`asserted`/`inherited`/`supplied`), the date each was last validated, and a live re-check where one is possible. Current state: **9 asserted, 5 inherited, 1 supplied, 9 measured — 14 have never been tested against game data.** `UPGRADE_BAND` and `INFERIOR_BAND` are flagged stale (calibrated under the old floor). `CRAFT_WEIGHTS_PCT["Acc"]` is flagged as free to move now that the Driver A/B has closed. Wired into `CLAUDE.md` and the `advise` skill so it runs rather than being remembered.

It justified itself immediately: the live checker for `CREDITS_PER_HOUR` reported 0.8M/hr against a 12M/hr constant, and the defect was in the **checker** — it divided ledger rewards by the ledger's full timestamp range, which spans six days of wall clock over ~13 hours of play. That is the same trap `fight_cadence` carries a warning about (pooling `seen_ms` measures the poll interval, not the thing). Now gap-aware and reporting 8.9M/hr. A validator is itself an inherited number waiting to happen; the register catching its own author's new code on the first run is the strongest argument for having it.

## 28 July 2026 — Session 12: Firewall equipped, chips spent, first readout

**Equipment change: `Resilient Firewall of Perpetuity` equipped ~22:08Z**, replacing `Brutal Firewall of Perpetuity` (ilvl 314, the last low-ilvl sustain anchor and the weakest slot since 22 July). Seven of eight slots are now contract crafts; only the Kernel baseline remains. Loadout effect on equip: **Regen 388.5 → 504.0 (+29.7%)**, MaxHP +2.96%, Eva +4.39%, **Def 1,235.3 → 1,160.5 (−6.05%)**, AtkDmg −1.21%, ArmorPen 0 → 10.

**Scarce spend: 133,409 chips** — ECC Memory L100 → L110 and Encryption Module L100 → L110 (~133M credits alongside). This was the earlier split recommendation rather than the later all-ECC revision; both were live in the same session and the split is the one that shipped. End state vs pre-craft: **Regen +34.1%, Def −3.4%** — the hardware covered most of the craft's Defense loss, which is better than the −6.05% projected. Chips 135,757 → 2,348.

**A/B opened: `firewall-ab-2026-07-28`** (`ihlib.FIREWALL_AB_2026_07_28`, now `ACTIVE_EXPERIMENT`). Baseline is the Aegisbound-Driver era only (n=16, mean 119.8, sd 4.3 — n=16 resolves +3 at 80% power); target 24 deaths. **The keep rule gates on the outcome and on contamination checks only.** Realized `prg`/round and net drain per round are named in the rule as *diagnostics that are not gates* — the explicit correction of the `driver-ab-2026-07-27` mis-specification. `driver-ab-2026-07-27` marked concluded in the same change, with its readout stored on the record.

**First readout at 3/24 deaths — not readable, and said so.** `115, 132, 133` vs baseline 119.8. With sd 4.3 the standard error on three deaths is ±2.5; the two 130s are encouraging and the 115 is not, and neither is evidence.

**The mechanism, however, is already readable at 323 detailed fights**, which is the useful asymmetry: net drain per round, matched on streak band, improved in every band — 60–85 **−117 → −383**, 86–105 **+553 → +276**, 106–130 **+1,723 → +887**. Net drain at depth roughly halved but remains positive, so this predicts a higher ceiling rather than an unbounded one. Controls clean: hit rate 80.3% vs 81.0% (the craft moves Accuracy +0.30%, so this is a contamination check), rounds/fight 50.5 → 51.1 flat as expected with no attack-speed change, same zone throughout.

**The window measures a bundle by policy, not oversight** — craft, both hardware buys, two player levels and Mechanical Keyboard L10. Stated, not staggered.

**Two findings logged to `open-questions.md`.** (1) **Realized regeneration is not flat in listed regeneration** — a +29.7% listed buy realized +0.4% / +4.7% / +11.5% of `prg`/round across streak bands 60–85 / 86–105 / 106–130, rising monotonically with depth. Working model: overheal capping. First evidence of diminishing returns on the build's confirmed win condition, and the reason the standing chip advice caps ECC instead of spending the whole budget. (2) **First isolated read on Defense** — gross damage/round at depth 349.0 → 368.6 (+5.6%) against Defense −6.05%, roughly 1:1. `damage_taken` is gross intake, which regeneration does not touch, so the Firewall's opposite-signed Def/Regen move is what made this readable at all. Both weights updated in `ihlib.assumptions()` so the register carries the new evidence rather than the old claim.

**Tooling fixed.** `ih.py ab` was still reporting the closed Driver test as active and folding Firewall-era deaths into its post-equip window. Also fixed a crash in `experiment_status` when an experiment carries no `boundary_fight_id` — that field only disambiguates the single capture straddling an equip, and is meaningless when the equip was not caught mid-session.
