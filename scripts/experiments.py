"""The campaign record: pre-registered A/B experiment declarations.

This module is DATA, quarantined from the analysis library on purpose: every
dict below is one campaign's pre-registered experiment — the gate written
before the gear change, the frozen baseline, the falsifiable mechanism
predictions, and (once closed) the concluded verdict. The reading logic lives
in ihlib (`experiment_status` / `experiment_mechanism`); nothing in here
computes.

Fresh campaign? Replace the declarations with your own and point
ACTIVE_EXPERIMENT at the live one (or None while nothing is declared —
`ih.py ab` reports "no active experiment"). Concluded experiments stay
importable for retrospective analysis and as worked examples of the
declaration format. ihlib re-exports every name in __all__, so both
`ihlib.ACTIVE_EXPERIMENT` and `experiments.ACTIVE_EXPERIMENT` work.
"""

__all__ = [
    "PAYLOAD_AB_2026_07_23", "SHELL_AB_2026_07_23", "DRIVER_AB_2026_07_27",
    "FIREWALL_AB_2026_07_28", "PAYLOAD_AB_2026_07_30",
    "FIREWALL_AB_2026_07_31", "SHELL_AB_2026_07_31", "DRIVER_AB_2026_08_03",
    "ROUTER_AB_2026_08_06", "SHELL_AB_2026_08_07", "ROUTER_AB_2026_08_09",
    "ACTIVE_EXPERIMENT",
    "RESERVED_PROBES",
]

PAYLOAD_AB_2026_07_23 = {
    "concluded": "KEEP — 23 Jul 2026 (death ceiling +2.3, hit 76.9% vs "
                 "70.1%); see docs/decision-log.md",
    "name": "payload-ab-2026-07-23",
    "item": "Bastioned Payload of Perfect Strike",
    "slot": "Payload",
    # compile+equip happened between the 08:28:42 and 08:32:02 captures
    "equip_ms": 1784795400000,          # 2026-07-23T08:30:00Z
    "boundary_fight_id": 169,            # last pre-equip fight id
    # pre-equip deaths observed 23 Jul 07:37-08:29 (old Payload)
    "baseline_deaths": [89, 96, 96, 98, 90, 96, 94],
    # pooled deep-streak hit counts from the 21 Jul legacy loss exports
    # (data/combat/*, old Payload, enemy eva ~2475-2543)
    "baseline_hits": (115, 49),
    "target_deaths": 10,
    # same-loadout-era baseline window (23 Jul 00:00Z); older deaths span
    # pre-Daemon-craft loadouts and only give a wide-context mean
    "baseline_recent_ms": 1784764800000,
    # VLAN Rules L10 (+1% Def) build completion — segment deaths after this
    "segment_ms": 1784800600000,        # ~2026-07-23T09:57Z (estimated)
    "segment_label": "the VLAN Rules L10 +1% Def",
    "keep_rule": "mean death streak +2 or better vs baseline 94.1, or "
                 "material miss-rate drop vs Mirrored; revert if depth flat "
                 "AND fights ~10% slower",
}

SHELL_AB_2026_07_23 = {
    "concluded": "KEEP — 23 Jul 2026 (death mean 104.3 vs 97.3, +7.0; last "
                 "four deaths 109-111; net drain and attrition onset both "
                 "improved); see docs/decision-log.md",
    "name": "shell-ab-2026-07-23",
    "item": "Citadel Shell of the Phoenix",
    "slot": "Shell",
    # compile+equip happened between the 10:19:57 and 10:33:09 captures
    "equip_ms": 1784802360000,          # 2026-07-23T10:26:00Z
    "boundary_fight_id": 515,            # last pre-equip fight id (10:19 capture)
    # payload-era deaths (post-Payload-equip 08:30Z, pre-Shell-equip), n=14
    "baseline_deaths": [97, 93, 97, 101, 96, 100, 101, 101, 101, 98, 97,
                        95, 92, 93],
    # payload-era detailed-fight hit counts (ph, pm) from the stream ledger;
    # the Shell does not touch Accuracy — a hit-rate shift flags contamination
    "baseline_hits": (17151, 4862),
    "target_deaths": 10,
    "baseline_recent_ms": 1784795400000,  # Payload equip — same-loadout era
    # VLAN Rules L10 (+1% Def) completes mid-test — segment deaths after this
    "segment_ms": 1784805060000,        # ~2026-07-23T11:11Z (estimated)
    "segment_label": "the VLAN Rules L10 +1% Def",
    # Damage clause amended at 4/10 deaths (23 Jul ~11:15Z, logged): the
    # original "damage taken/fight <= +5%" measured GROSS intake, which must
    # rise when trading Def/Barrier for Regen and ignores the recovery the
    # craft buys; also pre-era damage_taken includes ~300-700/fight of
    # barrier soak that never touched HP. Replaced with net drain.
    "keep_rule": "KEEP if mean death streak >= 96.3 (baseline 97.3 - 1) AND "
                 "net drain/fight (damage_taken - in-fight prg - barrier "
                 "soak) <= +5% at matched bracket AND attrition onset not "
                 "earlier; REVERT if mean < 95.3, net drain worse than +5%, "
                 "or high-accuracy burst deaths dominate (Def 28.4->12.2, "
                 "Barrier 221->0 is the exposed flank)",
}

DRIVER_AB_2026_07_27 = {
    "name": "driver-ab-2026-07-27",
    "item": "Aegisbound Driver of Cataclysm",
    "slot": "Driver",
    # crafted and compiled by 21:46:57Z; equip immediately after
    "equip_ms": 1785189000000,          # 2026-07-27T21:50:00Z
    "boundary_fight_id": 114,            # last pre-equip fight id (21:46 capture)
    # post-Analyzer/Router/hardware-package deaths, Corporate Network only,
    # streak >= 50 (drops one 6 from a zone switch and one 129 pre-package
    # outlier), 27 Jul 17:00Z -> 21:47Z. n=29, mean 113.8, sd 5.3, se 0.98.
    "baseline_deaths": [110, 114, 117, 107, 120, 117, 111, 105, 112, 123,
                        113, 108, 114, 113, 110, 116, 121, 107, 109, 107,
                        118, 112, 117, 116, 112, 122, 120, 122, 106],
    # pooled detailed-fight hit counts over the same window. UNLIKE the
    # Payload/Shell tests this is NOT a contamination check -- this craft
    # spends Accuracy (-4.35%), so hit rate is a TREATMENT metric and is
    # expected to fall. It falling further than the accuracy cut implies is
    # the failure signal.
    "baseline_hits": (131725, 32504),   # 80.21% over 3,304 detailed fights
    "target_deaths": 24,                # ~24 to resolve +3 at 80% power (sd 5.3)
    "baseline_recent_ms": 1785164400000,  # 27 Jul 17:00Z -- same-loadout era
    # Homelab jobs land through the window (Mechanical Keyboard L8 +1% AtkDmg,
    # VLAN Rules L11 +1% Def, Traffic Mirror L8 +1% Eva, IDS Signatures L7).
    # Each is ~+0.5% of a realized stat -- inside the noise, but the window
    # measures a BUNDLE and is not a clean single-item read. Stated, not fixed.
    # None, NOT equip_ms. Declaring the boundary AT the equip made the
    # `ended_at_ms >= segment_ms` test true for every post-equip death, so
    # the readout told the reader to analyse the whole window separately --
    # the same false-contamination bug fixed in code on 7 Aug 2026, written
    # in data. "No mid-test segment" is spelled None.
    "segment_ms": None,
    # Amended 27 Jul 22:0xZ, BEFORE any post-equip death was scored: the
    # original clause read "fights/hour up >= +5%", which is unsatisfiable --
    # fight cadence is a fixed 4.872 s/fight (n=29, sd 0.053, invariant across
    # every loadout change today including this +9.9% AtkSpd equip). Attack
    # speed pays in ROUNDS per fight, not fights per hour. Replaced with the
    # real mechanism, which is also already visible: rounds/fight -8.3% at
    # streak 106-130, -4.2% at 86-105.
    "keep_rule": "KEEP if mean death streak >= 111.8 (baseline 113.8 - 2) AND "
                 "rounds/fight at streak >=86 down >= 4% vs pre-equip "
                 "(42.0 at 86-105, 50.7 at 106-130); REVERT if mean <= 108.8, "
                 "or if rounds/fight is flat at depth, or if hit rate "
                 "falls materially below the ~78.5% the -4.35% Accuracy cut "
                 "implies, or if deaths starting above 70% HP RISE above the "
                 "baseline 5/29 (17%) -- that flank is what the +17% "
                 "throughput was bought to close",
}

DRIVER_AB_2026_07_27["concluded"] = (
    "KEEP, 28 Jul 2026. 13/24 deaths, mean 120.2 vs baseline 113.8 (+6.4), "
    "Welch t~3.8 against a keep threshold of 111.8. Stopped at 13 of a "
    "pre-registered 24 because the Firewall craft made every further death "
    "uninterpretable as a Driver test -- reason recorded before the craft, not "
    "after. The rounds/fight clause would have FAILED (40.0 vs 40.5 at 86-105; "
    "50.4 vs 49.6 at 106-130, i.e. up); per the standing resolution logged 27 "
    "Jul the primary outcome governs and that clause is a mis-declared "
    "diagnostic. Hit rate 80.8% vs 80.2% -- the -4.35% Accuracy cut cost "
    "nothing, consistent with saturation.")

FIREWALL_AB_2026_07_28 = {
    "name": "firewall-ab-2026-07-28",
    "item": "Resilient Firewall of Perpetuity",
    "slot": "Firewall",
    "equip_ms": 1785276480000,          # 2026-07-28T22:08:00Z
    "boundary_fight_id": None,
    # Aegisbound-Driver era only (that A/B closed KEEP), Corporate Network,
    # streak >= 50. n=16, mean 119.8, sd 4.3 -> n=16 resolves +3 at 80% power.
    "baseline_deaths": [110, 116, 116, 117, 119, 119, 119, 119, 119, 119, 120,
                        122, 123, 124, 126, 129],
    # The Firewall moves Accuracy by +0.30%, so hit rate is a CONTAMINATION
    # check here, not a treatment metric -- unlike the Driver test.
    "baseline_hits": (35163, 8238),     # 81.02% over 821 detailed fights
    "target_deaths": 24,
    "baseline_recent_ms": 1785189000000,   # Driver equip -- same-loadout era
    # The window measures a BUNDLE by explicit policy, not by oversight:
    # ECC Memory L100->L110 and Encryption Module L100->L110 (133.4K chips)
    # landed ~20 min after the equip, plus 2 player levels and Mechanical
    # Keyboard L10. End state vs pre-craft: Regen +34.1%, Def -3.4%.
    "segment_ms": 1785277800000,        # ~22:30Z, the hardware purchase
    "segment_label": "the ECC+Encryption 133.4K-chip",
    # Gates on the OUTCOME and on contamination only. Realized prg/round and
    # net drain are recorded as DIAGNOSTICS and are explicitly NOT gates --
    # that is the mis-specification driver-ab-2026-07-27 made.
    "keep_rule": "KEEP if mean death streak >= 117.8 (baseline 119.8 - 2); "
                 "REVERT if mean <= 114.8. Contamination checks only: hit rate "
                 "must stay near 81.0% (this craft moves Accuracy +0.30%, so a "
                 "material move means something else changed), the window must "
                 "not span a zone change, and deaths starting above 70% HP "
                 "must not rise above the baseline 2/16 (13%) -- Defense fell "
                 "6.05% on equip before hardware restored part of it, and "
                 "burst is the exposed flank. Realized prg/round and net drain "
                 "per round are DIAGNOSTICS, not gates.",
    "concluded": "2026-07-30 KEEP — mean 140.2 over 89 deaths vs gate 117.8 "
                 "(+20.4 streaks). Bundle window by policy: 87/89 deaths after "
                 "the VLAN +1% Def segment, plus the 29 Jul Kernel and Daemon "
                 "crafts. Hit rate 79.7% vs 81.0% baseline attributed to the "
                 "bundle, not the Firewall's +0.30% Acc. Revert path Brutal "
                 "Firewall of Perpetuity released.",
}

PAYLOAD_AB_2026_07_30 = {
    "name": "payload-ab-2026-07-30",
    "item": "Vital Payload of Extinction",
    "slot": "Payload",
    # PROVISIONAL equip time (advisory told the player to equip on reading it,
    # ~21:00Z 30 Jul). Refine from the stream ledger's stat-change record when
    # grading -- a late equip misclassifies pre fights as post and only
    # dilutes, but the boundary should still be corrected.
    # BOUNDARY CONFIRMED from the stream's Corruption 17.4<->71.6 stat-change
    # markers: Vital first on ~20:43:06Z, Bastioned back 20:53:06Z-21:00:36Z
    # (profiler pre-arm re-run), Vital re-equipped by 21:00:36Z. The 21:00:00Z
    # value below sits inside the final swap's poll-uncertainty window
    # [20:58:06, 21:00:36] -- keep it. GRADING NOTE: streak runs SPAN swaps
    # (~13 min at these depths), so the first post death (streak 154, run
    # began ~20:55:46Z) is a mixed-gear run, as are the 153/162 deaths near
    # the boundary; the clean post cohort is deaths whose run STARTED after
    # 21:00:36Z (run_start ~= ended_at_ms - streak*4872).
    "equip_ms": 1785445200000,          # 2026-07-30T21:00:00Z, confirmed
    "boundary_fight_id": None,
    # Baseline = the full post-Firewall window (firewall-ab-2026-07-28 close),
    # mean 140.2, n=89, Corporate Network.
    "baseline_deaths": [115, 132, 133, 147, 128, 133, 125, 131, 134, 134, 138,
                        137, 134, 131, 123, 136, 138, 134, 133, 148, 139, 134,
                        129, 141, 134, 136, 137, 141, 139, 133, 146, 141, 140,
                        143, 137, 145, 142, 144, 137, 139, 150, 146, 152, 148,
                        146, 154, 144, 127, 144, 137, 156, 157, 137, 148, 138,
                        146, 140, 143, 142, 144, 140, 132, 140, 146, 135, 144,
                        145, 146, 136, 134, 142, 152, 139, 137, 152, 147, 145,
                        140, 129, 147, 142, 159, 150, 142, 156, 128, 138, 148,
                        145],
    "baseline_hits": (456707, 115974),  # 79.7% pm-flag basis, post-Firewall
    "target_deaths": 24,
    "baseline_recent_ms": 1785276480000,   # Firewall equip -- same-loadout era
    # The window measures a DECLARED BUNDLE: the 287K-chip hardware package
    # (Packet Shield 14->88 on ~2,364 gear-flat Barrier, ECC 110->119, minor
    # tracks) landed minutes before the equip, inside this window and after
    # the whole baseline. Attribution between craft and hardware is not
    # recoverable from this window and is not attempted.
    "segment_ms": None,
    # Unlike the Firewall test, hit rate here is a TREATMENT metric with a
    # pre-registered size (below), NOT a contamination check. This equip is
    # also the strongest test yet of the 22 Jul "output does not move the
    # death ceiling" law: it buys ~+10-15% net output (AtkDmg +34.6pp affix,
    # Corrupt 16->66 gear-flat) with Acc -26.4pp / CritCh -10.1pp.
    "keep_rule": "KEEP if mean death streak >= 138.2 (baseline 140.2 - 2); "
                 "REVERT if mean <= 135.2. Contamination checks only: no zone "
                 "change in the window, and fight cadence must stay ~4.872 s. "
                 "PRE-REGISTERED treatment predictions (diagnostics, not "
                 "gates, written before any post data existed): (1) hit law "
                 "-- Accuracy stat 10,350 -> ~9,186 (-11.2%) predicts "
                 "per-attack hit rate at the streak-120-159 faces down ~3.8pp "
                 "(65-68% -> ~62-64%; pm-flag pooled rate ~79.7% -> ~76%); "
                 "(2) corruption law -- stat 17.4 -> ~71.6 predicts max "
                 "outgoing corruption/round at full stack ~6x stat = ~430 "
                 "(was ~104), and this EXTENDS the linear-to-~50 verified "
                 "range to ~72; (3) rounds/fight at matched streak band down "
                 "~10-13%. A large miss on (1) or (2) is a defect report "
                 "against the fitted law, whatever the depth outcome.",
    "concluded": "2026-07-31 KEEP — mean 155.0 over 29 deaths (pre-declared "
                 "n=24 reached; first-24 mean 154.6) vs gate 138.2, +14.8 "
                 "over the 140.2 baseline. Contamination clean: no zone "
                 "change, cadence held. Treatment predictions: (1) hit law "
                 "HELD (pooled 77.5% vs ~76 predicted); (2) corruption law "
                 "HELD out-of-sample, linearity extended to ~72 (30 Jul "
                 "profiler); (3) rounds/fight -39-41% at matched levels "
                 "(profiler; bundles the same-hour hardware package). The 22 "
                 "Jul 'output does not move the death ceiling' law survives "
                 "in strict form only as 'this BUNDLE moved it' -- "
                 "attribution between craft and hardware not attempted by "
                 "policy. Revert path Bastioned Payload of Perfect Strike "
                 "RELEASED.",
}

FIREWALL_AB_2026_07_31 = {
    "name": "firewall-ab-2026-07-31",
    "item": "Predatory Firewall of Immortality",
    "slot": "Firewall",
    # PROVISIONAL equip time -- craft finished ~11:59Z 31 Jul, advisory told
    # the player to equip on reading it. Refine from the stream's stat-change
    # markers when grading (Def +26.33pp / Regen +43 / MaxHP -11.98pp on swap
    # are unmistakable); runs SPAN swaps at these depths (~13 min), so the
    # clean post cohort is deaths whose run STARTED after the confirmed
    # boundary (run_start ~= ended_at_ms - streak*4872).
    "equip_ms": 1785500100000,          # 2026-07-31T12:15:00Z, provisional
    "boundary_fight_id": None,
    # Baseline = the full payload-ab-2026-07-30 post window (closed KEEP),
    # mean 155.0, n=29, Corporate Network.
    "baseline_deaths": [154, 155, 148, 155, 160, 147, 157, 155, 160, 170,
                        161, 148, 162, 155, 159, 158, 154, 158, 162, 147,
                        153, 148, 150, 134, 163, 154, 155, 155, 157],
    "baseline_hits": (99213, 28779),    # 77.5% pm-flag basis, post-Payload
    "target_deaths": 24,
    "baseline_recent_ms": 1785445200000,   # Payload equip -- same-loadout era
    # DECLARED BUNDLE by policy: the window will also contain the pending
    # equal-marginal chip spend cut from the fresh 11:59Z hardware panel and
    # any contract-board rewards. Attribution is not attempted.
    "segment_ms": None,
    "keep_rule": "KEEP if mean death streak >= 153.0 (baseline 155.0 - 2); "
                 "REVERT if mean <= 150.0. Contamination checks only: no "
                 "zone change in the window, and fight cadence must stay "
                 "~4.872 s. PRE-REGISTERED treatment predictions "
                 "(diagnostics, not gates, written before any post data "
                 "existed): (1) mitigation law -- Def stat +~11.4% (affix "
                 "+26.33pp x 0.435 pool factor) predicts incoming direct per "
                 "landed hit down ~9% (elasticity -0.88, K~219); (2) hit "
                 "laws -- Eva stat -~4.4% predicts enemy hit rate on us up "
                 "+1.3-1.8pp (enemy-side slope 1.184); our Acc +3.75pp affix "
                 "predicts our per-attack hit up ~+0.7pp; (3) realized "
                 "prg/round at streak >= 60 up +2-6% (listed Regen +43 flat "
                 "= +8%, realization depletion-dependent, mechanics.md §17). "
                 "(4) MaxHP stat falls ~7.8% -- this equip doubles as the "
                 "first live test of the UNMEASURED MaxHP weight (0.5): the "
                 "outcome gate holding at KEEP is evidence the weight is not "
                 "grossly under-priced; a REVERT with mitigation predictions "
                 "(1)-(3) all landing is evidence Max HP is worth far more "
                 "than 0.5 and the weight must be re-fit before the next "
                 "sustain trade.",
    "concluded": "2026-07-31 KEEP — mean 167.6 over 34 deaths (pre-declared "
                 "n=24 passed at first-24 mean 168.1) vs gate 153.0, +12.5 "
                 "over the 155.1 baseline. Contamination clean: no zone "
                 "change, cadence held. All four pre-registered predictions "
                 "landed: per-round gross -10/-11% at the deep bands (Def "
                 "law predicted -9% direct-channel; bundled with the 107K-"
                 "chip package); deep-band hit +0.7pp exactly as the hit law "
                 "predicted; realized regen/round +7.7% (244.2 -> 263.0, "
                 "top of the +2-6% band); and the -7.8% MaxHP side never "
                 "bit — the first live MaxHP-weight test resolves as 'not "
                 "grossly under-priced in a mitigation-compensated trade'. "
                 "Anomaly logged, not predicted: shallow-band gross fell "
                 "24-47%, far beyond the Def law — stack-exposure-vs-fight-"
                 "length hypothesis in open-questions.md. Revert path "
                 "Resilient Firewall of Perpetuity RELEASED.",
}

SHELL_AB_2026_07_31 = {
    "concluded": "KEEP — 1 Aug 2026. Mean 173.5 over 25 deaths (pre-declared "
                 "n=24) vs gate 165.6, +5.8 over the 167.7 same-loadout "
                 "baseline. Contamination clean: zone unchanged, cadence "
                 "4.644 pre vs 4.655 post across the boundary (the standing "
                 "4.872 CONSTANT was stale -- era-stepped to ~4.65 since 30 "
                 "Jul, re-fit in the same session; no step at the equip). "
                 "All 25 deaths post-date the VLAN +1% Def boundary, so the "
                 "window reads as a bundle. All four pre-registered "
                 "predictions graded -- see equipment-tests.md; the Barrier "
                 "one exposed and fixed the soak stock-sum bug in "
                 "_fight_record. New standing baseline 173.5.",
    "name": "shell-ab-2026-07-31",
    "item": "Shielded Shell of Bastion",
    "slot": "Shell",
    # Declared BEFORE the craft ran (as "Shielded Shell of Segmentation");
    # renamed on promotion, realized +44.2. BOUNDARY CONFIRMED from the
    # stream's stats marker at 20:10:05Z -- MaxHP 22,801 -> 25,043, Evasion
    # 6,365 -> 5,825, Regeneration 625.95 -> 656.31 -- the swap landed inside
    # the poll window [20:07:35, 20:10:05]. The provisional 20:30:00Z was
    # LATE and would have classified early post fights as pre. Runs span
    # swaps at these depths: the clean post cohort is deaths whose run
    # STARTED after the boundary (run_start ~= ended_at_ms - streak*4872).
    "equip_ms": 1785528605313,          # 2026-07-31T20:10:05Z, confirmed
    "boundary_fight_id": None,
    # Baseline = the full firewall-ab-2026-07-31 post window (closed KEEP),
    # mean 167.6, n=34, Corporate Network.
    "baseline_deaths": [175, 166, 162, 158, 168, 181, 173, 172, 165, 160,
                        166, 163, 162, 174, 170, 154, 171, 171, 166, 170,
                        172, 177, 166, 172, 172, 158, 166, 155, 162, 173,
                        167, 180, 163, 170],
    "baseline_hits": (176636, 52676),   # 77.0% pm-flag basis, post-Firewall
    "target_deaths": 24,
    "baseline_recent_ms": 1785500100000,  # Firewall equip -- same-loadout era
    # DECLARED BUNDLE by policy: the 110.7K-chip equal-marginal spend (ECC
    # L121->134 carrying most of it) lands inside this window.
    "segment_ms": None,
    "keep_rule": "KEEP if mean death streak >= 165.6 (baseline 167.6 - 2); "
                 "REVERT if mean <= 162.6. Contamination checks only: no "
                 "zone change in the window, and fight cadence must stay "
                 "~4.872 s. PRE-REGISTERED treatment predictions "
                 "(diagnostics, not gates, written before the CRAFT ran, "
                 "from the deepened contract's projection): (1) Barrier law "
                 "-- gear Barrier rises by the crafted affix (~650-730 at "
                 "Segmentation T1) and per-fight pool drawdown rises by "
                 "exactly 1.00x that amount; (2) Thorns law -- `ptd` per "
                 "enemy landed hit rises ~0.97x the crafted Thorns affix "
                 "(~+39 at of Reprisal T3); (3) Eva stat falls ~7.4% (affix "
                 "20.0 -> ~3.0pp) predicting enemy hit rate on us UP "
                 "+2.5-3pp -- the priced cost of the trade; (4) MaxHP rises "
                 "~+7% stat: the REVERSE MaxHP probe. The firewall window "
                 "cut max_hp 7.8% and depth rose; if depth rises here too, "
                 "both signs moved with the mitigation-weighted totals and "
                 "the 0.5 weight is bracketed from both directions.",
}

DRIVER_AB_2026_08_03 = {
    "name": "driver-ab-2026-08-03",
    "item": "Slippery Driver of Armageddon",  # crafted from "of Striking" 5 Aug, realized +44.0
    "slot": "Driver",
    # Declared BEFORE the craft ran (base name above; it will rename on
    # promotion). equip_ms is a FAR-FUTURE SENTINEL: the first provisional
    # (3 Aug 14:05Z, declaration time) leaked a pre-craft death (the 188
    # record) into the post window because the craft had not run -- an
    # early boundary corrupts silently, an empty post window is visibly
    # wrong. Set the REAL boundary from the stream stats marker at equip
    # (Evasion jumps ~+5%, barrier start-pool ~+1,500 x Packet Shield
    # multiplier; MaxHP nearly unchanged), the way the shell boundary was
    # corrected to 20:10:05. Until then the post window MUST read empty.
    # Boundary set 5 Aug 23:xx from capture-pair proof: last unequipped
    # capture 21:52:50Z, first equipped capture 22:01:05Z. The stream stats
    # marker (22:02:33Z, changed_from = Aegisbound-era values) has ~10-min
    # cadence -- too coarse to pin the click, so the boundary is the first
    # PROOF of equip: every fight after it is certainly post-equip. The
    # <=8 ambiguous minutes fall into the pre side of the display; the gate
    # numbers (172.2/169.2) were pre-registered off the frozen 74-death
    # baseline, so they are unaffected.
    "equip_ms": 1785967265758,          # 2026-08-05T22:01:05.758Z
    "boundary_fight_id": None,
    # Baseline = the full post-Shell same-loadout era (shell-ab closed KEEP
    # 1 Aug at 173.5/25; era kept accruing): n=74, mean 174.2, run_start
    # after the shell boundary at cadence 4.65.
    "baseline_deaths": [167, 166, 173, 167, 170, 167, 171, 175, 177, 174,
                        170, 176, 170, 170, 172, 187, 181, 172, 166, 179,
                        184, 171, 177, 179, 180, 179, 183, 175, 164, 169,
                        179, 159, 168, 169, 177, 176, 182, 170, 176, 172,
                        171, 180, 173, 171, 170, 176, 185, 167, 179, 174,
                        171, 168, 171, 176, 180, 185, 177, 171, 181, 182,
                        167, 179, 167, 171, 172, 173, 167, 172, 183, 176,
                        171, 181, 182, 184],
    "baseline_hits": (299124, 89011),   # 77.1% ph/pm basis, post-Shell era
    "target_deaths": 24,
    "baseline_recent_ms": 1785528605313,  # Shell equip -- same-loadout era
    # DECLARED BUNDLE by policy: the ~365K-chip equal-marginal package (ECC
    # L134->156, Packet Shield L89->110 -- which multiplies this craft's own
    # Barrier), the Snapshot Rollback install and the CI/CD Pipeline install
    # all land inside this window. Snapshot Rollback mechanically RAISES
    # death depth (25% HP recovery on lethal, 1/10 fights) and is
    # per-fight OBSERVABLE in the ledger (`homelab_snapshot_rollback`), so
    # its share of any depth gain is separately readable -- diagnostic,
    # not a gate.
    "segment_ms": None,
    "keep_rule": "KEEP if mean death streak >= 172.2 (baseline 174.2 - 2); "
                 "REVERT if mean <= 169.2. Contamination checks only: no "
                 "zone change in the window, and fight cadence must stay "
                 "at the ~4.65 era value (trailing-window check). "
                 "PRE-REGISTERED treatment predictions (diagnostics, not "
                 "gates, written before the CRAFT ran, from the deepened "
                 "contract's projection): (1) Barrier law -- gear Barrier "
                 "rises ~+990 (of Quarantine T6->T1, median roll) and the "
                 "per-fight start pool rises by 1.00x that TIMES the Packet "
                 "Shield pool multiplier (1.4446 at L89, ~1.55 if the "
                 "chip package lands first: start pool 4,584 -> ~6,050-"
                 "6,500) -- the multiplier is priced IN this time, the "
                 "shell pre-registration forgot it; (2) rounds/fight at "
                 "matched streak band UP ~8-15% (AtkSpd -13.5pp per the "
                 "measured -2..-5% rounds per +9.9%, plus ~-10% damage "
                 "per landed hit from CritDmg 50.9->17.4pp at ~31% crit) "
                 "-- the priced cost of the trade; (3) enemy hit rate on "
                 "us DOWN ~1.5+-0.5pp at matched band (loadout Eva "
                 "+6.88pp, inverse hit law -- third out-of-sample test); "
                 "(4) player damage per landed hit at matched band falls "
                 "~8-12%. WATCH (no law): longer fights raise enemy "
                 "corruption-stack exposure (ecs) -- if damage_taken/round "
                 "at matched band rises MORE than the enemy-hit prediction "
                 "implies, the open-questions stack-exposure hypothesis "
                 "gains a live data point.",
}

DRIVER_AB_2026_08_03["concluded"] = (
    "KEEP — 6 Aug 2026. Mean 189.2 over 47 deaths (pre-declared 24; closed "
    "late, every extra death confirmatory) vs gate 172.2; +12.6 vs the "
    "103-death same-loadout pre window (176.5), +15.0 vs the frozen 74-death "
    "baseline (174.2). Contamination clean: cadence 4.649 trailing vs era "
    "4.65, no zone change; whole post window sits after the VLAN +1% Def "
    "boundary and inside the declared bundle (290K-chip package, Snapshot "
    "Rollback — 41 procs/6,561 post fights). First sim-vs-live pair: "
    "sub-prediction (b) fired — live post 189.2 vs sim old-arm absolute "
    "187.3 means the +10 offset was mostly the hardware package being real, "
    "the sim's absolute scale is usable era-matched, and the craft's own "
    "live share (~+1.9 +-2) matches the sim's -0.58 +- 1.03. Prediction "
    "grades in equipment-tests.md; new standing baseline 189.2.")

ROUTER_AB_2026_08_06 = {
    "concluded": "KEEP -- 7 Aug 2026, mean 199.8 over 24/24 deaths vs gate "
                 ">=187.2 (baseline 189.8), delta +10.0. Contamination "
                 "checks passed: no zone change, cadence 4.649s in the 4.65 "
                 "era. BUNDLE: all 24 post deaths fall after the VLAN +1% "
                 "Def boundary. Prediction (1), the Regen-law forward test, "
                 "predicted +5.4 (sharpened +7.5 +-1.5) and the window "
                 "delivered +10.0 -- first out-of-sample LIVE confirmation, "
                 "over-delivering like the rest of the era; realized "
                 "prg/round 292.3 -> 320.3; (2) rounds/fight +8.1..+11.6% "
                 "vs the predicted +10-18%, at the low edge. Unexplained and "
                 "filed as open-questions par.18: our hit rate fell "
                 "0.7-2.1pp in ALL FOUR matched bands on a swap that changed "
                 "no Accuracy. Revert path Titanic Router of the Undying "
                 "RELEASED. See docs/decision-log.md",
    "name": "router-ab-2026-08-06",
    "item": "Aggressive Router of Recovery",  # will rename on promotion
    "slot": "Router",
    # Declared BEFORE the craft ran (6 Aug 2026 evening, same session as the
    # CI/CD Regen fit that unblocked it), equip_ms held at the far-future
    # sentinel per the driver lesson until capture-pair proof existed.
    # Boundary set ~19:50Z same day: last unequipped capture 19:47:38.601Z,
    # first equipped 19:49:24.621Z -- every fight after it is certainly
    # post-equip; the <=2 ambiguous minutes fall pre. Player equipped ahead
    # of the sim-first block (reasonable: P(upgrade) 92.5% on measured
    # weights, realized +44.9); the 00:00 UTC CI/CD block still runs
    # new-vs-old arms as the second agreement pair, now post-hoc.
    "equip_ms": 1786045764621,          # 2026-08-06T19:49:24.621Z
    "boundary_fight_id": None,
    # Baseline = the full post-Driver same-loadout era at declaration
    # (driver-ab-2026-08-03 closed KEEP 6 Aug at 189.2/47); frozen here for
    # the gate numbers, era keeps accruing until equip.
    "baseline_deaths": [183, 192, 201, 179, 197, 198, 188, 183, 194, 175,
                        180, 187, 187, 190, 191, 188, 193, 198, 185, 183,
                        192, 193, 192, 186, 192, 184, 186, 191, 184, 182,
                        196, 186, 192, 196, 196, 190, 191, 191, 195, 194,
                        186, 185, 184, 197, 194, 185, 179],
    "baseline_hits": (254064, 80607),   # post-Driver era player ph/pm basis
    "target_deaths": 24,
    "baseline_recent_ms": 1785967265758,  # Driver equip -- same-loadout era
    # DECLARED BUNDLE by policy: the 6 Aug ECC-directed 144K-chip package
    # (ECC L181 -- Regen-relevant), tonight's contract-board evening and any
    # homelab level-13 installs land near this window. Equip decision itself
    # is SIM-FIRST (par 9.4): a 15-run paired CI/CD block (post-craft vs
    # current loadout) decides the equip; this live gate is confirmation +
    # the second sim-vs-live agreement pair.
    "segment_ms": None,
    "keep_rule": "KEEP if mean death streak >= 187.2 (baseline 189.2 - 2); "
                 "REVERT if mean <= 184.2. Contamination checks only: no "
                 "zone change in the window, and fight cadence must stay at "
                 "the ~4.65 era value (trailing-window check). "
                 "PRE-REGISTERED treatment predictions (diagnostics, not "
                 "gates, written before the CRAFT ran, from the deepened "
                 "contract's projection): (1) REGEN LAW FORWARD TEST -- the "
                 "first out-of-sample test of the 6 Aug CI/CD fit: swap "
                 "Regen delta at median roll is +45.6 listed (153.6 proj vs "
                 "Titanic 108), so predict +5.4 streaks from the Regen term "
                 "alone at 0.119 streaks/listed-point; (2) rounds/fight at "
                 "matched band UP ~10-18% (AtkSpd -17.47pp per the measured "
                 "-2..-5% per +9.9%) -- the priced cost; (3) damage taken "
                 "per landed enemy hit at matched band DOWN ~4-8% (Def "
                 "affix +24.1pp -> stat +~10.5% via the 0.435 pool factor, "
                 "elasticity -0.88 on the ~41% direct channel); (4) enemy "
                 "hit rate on us UP ~+0.5pp (loadout Eva -1.97pp, inverse "
                 "hit law); (5) realized prg/round at streak >= 60 rises "
                 "toward the +87 loadout listed delta (~290 -> ~375 if "
                 "fully realized; mechanics par 17 predicts near-full "
                 "realization at this depth). NOTE no Barrier change on "
                 "this swap -- a clean Regen/Def family test.",
}

SHELL_AB_2026_08_07 = {
    "name": "shell-ab-2026-08-07",
    "item": "Assault Shell of the Shadow",
    "slot": "Shell",
    # The item this replaced, held as the revert path while the gate is hot.
    # Read by ihlib.protected_revert_items() so lock/decompile advice cannot
    # recommend deleting the only way back out of a live experiment.
    "revert_item": "Shielded Shell of Bastion",
    # Boundary from the capture pair: 08:30:37.344Z still showed Shielded
    # Shell of Bastion, 08:59:51.068Z showed the crafted Shell equipped.
    # That leaves ~29 ambiguous minutes -- WIDER than the Router's ~2 -- so
    # the boundary is set at the FIRST-EQUIPPED capture and every ambiguous
    # fight falls PRE, which biases against the treatment (the driver lesson).
    "equip_ms": 1786093191068,          # 2026-08-07T08:59:51.068Z
    "boundary_fight_id": None,
    # Baseline = the post-Router same-loadout era STRICTLY BEFORE equip_ms
    # (router-ab-2026-08-06 closed KEEP this morning at 199.8/24; the era
    # accrued one more pre-equip death for 25, mean 199.8). Frozen here for
    # the gate numbers. NOTE the 26th death of that era (streak 212) fell
    # AFTER 08:59:51 and is therefore POST -- it was pooled into an earlier
    # draft of this baseline, which would have set the gate off a treatment
    # observation. Declare-the-cohort applies to the frozen list too.
    "baseline_deaths": [200, 208, 186, 195, 183, 200, 199, 198, 214, 206,
                        200, 202, 202, 201, 200, 194, 188, 203, 194, 206,
                        205, 207, 201, 203, 201],
    "baseline_hits": (104737, 38163),   # post-Router era player ph/pm basis
    "target_deaths": 24,
    "baseline_recent_ms": 1786045764621,  # Router equip -- same-loadout era
    # DECLARED BUNDLE for the LIVE window only: the ECC Memory L181->L193
    # buy (~160K chips, Regen-side) landed between the 08:59:51 and 09:00:28
    # captures, i.e. ~35 min after equip. NOTE the SIM block is NOT bundled:
    # both arms ran 08:59:32-08:59:46, before the chips were spent (161,060
    # -> 168,057 at 08:59:51 -> 7,878 at 09:00:28), so the +20.20 +- 1.32 is
    # the craft alone -- the cleanest paired readout the pipeline has given.
    "segment_ms": None,
    "keep_rule": "KEEP if mean death streak >= 197.8 (baseline 199.8 - 2); "
                 "REVERT if mean <= 194.8. Contamination checks only: no "
                 "zone change in the window, and fight cadence must stay at "
                 "the ~4.65 era value (trailing-window check). "
                 "SIM-FIRST DECISION ALREADY TAKEN (par 9.4): the 4/4 paired "
                 "CI/CD block read B-A = +20.20 +- 1.32 streaks (~15 sigma), "
                 "arms identified from player_combat_stats and constant "
                 "within arm; equip followed. This live gate is confirmation "
                 "+ the THIRD sim-vs-live agreement pair. "
                 "PRE-REGISTERED treatment predictions (diagnostics, not "
                 "gates): (1) ABSOLUTE-SCALE TEST -- sim delta +20.2 on a "
                 "baseline of 199.8 predicts a live post mean of ~220-222 "
                 "(plus a small ECC term); landing 218-224 holds the sim's "
                 "absolute scale at n=3 gear eras. (2) REGEN LAW FORWARD "
                 "TEST #2: item Regen 49 -> 202 = +153 listed, so 0.119/pt "
                 "predicts +18.2 streaks from the Regen term ALONE -- i.e. "
                 "~90% of the observed +20.2, the law's second out-of-sample "
                 "test and its first on a clean unbundled pair. (3) BARRIER "
                 "CORROBORATION for par.15: loadout Barrier fell 18.0% "
                 "(7,195 -> 5,901) INSIDE a +20.2 gain; after the Regen term "
                 "only ~+2.0 streaks remain for the NET of Def +4.5%, Acc "
                 "+4.2% and MaxHP +1.7% MINUS Barrier -18% and Thorns -40%, "
                 "which bounds Barrier's marginal depth cost as small. This "
                 "CORROBORATES par.15 but does NOT unblock the PENDING_REFIT "
                 "-- Barrier did not move alone, so the dedicated isolation "
                 "pair is still owed. (4) realized prg/round at streak >= 60 "
                 "rises from 320.3 toward ~430 (loadout Regen 869 -> 1,160, "
                 "+33.6%). (5) rounds/fight at matched band FLAT within "
                 "+-2%: this swap changed no Attack Speed, which makes it a "
                 "discriminant against the Router window's AtkSpd confound. "
                 "(6) HIT-RATE DISCRIMINANT for par.18: Acc rose 4.2% "
                 "(Augment landed Omniscient T1) but Eva rose 5.8%, so the "
                 "fitted law logit(hit) = -0.164 + 1.420*ln(Acc/Eva) "
                 "predicts our hit rate DOWN ~0.4pp at matched band. If the "
                 "observed drop is ~0.4pp rather than the Router window's "
                 "0.7-2.1pp, par.18's anomaly was composition, not a broken "
                 "law. NOTE this is NOT a MaxHP test: MaxHP went UP 1.7%, "
                 "not down 8.3% as the contract projected, because "
                 "watchdog_matrix reached T1 -- the asserted 0.5 weight "
                 "stays unbounded by this window.",
}

SHELL_AB_2026_08_07["concluded"] = (
    "KEEP -- 7 Aug 2026. Mean 222.0 over 29 deaths (pre-declared 24) vs gate "
    "197.8; +22.2 vs the frozen 25-death same-loadout baseline (199.8). "
    "Contamination clean: cadence 4.601 on a trailing n=50 vs the 4.65 era "
    "value, no zone change (corporate_network throughout), and NO mid-window "
    "segment was declared -- the one declared bundle is the ECC Memory "
    "L181->L193 buy ~35 min after equip. THIRD sim-vs-live agreement pair, "
    "and the first with a provably unbundled sim block (both arms ran "
    "08:59:32-08:59:46, before the chips were spent). Predictions (1)-(4) "
    "held: absolute scale landed 222.0 inside the predicted 218-224; the "
    "Regen law's second out-of-sample forward test gave +18.2 of the +22.2 "
    "from the Regen term alone; the Barrier bound corroborates par.15 "
    "without unblocking it (Barrier did not move alone); realized prg/round "
    "at streak >=60 reached 445.2 against a predicted ~430. Predictions (5) "
    "and (6) MISSED and are recorded, not dropped -- rounds/fight rose in "
    "all four bands with no AtkSpd change (open-questions par.19; not a "
    "victory-selection artefact, win rate is 100% in both arms in every "
    "band), and hit rate rose in all four bands where the law predicted "
    "-0.4pp, which is composition-shaped and promotes par.18 candidate (a). "
    "Revert path Shielded Shell of Bastion RELEASED."
)

# Concluded experiments stay importable for retrospective analysis:
# experiment_status(SHELL_AB_2026_07_23).
#
# None while nothing is declared. The next gate is owed by the approved
# Bastioned Kernel of Mending craft, and cannot be written until the craft
# resolves and its realized stat line is known -- declaring a baseline from
# the treatment side is the error SHELL_AB_2026_08_07 documents avoiding.
ROUTER_AB_2026_08_09 = {
    "name": "router-ab-2026-08-09",
    "item": "Intangible Router of the Colossus",
    "slot": "Router",
    "revert_item": "Aggressive Router of the Undying",
    # crafted from Intangible Router of Vitality and equipped between the
    # 10:04:29Z and 10:08:23Z captures
    "equip_ms": 1786270000000,          # 2026-08-09T10:06:40Z
    # Baseline is deliberately TIGHT. The 213-death same-loadout window since
    # the 7 Aug Shell equip spans two zones and max_hp 29,688-43,988 -- a 48%
    # span, which `cohort_summary` flags as straddling a gear change. Narrowed
    # to 9 Aug, data_center only, max_hp 43,480-43,873 (a 0.9% span), which is
    # one continuous session on one loadout.
    "baseline_deaths": [246, 242, 236, 231, 241, 240, 217, 239, 248, 247],
    "baseline_recent_ms": 1786248000000,   # 2026-08-09T04:00Z
    # Contamination reference only -- this craft barely touches Accuracy
    # (+1.70pp at loadout, +0.36 score), so hit rate is a check, not a
    # treatment metric. Pooled over the 720 streamed fights 09:07Z-10:06Z:
    # the auto-stream was OFF from 08-08 11:06Z to 08-09 09:07Z, so no
    # streamed fight exists for most of the baseline death window and this
    # is the nearest same-loadout coverage there is. It sits entirely on the
    # POST-ECC side of the declared segment. `pm` flags first-attack misses
    # only (data-dictionary.md), so 72.20% is the biased first-attack rate
    # and is comparable only against the same statistic.
    "baseline_hits": (31026, 11949),
    # ECC Memory L217 -> L227 (~164K chips) landed between the 09:06Z and
    # 10:04Z captures, i.e. INSIDE the pre-equip window. The three deaths at
    # 09:23 / 09:42 / 10:01 (240, 237, 243, mean 240.0) may carry it and are
    # excluded from `baseline_deaths` above rather than silently pooled.
    # Declared BEFORE any post-equip death was scored.
    "segment_ms": 1786259179000,        # 2026-08-09T09:06:19Z
    "segment_label": "the ECC Memory L217->L227 buy (~+2% Regen)",
    "target_deaths": 12,
    # Predicted +14.33 +- 1.97 by the 6-run CI/CD pair run 10:08Z (3/arm,
    # arms identified from player_combat_stats: Regen 1964.2 -> 2316.5,
    # MaxHP 43,988 -> 48,118, Def 3914.5 -> 3801.7). Baseline sd is 8.7, so
    # 12 deaths give SE ~2.5 and resolve that effect at ~5.7 sigma.
    "keep_rule": "KEEP if mean death streak >= 244.0 (baseline 238.7 + 5.3, "
                 "~2 SE) over 12 deaths; REVERT if mean <= 234.0. "
                 "Contamination: cadence within ~2% of the era value, zone "
                 "stays data_center, and the declared ECC segment is read "
                 "separately if it lands on the wrong side.",
    "predictions": [
        "(1) THE HEADLINE DISAGREEMENT, pre-registered because it is the most "
        "informative thing in this window: the score model predicts +21.1 "
        "streaks (total +105.4 score at beta_Regen 0.200) and the Regen law "
        "alone predicts +19.6 (+165 item-flat x 0.119), but the CI/CD pair "
        "measured only +14.33 +- 1.97. The model over-predicts the sim by "
        "~7 streaks, ~3.5 SE. If live lands near 253 the sim is wrong; if it "
        "lands near 258 the model is right and the sim under-reads; if it "
        "lands near 253 the two agree and the SCORE MODEL is over-predicting "
        "at this Regen level -- which is what the 28 Jul diminishing-returns "
        "amendment predicts and has never been tested forward.",
        "(2) Regen realization: composed Regen 1964.2 -> 2316.5 (+17.9%). "
        "Realized prg/round at streak >=60 should rise from the 445.2 "
        "measured at the Shell close toward ~500, LESS than proportional if "
        "the depth-dependent overheal cap is real.",
        "(3) Defense fell 3914.5 -> 3801.7 (-2.9%), the first mitigation cut "
        "since the Shell craft. Damage taken per round at matched streak "
        "band should rise ~1-3%. If it rises materially more, the linear Def "
        "weight is under-penalizing mitigation loss.",
        "(4) FREE MaxHP BOUND, and currently the only one obtainable: MaxHP "
        "rose 43,988 -> 48,118 (+9.4%) inside a Regen-positive bundle. "
        "MaxHP is ASSERTED at 0.5, never validated, and `audit` reports "
        "PROBE-GONE -- no owned item is a pure enough lever to measure it. "
        "So this window is a bound, not a fit, and it is bracketed the same "
        "way the 31 Jul / 1 Aug pair bracketed it.",
    ],
}


ROUTER_AB_2026_08_09["concluded"] = (
    "KEEP -- 9 Aug 2026, TRUNCATED AT n=9 OF A PRE-DECLARED 12. Truncated "
    "deliberately, by the Firewall craft being equipped rather than held back "
    "for the remaining 3 deaths: progression outranks measurement and the "
    "window had already answered the question. Recording the n it reached and "
    "WHY, rather than reporting 12, is the whole of the discipline here. "
    "Mean 255.2 over 9 deaths vs a 244.0 gate (baseline 238.7), delta +16.5. "
    "Excluding the one equip-boundary straddler -- a streak begun ~6 min "
    "before the equip and therefore fought on the old Router -- reads 257.1 "
    "over 8 (+18.4); that is DISCLOSURE, not the declared metric, and the "
    "verdict does not turn on it. "
    "CONTAMINATION: the declared ECC Memory L217->L227 segment covers all 9 "
    "deaths, so the window measures Router+ECC as a bundle; cadence and zone "
    "held (data_center throughout), hit rate 71.8% vs a 72.2% baseline, i.e. "
    "flat as expected for a craft that barely moves Accuracy. "
    "PREDICTION (1) RESOLVED, and it is the point of the window: the CI/CD "
    "pair predicted +14.33 +- 1.97 and live delivered +16.5 -- agreement "
    "inside ~1.1 sigma, the FOURTH sim-vs-live agreeing pair. The score model "
    "predicted +21.1 and the Regen law +19.6, so BOTH over-predict live while "
    "the sim does not. That is the 28 Jul diminishing-returns amendment "
    "getting its first forward test, and it passed. "
    "PREDICTIONS (2)-(4): realized prg/round and the Defense cut are readable "
    "in the mechanism table; the MaxHP bound (43,988 -> 48,118 inside a "
    "Regen-positive bundle) is a bound only, and MaxHP remains PROBE-GONE. "
    "Revert path Aggressive Router of the Undying RELEASED."
)

ACTIVE_EXPERIMENT = None


# ---------------------------------------------------------------------------
# Reserved probe arms: gear held as INSTRUMENTS, not as craft bases.
#
# A measurement that needs a paired CI/CD block needs a gear swap that moves
# ONE family and little else. Such an item is worthless to `plan_craft` by
# construction -- it is chosen for what it ISOLATES, not for what it scores --
# so value-based lock advice will always rank it for decompile. That is the
# same structural blind spot `protected_revert_items` exists to close for A/B
# revert paths, and it had been left open for probe arms.
#
# It cost five instruments. Until 9 Aug 2026 the reservation lived as prose in
# docs/candidate-status.md ("five items are reserved CI/CD probe arms --
# Pinpoint Kernel of Rejuvenation, Assault Kernel of Penetration, Guided
# Kernel of Restoration, Prolific Driver of Isolation, Slippery Driver of
# Sandboxing"). Nothing read that sentence: not `lock_actions`, not `audit`.
# By 9 Aug every one of the five was gone from the inventory, the MaxHP probe
# among them -- and MaxHP is still ASSERTED, still the largest unpriced term,
# and still waiting on exactly the block those arms were held for.
#
# So the reservation is declared by FAMILY, never by item name. A name list
# rots the moment the inventory turns over, which is precisely how the first
# five were lost; a family is a standing question, and `ihlib.probe_levers`
# re-picks the best owned lever for it against every fresh capture. The
# workspace rule this obeys is "a model fitted on currently-owned state rots
# when the inventory turns over" -- so do not put item names here.
#
# Fields: `family` is a CRAFT_WEIGHTS key. `arms` is how many levers to hold
# (2 gives the block a spare when a drop displaces the best one mid-day).
# `concluded` retires the row without deleting the record, exactly as the
# experiment declarations do.
RESERVED_PROBES = [
    {
        "family": "ArmorPen",
        "arms": 2,
        "concluded": "RESOLVED 9 Aug 2026 — the 12-run Analyzer pair read "
                     "-11.22 +- 1.76 streaks and, pooled with the 8 Aug craft "
                     "pair, fit 0.045 +- 0.006 against an applied 0.068 "
                     "(3.6 sigma). Weight refit and the PENDING_REFITS row "
                     "closed in the same session. Arms released.",
        "reason": "the one KNOWN-WRONG constant in PENDING_REFITS: "
                  "CRAFT_WEIGHTS_FLAT[ArmorPen] applies 0.068 (Regen's beta "
                  "0.200) against a measured 0.116-0.132 off the 8 Aug "
                  "Analyzer pair. Every potential/contract/hardware verdict "
                  "prints a banner until it resolves, and six CONTESTED items "
                  "hold inventory waiting on it",
        "unblock": "the par.22 design applied to ArmorPen (open-questions "
                   "par.21): one 12-run CI/CD block, 6 runs/arm, arms "
                   "differing in ArmorPen with the other families subtracted "
                   "at their own betas",
        },
    {
        # The ArmorPen row above concluded on the WEIGHT, which is what it
        # declared, and released its arms correctly. But par.21 closed with a
        # second question still open in the same paragraph -- "both depth
        # pairs ran in Data Center at ArmorPen ~1,029, the damage law is
        # convex, so the fit is regime-local; the Corporate Network extension
        # is still unrun and is still the cheapest test of whether any beta
        # generalises across zones" -- and no reservation ever backed it.
        # Result on 10 Aug 2026: `locks` listed BOTH arms for decompile
        # (Targeted Analyzer of Light Speed, Resilient Analyzer of Decay)
        # while open-questions called them the instrument for the cheapest
        # open test in the file. Two producers of one answer, disagreeing --
        # which is how everything here gets found. The arms are the same two;
        # only the zone changes, so this costs 2 inventory slots at 74/102
        # and one pair of runs out of a daily budget that expires unused.
        "family": "ArmorPen",
        # NAMED, not purity-ranked, because this is a REPLICATION: the beta
        # being re-tested was fitted on these two arms, so re-running the
        # ranking answers a different question. On 10 Aug 2026 the top two by
        # purity had both changed since the first block, and the new leader
        # (`Uncatchable Analyzer of the Bastion`, signed purity 50.8 off 67.3
        # of absolute movement) is precisely the near-total-cancellation arm
        # par.21 argued against running.
        "items": ["Targeted Analyzer of Light Speed",
                  "Resilient Analyzer of Decay"],
        "reason": "every conversion in the model (Regen 0.200, ArmorPen "
                  "0.132, Barrier ~0) was fitted in Data Center at ArmorPen "
                  "~1,029, and the damage law dmg = Atk*K/(K+Def-AP) is "
                  "convex -- value per point RISES as ArmorPen approaches "
                  "enemy Defense. Nothing has ever tested whether a beta "
                  "survives a zone change, so every weight in the register is "
                  "regime-local by default and nobody has priced the regime",
        "unblock": "re-run the SAME two Analyzer arms in Corporate Network "
                   "(open-questions par.21, 'second, free reading already "
                   "available'). The zones differ by ~30 streaks for this "
                   "build: if the conversion is regime-local the two zones "
                   "disagree, and if it is a property of the stat they do "
                   "not. One extra pair of runs",
        "concluded": None,
    },
    {
        # Opened 10 Aug 2026 the moment PENDING_REFITS re-opened on Barrier.
        # The 7 Aug block that fitted the weight was censored by the zone's
        # enemy-level cap (6/6 runs of the low-Barrier arm at or above it,
        # 0/6 of the high-Barrier arm), so a re-fit is needed and the arm it
        # needs was on that same evening's decompile list at -51.9. That is
        # incident #27 and #33 for the third time: a measurement need with no
        # code-level reservation, and the instrument one click from deletion.
        "family": "Barrier",
        # BY FAMILY, not by name: this is a fresh FIT, not a replication, so
        # a better-ranked substitute answers the same question. (The par.21
        # row above is named precisely because it is the other case.) The
        # original arms cannot be reconstructed anyway -- the loadout moved
        # from Barrier 5,900 / Regen 1,221 to Barrier 1,746 / Regen 1,178.
        "arms": 2,
        "reason": "CRAFT_WEIGHTS_FLAT[Barrier] = 0.0088 is back in "
                  "PENDING_REFITS: beta_Barrier = 0.041 +- 0.024 was fitted "
                  "on an arm the zone's enemy-level cap had truncated, and "
                  "the censoring bound on the arm carrying LESS Barrier, so "
                  "both the beta and the weight are CEILINGS and the true "
                  "value may be zero. Barrier is carried by four equipped "
                  "items and by the Packet Shield hardware track, so the "
                  "ceiling is priced into every craft, lock and chip verdict",
        "unblock": "a CI/CD pair on the purest owned Barrier lever, read as "
                   "beta (streaks per score point) per par.22. UNDERPOWERED "
                   "AND SAY SO: the best lever owned on 10 Aug 2026 is "
                   "`Guided Driver of Swiftness` at -11.7 Barrier score "
                   "against -1.5 signed other (purity 7.7, but off 25.4 of "
                   "ABSOLUTE movement -- heavy cancellation, the caveat "
                   "PROBE_MIN_PURITY's register row names). Regen-parity "
                   "predicts -2.3 streaks and beta=0 predicts 0, which is "
                   "~2 sigma at 6 runs/arm against par.22's 8 -- directional "
                   "only, and it pools with a later block. A -49-score lever "
                   "like the original would settle it outright",
        "concluded": None,
    },
    {
        "family": "MaxHP",
        "arms": 2,
        "reason": "CRAFT_WEIGHTS_PCT[MaxHP] = 0.5 is ASSERTED and has NEVER "
                  "been validated -- the largest unpriced term in the model. "
                  "The Software Profiler cannot see it (full-HP single "
                  "fights), so the CI/CD Pipeline is the only instrument that "
                  "can. Bracketed from both signs by the 31 Jul / 1 Aug "
                  "mitigation-compensated trades, but never fitted",
        "unblock": "a CI/CD pair on a MaxHP-carrying lever at matched "
                   "mitigation, read as beta (streaks per score point) per "
                   "par.22 -- the reparameterization that made the Barrier "
                   "row finally answerable",
        "concluded": None,
    },
]
