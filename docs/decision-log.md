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
