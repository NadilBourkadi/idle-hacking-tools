#!/usr/bin/env python3
"""Query CLI for Idle Hacking full-state captures.

Usage: python3 scripts/ih.py <command> [args]

Commands:
  captures                 list capture files with counts
  loadout [--file F]       equipped items + summed combat totals
  item QUERY [--file F]    full detail for one item (name substring / id prefix)
  candidates [--slot S]    inventory items table, optionally one slot
  compare A B              stat delta between two items
  diff [OLD] [NEW]         item changes between captures (default: last two)
  stats                    player resources, level, homelab presence
  history QUERY            an item's stability/affixes across all captures
  potential [--slot S]     rank candidates by PROJECTED post-craft ceiling
                           (empirical tier ladders; use for candidate decisions
                           instead of raw compare/candidates output)
  homelab                  level/progress, active jobs, purchasable upgrades
  hardware                 shop tracks ranked by value per chip (heuristic)
  ab [--brief]             active A/B experiment status across ALL captures
                           (deduped; each capture permanently banks its
                           combat windows — capture at least once per climb)
  contract ITEM            simulate a craft contract's OUTCOME DISTRIBUTION
                           [--phase 'of Haste:4' ...] [--order] [--floor N]
                           (use instead of the flat ~5-point discount when a
                           craft verdict is close — see ihlib.simulate_contract)
  calibration              score the prediction ledger: planner bias,
                           interval coverage, verdict survival
  assumptions              provenance register for every tunable constant
                           (asserted/inherited = never tested; those are
                           the ones that have been wrong every time)
  cadence                  measured seconds per fight from the death clock
                           (a fixed real-time tick that era-steps — quote
                           FIGHT_CADENCE_S; attack speed is NOT income)
  sims [--mode M]          Hacking Simulator runs banked by the userscript
                           (software_profiler | cicd_pipeline; CI/CD arm
                           summaries are grouped per UTC day-block)
  brief                    one-process advisory digest of everything above
                           (triage layer — drill into anything flagged)

Output is deliberately compact; prefer this over ad-hoc capture parsing.
"""

import argparse
import contextlib
import io
import re
import statistics
import sys
import textwrap
import time
from datetime import datetime, timezone

import ihlib


def cmd_captures(args):
    for path in ihlib.capture_paths():
        cap, _ = ihlib.load_capture(path)
        state = cap["state"]
        inv = (state.get("inventoryData") or {}).get("items") or []
        eq = state.get("equipmentData") or {}
        lazy = [
            k for k in ("statsBreakdown", "extendedStats", "recentLossStreaks",
                        "combatLog", "homelabInfo", "hardwareInfo")
            if state.get(k)
        ]
        print(f"{path.name}  v{cap.get('sourceVersion')}  "
              f"{len(eq)} equipped, {len(inv)} inventory"
              f"{'  +' + ','.join(lazy) if lazy else ''}")


def cmd_loadout(args):
    cap, path = ihlib.load_capture(args.file)
    print(f"# {path.name}")
    equipped = []
    for where, slot, item in ihlib.iter_items(cap):
        if where != "equipped":
            continue
        equipped.append(item)
        print(f"{slot:9s} {item.get('name'):42s} ilvl {item.get('item_level'):>4} "
              f"stab {item.get('stability')}/{item.get('stability_max')}")
    print("\nLoadout combat totals:")
    print(" ", ihlib.fmt_totals(ihlib.merge_totals(equipped)))


def resolve_one(cap, query):
    matches = ihlib.find_items(cap, query)
    if not matches:
        sys.exit(f"no item matches {query!r}")
    if len(matches) > 1:
        exact = [m for m in matches if m[2].get("name", "").lower() == query.lower()]
        if len(exact) == 1:
            return exact[0]
        print(f"({len(matches)} matches for {query!r}, using first; others: "
              f"{', '.join(m[2].get('name') for m in matches[1:5])})")
    return matches[0]


def cmd_item(args):
    cap, path = ihlib.load_capture(args.file)
    where, slot, item = resolve_one(cap, args.query)
    print(f"# {path.name}")
    print(ihlib.item_header(item, slot, where))
    implicit = item.get("implicit_info")
    if implicit:
        label = ihlib.stat_label(implicit.get("stat_type") or "?")
        value = implicit.get("value", 0)
        text = (f"{value:+g}" if implicit.get("effect_type") == "flat_add"
                else f"{value * 100:+.2f}%")
        print(f"  implicit: {label} {text}")
    for line in ihlib.affix_lines(item):
        print(line)
    print("  totals:", ihlib.fmt_totals(ihlib.item_stat_totals(item), combat_only=False))
    preview = item.get("crafting_preview")
    if preview:
        # UI button names differ from the payload keys (decoded 27 Jul 2026
        # from vendor/game-js): annul -> PRUNE, masterwork -> REFACTOR.
        labels = [
            ("base_cost_with_stability", "base w/stability"),
            ("augment_cost", "augment"), ("augment_credit_cost", "augment cr"),
            ("tier_promotion_primary_cost", "VU prefix"),
            ("tier_promotion_secondary_cost", "VU suffix"),
            ("masterwork_cost", "Refactor"), ("annul_cost", "Prune"),
            ("bias_primary_cost", "Bias"), ("bias_credit_cost", "Bias cr"),
            ("bias_essence_cost", "Bias essence"),
            ("lock_cost", "Lock cr"), ("compile_cost", "compile"),
        ]
        print("  costs:", "  ".join(f"{name} {round(preview[k]):,}"
                                    for k, name in labels if preview.get(k)))
        if preview.get("lock_cost"):
            print("         Lock also costs 1 Stabilizer "
                  f"(held: {(cap['state'].get('currentPlayer') or {}).get('stabilizers', 0):,})")


def cmd_candidates(args):
    cap, path = ihlib.load_capture(args.file)
    print(f"# {path.name}")
    slot_filter = args.slot.lower() if args.slot else None
    rows = [
        (slot, item) for where, slot, item in ihlib.iter_items(cap)
        if where == "inventory"
        and (slot_filter is None or (slot or "").lower() == slot_filter)
    ]
    rows.sort(key=lambda r: (r[0] or "", -(r[1].get("item_level") or 0)))
    for slot, item in rows:
        print(f"{slot:9s} {item.get('name'):44s} {item.get('rarity', '?'):5s} "
              f"ilvl {item.get('item_level'):>4} "
              f"stab {item.get('stability'):>2}/{item.get('stability_max'):>2}  "
              f"{ihlib.fmt_totals(ihlib.item_stat_totals(item))}")
    print(f"({len(rows)} items)")


def cmd_compare(args):
    cap, path = ihlib.load_capture(args.file)
    where_a, slot_a, a = resolve_one(cap, args.a)
    where_b, slot_b, b = resolve_one(cap, args.b)
    print(f"# {path.name}")
    print("A:", ihlib.item_header(a, slot_a, where_a))
    print("B:", ihlib.item_header(b, slot_b, where_b))
    ta, tb = ihlib.item_stat_totals(a), ihlib.item_stat_totals(b)
    labels = [label for label in ihlib.COMBAT_ORDER
              if label in ta or label in tb]
    labels += sorted(set(list(ta) + list(tb)) - set(labels))
    print(f"{'stat':12s} {'A':>14s} {'B':>14s} {'B-A':>14s}")
    for label in labels:
        pa, fa = ta.get(label, (0, 0))
        pb, fb = tb.get(label, (0, 0))
        if abs(pa) + abs(pb) > 1e-9:
            print(f"{label:12s} {pa*100:13.2f}% {pb*100:13.2f}% {(pb-pa)*100:+13.2f}%")
        if abs(fa) + abs(fb) > 1e-9:
            print(f"{label:12s} {fa:14g} {fb:14g} {fb-fa:+14g}")


def item_signature(item):
    affixes = []
    for side in ("prefixes", "suffixes"):
        for affix in item.get(side) or []:
            affixes.append((affix.get("affix_id"), affix.get("tier")))
    return (item.get("stability"), tuple(sorted(a for a in affixes)))


def cmd_diff(args):
    paths = ihlib.capture_paths()
    old_path = args.old or (paths[-2] if len(paths) > 1 else None)
    new_path = args.new or paths[-1]
    if not old_path:
        sys.exit("need at least two captures to diff")
    old, old_path = ihlib.load_capture(old_path)
    new, new_path = ihlib.load_capture(new_path)
    print(f"# {old_path.name} -> {new_path.name}")
    old_items = {i.get("id"): (s, i) for _, s, i in ihlib.iter_items(old)}
    new_items = {i.get("id"): (s, i) for _, s, i in ihlib.iter_items(new)}
    for item_id in new_items.keys() - old_items.keys():
        slot, item = new_items[item_id]
        print(f"+ {slot:9s} {item.get('name')}  ilvl {item.get('item_level')} "
              f"{item.get('rarity')}")
    for item_id in old_items.keys() - new_items.keys():
        slot, item = old_items[item_id]
        print(f"- {slot:9s} {item.get('name')}  ilvl {item.get('item_level')}")
    for item_id in new_items.keys() & old_items.keys():
        _, a = old_items[item_id]
        slot, b = new_items[item_id]
        if item_signature(a) != item_signature(b):
            print(f"~ {slot:9s} {b.get('name')}  "
                  f"stab {a.get('stability')}->{b.get('stability')}")
            old_affixes = {af.get("affix_id"): af.get("tier")
                           for side in ("prefixes", "suffixes")
                           for af in a.get(side) or []}
            new_affixes = {af.get("affix_id"): af.get("tier")
                           for side in ("prefixes", "suffixes")
                           for af in b.get(side) or []}
            for affix_id in sorted(set(old_affixes) | set(new_affixes)):
                ta, tb = old_affixes.get(affix_id), new_affixes.get(affix_id)
                if ta != tb:
                    print(f"    {affix_id}: T{ta} -> T{tb}")


def cmd_stats(args):
    cap, path = ihlib.load_capture(args.file)
    player = cap["state"].get("currentPlayer") or {}
    print(f"# {path.name}")
    for key in ("hack_level", "hack_exp", "credits", "chips", "stabilizers",
                "current_win_streak", "current_zone"):
        if key in player:
            value = player[key]
            print(f"  {key}: {value:,.0f}" if isinstance(value, (int, float))
                  else f"  {key}: {value}")
    essences = {k.replace("essence_", ""): v for k, v in player.items()
                if k.startswith("essence_") and v}
    if essences:
        print("  essences:", ", ".join(f"{k} {v:,}" for k, v in sorted(essences.items())))
    for binding in ("homelabInfo", "combatLog", "recentLossStreaks",
                    "statsBreakdown", "extendedStats", "hackingZones"):
        value = cap["state"].get(binding)
        size = len(value) if isinstance(value, (list, dict)) else value
        print(f"  {binding}: {'empty' if not value else size}")


def cmd_history(args):
    for path in ihlib.capture_paths():
        cap, _ = ihlib.load_capture(path)
        matches = ihlib.find_items(cap, args.query)
        if matches:
            where, slot, item = matches[0]
            tiers = ",".join(
                f"T{af.get('tier')}" for side in ("prefixes", "suffixes")
                for af in item.get(side) or [])
            print(f"{path.name}: {where} stab "
                  f"{item.get('stability')}/{item.get('stability_max')}  [{tiers}]")
        else:
            print(f"{path.name}: (absent)")


def cmd_potential(args):
    for _line in ihlib.pending_refit_banner():
        print("# " + _line)
    cap, path = ihlib.load_capture(args.file)
    # ladders come from the WHOLE capture archive, not this capture: an affix's
    # tier range is a game constant, so decompiling an item must not delete the
    # evidence. See ihlib.tier_ladders_archive for the +9.0 -> +4.6 Firewall
    # regression that this prevents.
    ladders = ihlib.tier_ladders_archive()
    print(f"# {path.name}")
    preserve = ihlib.stability_preserve_chance(cap)
    depth = ("depth set by Stability budget" if args.cap <= 1
             else f"planned no deeper than T{args.cap}")
    backup = (f", Snapshot Backups {preserve*100:.0f}% Stability preserve"
              if preserve else "")
    print(f"# Projected post-craft ceilings ({depth}, Compile floor "
          f"{args.floor}{backup}); score = bottleneck planning heuristic "
          "(ihlib.CRAFT_WEIGHTS_*), not a game formula.")
    print("# These are optimal-plan ceilings. Judge close calls with "
          "`ih.py contract` (outcome distribution), never a flat discount — "
          "calibration shows realized runs ABOVE projection in every "
          "uncapped era (`ih.py calibration`).")
    # ladder law re-fitted from the archive, not hard-coded (ihlib.fit_tier_steps)
    shallow_step, deep_step = ihlib.fit_tier_steps(cap, ladders=ladders)
    print(f"# Tier ladder fitted over {len(ihlib.capture_paths())} captures: "
          f"{shallow_step:.3f}x per tier "
          f"above T{ihlib.DEEP_TIER}, {deep_step:.3f}x at or below it. "
          f"'low' = same plan re-valued at the p25 deep step "
          f"({ihlib.TIER_STEP_DEEP_LOW:.3f}); a verdict that needs the median "
          f"to clear the band is resting on extrapolation.")
    slot_filter = args.slot.lower() if args.slot else None
    slots = [s for s in ihlib.SLOT_DISPLAY.values()
             if slot_filter is None or s.lower() == slot_filter]
    items = list(ihlib.iter_items(cap))
    for slot in slots:
        equipped = next((i for w, s, i in items if w == "equipped" and s == slot), None)
        print(f"\n== {slot} ==")
        if equipped:
            base = ihlib.weighted_score(ihlib.item_stat_totals(equipped))
            print(f"  equipped  {equipped.get('name'):<44} score {base:6.1f}  "
                  f"{ihlib.fmt_totals(ihlib.item_stat_totals(equipped))}")
        else:
            base = 0.0
            print("  (slot empty)")
        rows = []
        for where, s, item in items:
            if where != "inventory" or s != slot:
                continue
            plan = ihlib.plan_craft(item, ladders, floor=args.floor,
                                    tier_cap=args.cap, preserve=preserve,
                                    deep_step=deep_step)
            rows.append((plan["score"], item, plan))
        rows.sort(key=lambda r: -r[0])
        eq_totals = ihlib.item_stat_totals(equipped) if equipped else {}
        for score, item, plan in rows[: args.top]:
            delta = score - base
            verdict = ("UPGRADE" if delta > ihlib.UPGRADE_BAND
                       else "inferior" if delta < ihlib.INFERIOR_BAND
                       else "sidegrade")
            marker = "~" if plan["estimated"] else " "
            steps = ", ".join(
                f"{label} T{f}->T{t}{'~' if est else ''}"
                for _uid, label, f, t, c, est in plan["steps"])
            aug = (f"Augment[{plan['augment_side']}]" if plan["augment_open"] else "full")
            print(f" {marker}ceiling   {item.get('name'):<44} score {score:6.1f} "
                  f"({delta:+6.1f} {verdict:<9})  ilvl {item.get('item_level'):>4} "
                  f"stab {item.get('stability'):>2}  "
                  f"stab ~{plan['expected_spend']:.1f}"
                  + (f"/~{plan['expected_attempts']:.0f} att" if preserve else "")
                  + f"  {aug}  Compile +{plan['compile_pct'] * 100:.1f}%")
            # the same plan valued at the p25 deep step -- a verdict that only
            # survives at the median is extrapolation, not evidence
            delta_low = plan["score_low"] - base
            if plan["deep_reliance"] and abs(plan["score_low"] - score) > 0.05:
                flip = ("" if (delta_low > ihlib.UPGRADE_BAND) == (delta > ihlib.UPGRADE_BAND)
                        else "  <-- VERDICT FLIPS")
                print(f"            low:  score {plan['score_low']:6.1f} "
                      f"({delta_low:+6.1f})  "
                      f"{plan['deep_reliance']} unobserved deep-tier "
                      f"promotion(s){flip}")
            if steps:
                print(f"            plan: {steps}")
            print(f"            proj: {ihlib.fmt_totals(plan['totals'])}")
            # where the delta came from -- a scalar hides which weight carries
            # it, which is how two Corruption artifacts topped this board
            parts = ihlib.score_contributions(plan["totals"], eq_totals)
            if parts:
                # print EVERY term: parts sorts by signed value, so any cap
                # drops the largest NEGATIVES first — a [:8] here hid a
                # -18.3 AtkDmg and a -38.4 Regen counterweight (2026-08-03)
                print("            from: " + "  ".join(
                    f"{label} {value:+.1f}" for value, label in parts))
                bad, labels = ihlib.suspect_share(parts)
                # `bad` is the SUM of the suspect contributions, so a +30
                # Barrier against a -30 Corrupt cancels to ~0 and an
                # abs(bad)-only gate goes silent on an item `locks` is
                # meanwhile pricing on the re-planned reading. Fire on the
                # gross exposure too (8 Aug 2026 review).
                gross = sum(abs(v) for v, label in parts
                            if label in ihlib.SUSPECT_WEIGHTS)
                if labels and (abs(bad) > 2 or gross > 2):
                    # The ex-suspect number that matters is the value of the
                    # ex-suspect-OPTIMAL plan, not this plan re-scored -- see
                    # ihlib.suspect_free_weights. Re-scoring the raw plan
                    # prices a contract nobody would run under those beliefs,
                    # and it released the best Analyzer base to the AT RISK
                    # list on 8 Aug 2026 while this very panel called it best
                    # in slot.
                    sf = ihlib.suspect_free_weights()
                    plan_sf = ihlib.plan_craft(
                        item, ladders, floor=args.floor, tier_cap=args.cap,
                        preserve=preserve, deep_step=deep_step, weights=sf)
                    d_sf = (ihlib.weighted_score(plan_sf["totals"], sf)
                            - ihlib.weighted_score(eq_totals, sf))
                    print(f"            !!    {abs(bad):.1f} of that is "
                          f"{'/'.join(labels)}; re-planned WITHOUT them the "
                          f"base is worth {d_sf:+.1f} (this plan re-scored: "
                          f"{delta - bad:+.1f}). "
                          + "; ".join(ihlib.SUSPECT_WEIGHTS[label]
                                      for label in labels))
                    steps_sf = ", ".join(
                        f"{label} T{f}->T{t}{'~' if est else ''}"
                        for _uid, label, f, t, c, est in plan_sf["steps"])
                    if steps_sf and steps_sf != steps:
                        print(f"            ex-suspect plan: {steps_sf}")
            econ = []
            for label in sorted(set(plan["totals"]) | set(eq_totals)):
                if ihlib.is_combat_stat(label):
                    continue
                dp = (plan["totals"].get(label, (0, 0))[0]
                      - eq_totals.get(label, (0, 0))[0])
                if abs(dp) > 1e-4:
                    econ.append(f"{label} {dp * 100:+.1f}%")
            if econ:
                print(f"            econ Δ vs equipped: {'  '.join(econ)}")


def cmd_homelab(args):
    cap, path = ihlib.load_capture(args.file)
    homelab, definitions, info = ihlib.homelab_state(cap)
    if not homelab:
        sys.exit("no homelabInfo in capture (open the Homelab tab and recapture)")
    print(f"# {path.name}")
    level = homelab.get("level", 0)
    points = homelab.get("progress_points", 0)
    line = f"  level {level} — {points:,} pts"
    for target in (level + 1, level + 2):
        need = ihlib.homelab_level_threshold(definitions, target)
        if need:
            line += f"; level {target} at {need:,} ({max(0, need - points):,} to go)"
    print(line)
    print(f"  slots {info.get('active_build_slots')}/{info.get('max_build_slots')}"
          f"  hackcoin {info.get('hackcoin')}  credits {info.get('credits'):,.0f}")

    names = {u["def"]["type"]: u["def"].get("name") or u["def"]["type"]
             for u in ihlib.iter_homelab_upgrades(homelab, definitions)}
    # Queued jobs are charged at queue time (credits/resources verified
    # 27 Jul 2026) and hold their cost_snapshot, so they count as spent and
    # as in-flight points just like running ones.
    jobs = homelab.get("active_jobs") or []
    pending = homelab.get("pending_jobs") or []
    in_flight_points = 0
    # ETAs share a DECLINING split: as each active job finishes the rest speed
    # up, so a fixed divisor over-states all but the longest.
    active_eta = ihlib.homelab_job_eta_hours(info, jobs)
    for label, group in (("active jobs", jobs), ("queued jobs", pending)):
        if not group:
            continue
        print(f"\n  {label}:")
        for job in group:
            done = job.get("progress_ticks") or 0
            total = job.get("duration_ticks") or 1
            pts = job.get("progress_points") or 0
            in_flight_points += pts
            # real time, not raw ticks: the lab advances o/n ticks per tick
            # (ihlib.homelab_job_hours). A queued job is priced as if it ran
            # alone, which is what it does once the actives drain.
            if group is jobs:
                idx = jobs.index(job)
                when = (f"{done / total * 100:3.0f}%  "
                        f"~{active_eta.get(idx, 0.0) * 60:.0f}min")
            else:
                when = (f"     {ihlib.homelab_job_hours(info, total - done) * 60:.0f}min"
                        " once started, alone")
            print(f"    {names.get(job.get('target'), job.get('target')):28s} "
                  f"-> L{job.get('target_level')}  {when}  +{pts}pts  "
                  f"[{ihlib.format_cost(job.get('cost_snapshot'))}]")
    if in_flight_points:
        free = (info.get("max_build_slots") or 0) - len(jobs)
        room = (info.get("max_queue_jobs") or 0) - len(pending)
        print(f"    (in-flight progress points: +{in_flight_points}"
              f" -> {points + in_flight_points:,}; "
              f"{free} slot(s) free, {room} queue place(s) free)")

    queued_targets = {job.get("target") for job in jobs + pending}
    installs = definitions.get("installs") or []
    install_names = {d.get("type"): d.get("name")
                     for d in (installs if isinstance(installs, list)
                               else installs.values())}
    free = (info.get("max_build_slots") or 0) - len(jobs)
    room = (info.get("max_queue_jobs") or 0) - len(pending)
    if free or room:
        picks = ihlib.homelab_fill_suggestions(cap, limit=free + room)
        print(f"\n  QUEUE ({free} slot(s), {room} queue place(s) free) — ranked "
              f"by pts/h, because tick throughput is a FIXED pool split across "
              f"active jobs (mechanics.md §15). More slots do NOT add rate;\n"
              f"  they only buffer work so progress never stops. Running a job "
              f"alone is how you finish it soonest, at the cost of points:")
        for p in picks:
            print(f"    {p['name']:26s} -> L{p['target_level']:<4} "
                  f"{p['pts_per_hour']:>4.0f}pts/h  +{p['points']:>3}pts  "
                  f"{p['hours']:.1f}h  "
                  f"{ihlib.format_cost(p['cost'])}")
            print(f"        under [{p['section']}]  {p['description'][:70]}")
            if p["unmodelled"]:
                print(f"        !! UNMODELLED — carries {', '.join(p['unmodelled'])}, "
                      f"which nothing in CRAFT_WEIGHTS prices. It is listed "
                      f"because it\n           cannot be RANKED, not because it "
                      f"lost: a 0.000 here means unpriced, not worthless.")
        if not picks:
            print("    nothing affordable left un-queued")

    print("\n  purchasable now (gate <= level, install present, below max),")
    print("  ranked the way QUEUE ranks: progress points per slot-hour, but")
    print("  jobs within HOMELAB_PTS_TOLERANCE of the best rate are ordered")
    print("  by the STAT they deliver. `score` is on the CRAFT_WEIGHTS scale,")
    print("  directly comparable to a gear affix and to `ih.py hardware` --")
    print("  hardware %, homelab % and equipment % share one pool (§13).")
    print("  score 0.000 is a real answer for resource and gather-XP")
    print("  upgrades — they pay in currencies bought at ~2 cr/unit. It is")
    print("  NOT an answer on rows marked UNMODELLED: those deliver a stat")
    print("  the game tracks and nothing here prices, so the 0.000 is")
    print("  missing rather than measured (10 Aug 2026: Thermal Budget).")
    rows = []
    for u in ihlib.iter_homelab_upgrades(homelab, definitions):
        gate = u["def"].get("unlock_level", 0)
        if gate > level or not u["install_present"] or not u["next"]:
            continue
        hours = ihlib.homelab_job_hours(info, u["next"].get("duration_ticks") or 0)
        pts = u["next"].get("progress_points", 0)
        rows.append((pts / hours if hours else 0, hours, u))
    best_rate = max((r[0] for r in rows), default=0.0)
    cutoff = best_rate * (1.0 - ihlib.HOMELAB_PTS_TOLERANCE)
    breakdown = cap["state"].get("statsBreakdown")
    rows.sort(key=lambda r: (r[0] < cutoff,
                             -ihlib.homelab_upgrade_score(r[2]["def"]), -r[0]))
    for pts_hr, hours, u in rows:
        d, nxt = u["def"], u["next"]
        section = install_names.get(u["install"], u["install"])
        queued = "  [QUEUED]" if d["type"] in queued_targets else ""
        est = "~" if nxt.get("estimated") else ""
        maxed = f"/{u['max_level']}" if u["max_level"] else ""
        print(f"    {d.get('name'):26s} L{u['level']}{maxed:<5} "
              f"+{nxt.get('progress_points', 0):>3}pts "
              f"{est}{hours:4.1f}h  {pts_hr:5.0f}pts/h  "
              f"score {_homelab_score_cell(d, breakdown)}  "
              f"{est}{ihlib.format_cost(nxt.get('cost'))}{queued}")
        print(f"        [{section}]  {(d.get('description') or '')[:80]}")
    upcoming = sorted({u["def"].get("unlock_level", 0)
                       for u in ihlib.iter_homelab_upgrades(homelab, definitions)
                       if u["def"].get("unlock_level", 0) > level})[:2]
    for gate in upcoming:
        gated = [u["def"].get("name") for u in ihlib.iter_homelab_upgrades(homelab, definitions)
                 if u["def"].get("unlock_level", 0) == gate]
        print(f"\n  unlocks at level {gate}: {', '.join(gated)}")
    installs = definitions.get("installs") or []
    pending = [d for d in (installs if isinstance(installs, list) else installs.values())
               if not (homelab.get("installed") or {}).get(d.get("type"))]
    if pending:
        print("\n  installs not yet built:")
        for d in sorted(pending, key=lambda d: d.get("unlock_level", 0)):
            gate = d.get("unlock_level", 0)
            state = "available NOW" if gate <= level else f"gated: homelab {gate}"
            print(f"    {d.get('name'):28s} {ihlib.format_cost(d.get('cost')):<24} ({state})")


def _plan_rows(plan):
    """{track name -> (current_level, target_level, chip_delta)} for the buys."""
    return {name: (level, target, cost)
            for name, _t, level, target, _v, cost in plan if target > level}


def _print_hardware_plan(hw, stats_breakdown, spendable):
    """SPEND / RESET blocks: what to do with the chips, on the weaker reading.

    Added 10 Aug 2026. Before it, `hardware` ranked tracks by value-per-1K and
    stopped — so the standing advice for an idle balance was a ranking, and
    the reset was announced with a refund figure and no idea whether taking it
    was worth anything. Both gaps mattered on the same day: 601,768 chips idle
    and a free reset that had been available since 1 Aug unpriced.

    The plan is built under `suspect_free_weights()`, not the raw ones. Chips
    are the least reversible spend in the game (no sell-back outside the
    monthly reset) and `locks` already decides irreversible questions on the
    weaker of the two readings; this is the same rule applied to the same
    class of decision. The believing plan is not hidden — every row the two
    disagree about is printed with the chips at stake.
    """
    curve = ihlib.hardware_cost_curve(hw, family="combat")
    if curve is None:
        return
    sf = ihlib.suspect_free_weights()
    plan = ihlib.hardware_plan(hw, stats_breakdown, spendable, curve=curve,
                               weights=sf)
    raw_plan = ihlib.hardware_plan(hw, stats_breakdown, spendable, curve=curve)
    buys, raw_buys = _plan_rows(plan), _plan_rows(raw_plan)
    reset_first = bool(hw.get("can_reset"))
    if buys:
        print(f"\n  SPEND {spendable:,.0f} chips — equal-marginal-value "
              f"allocation, planned under DISBELIEF of the flagged families")
        print("  (chips cannot be sold back outside the monthly reset, so this "
              "ranks on the\n   weaker reading, exactly as `locks` does):")
        if reset_first:
            print("  ** this is the plan for NOT resetting. A reset is "
                  "available and priced below;\n     if you take it, use the "
                  "re-buy schedule there instead — these two are\n     "
                  "alternatives, not a sequence. **")
        for name, (level, target, cost) in sorted(buys.items(),
                                                  key=lambda kv: -kv[1][2]):
            print(f"    {name:26s} L{level} -> L{target}  {cost:,.0f} chips")
    # Only CATEGORICAL disagreements are worth a line: a track one reading
    # funds and the other does not. Every other row differs by a few levels
    # purely because the budget freed by dropping a track has to land
    # somewhere, and printing those buries the one that decides anything.
    # A threshold would need a registered constant; "bought or not" needs none.
    for name in sorted(set(buys) ^ set(raw_buys)):
        funded, row = ("believing", raw_buys[name]) if name in raw_buys \
            else ("disbelieving", buys[name])
        _level, target, cost = row
        print(f"    !! the two readings DISAGREE on {name}: only the "
              f"{funded} plan funds it, at L{target} for {cost:,.0f} chips "
              f"({cost / max(spendable, 1):.0%} of the budget)")
    gain = ihlib.hardware_reset_gain(hw, stats_breakdown, spendable,
                                     curve=curve, weights=sf)
    if not gain:
        return
    print(f"\n  RESET vs BUY-ON-TOP — re-cutting all "
          f"{hw.get('highest_hardware_levels_held')} held levels is worth "
          f"{gain['gain']:+.1f} score")
    print(f"    keep levels, spend {spendable:,.0f} chips     -> banked score "
          f"{gain['keep_score']:.1f}")
    print(f"    reset, spend {gain['budget']:,.0f} chips       -> banked score "
          f"{gain['reset_score']:.1f}")
    shortfall = gain["refund_shortfall"]
    shortfall = f"{shortfall:+.1%}" if shortfall is not None else "un-modelled"
    print(f"    the game's refund of {gain['refund_chips']:,.0f} chips is "
          f"{shortfall} against the fitted curve's\n    "
          f"{gain['modelled_refund']:,.0f} for the levels held, which is the "
          f"ground truth the whole cost\n    model self-checks on. Only the "
          f"all-sections option is priced: it dominates every\n    subset.")
    cross = gain["gain_cross"]
    agree = "AGREE" if (cross > 0) == (gain["gain"] > 0) else "DISAGREE"
    print(f"    scored under the OTHER weighting the same two plans read "
          f"{cross:+.1f} — the two\n    readings {agree}. This check is not "
          f"decoration: planning under disbelief does\n    not merely decline "
          f"to buy a flagged family, it tears DOWN levels of it already\n"
          f"    held, so 'the refund is full value' does not by itself make a "
          f"re-cut safe.")
    for name, (_l, target, cost) in sorted(
            _plan_rows(gain["reset_plan"]).items(), key=lambda kv: -kv[1][2]):
        print(f"    re-buy  {name:26s} -> L{target}  {cost:,.0f} chips")
    print("    NOT MODELLED, and it is what the action WRITES: an all-sections "
          "reset also\n    zeroes the unscored economy tracks (Drop Rate "
          "Amplifier, Loot Filter, Power\n    Supply), which are bought with "
          "HACKCOIN. The refund returns "
          f"{(gain['refund'].get('hackcoin') or 0)} hackcoin — full value, so "
          "restoring them\n    is a wash, but it is a wash you have to spend "
          "back by hand.")


def _homelab_score_cell(defn, stats_breakdown):
    """The score column: a number, or why there isn't one.

    `0.000` and `UNMODELLED` are different claims and printing both as the
    former is how Thermal Budget sat at the bottom of this list.
    """
    unmodelled = ihlib.homelab_unmodelled_effects(defn, stats_breakdown)
    if unmodelled:
        return f"UNMODELLED[{','.join(unmodelled)}]"
    return f"{ihlib.homelab_upgrade_score(defn):5.3f}"


def cmd_hardware(args):
    cap, path = ihlib.load_capture(args.file)
    hw = ihlib.hardware_state(cap)
    if not hw:
        sys.exit("no hardwareInfo in capture (open the Hardware Shop tab and recapture)")
    print(f"# {path.name}")
    stats_breakdown = hw.get("stats_breakdown") or {}
    # live currentPlayer balance, not the panel snapshot -- see ihlib.chip_budget
    spendable, free_chips, locked_chips = ihlib.chip_budget(cap)
    locked_note = f" (+{locked_chips:,.0f} shop-locked)" if locked_chips else ""
    stale_note = ("" if free_chips == hw.get("chips")
                  else f"  [panel snapshot said {hw.get('chips'):,.0f}]")
    # `hardware_purchased` was printed as "levels held" until 10 Aug 2026. It
    # is the LIFETIME purchase count and includes levels the 27 Jul reset
    # already refunded -- 1,671 against 850 actually held. Only the held
    # figure is what a reset hands back, so the two were 2x apart in the one
    # place a reader would use them. Checked against ground truth: across
    # every capture in the archive `highest_hardware_levels_held` equals
    # sum(current_level) exactly, and `hardware_purchased` does not.
    print(f"  chips {free_chips:,.0f}{locked_note}  "
          f"hackcoin {hw.get('hackcoin')}  "
          f"levels held {hw.get('highest_hardware_levels_held')} "
          f"(bought {hw.get('hardware_purchased')} lifetime)"
          f"{stale_note}")
    if hw.get("can_reset"):
        refund = next((o.get("refund") for o in hw.get("reset_section_options") or []
                       if o.get("section") == "all"), None)
        print(f"  RESET AVAILABLE ({hw.get('reset_preview_mode')}, "
              f"{hw.get('reset_cooldown_mode')}): all-hardware refund "
              f"{ihlib.format_cost(refund)}")
    for _line in ihlib.pending_refit_banner():
        print("  " + _line)
    _print_hardware_plan(hw, stats_breakdown, spendable)
    print("\n  combat tracks by value per 1K chips (CRAFT_WEIGHTS heuristic on the")
    print("  current build; additive pooling confirmed — mechanics.md §13).")
    print("  This ranks raw SCORE, which is NOT comparable across stat")
    print("  families — rows marked !! carry a family in SUSPECT_WEIGHTS,")
    print("  whose own note says why it is not trusted:")
    combat_rows, economy_rows = [], []
    for d in hw.get("definitions") or []:
        value = ihlib.hardware_track_value(d, stats_breakdown)
        cost = d.get("next_cost") or {}
        if value:
            per_1k = value / max(cost.get("chips", 0), 1) * 1000
            combat_rows.append((per_1k, value, d))
        else:
            economy_rows.append(d)
    for per_1k, value, d in sorted(combat_rows, key=lambda r: -r[0]):
        cost = d.get("next_cost") or {}
        afford = "" if d.get("can_afford") else "  [CAN'T AFFORD]"
        depth_note = ihlib.hardware_track_depth_note(d)
        print(f"    {d.get('name'):26s} L{d.get('current_level'):>3}  "
              f"value/lvl {value:5.2f}  per-1K-chips {per_1k:6.2f}  "
              f"next {ihlib.format_cost(cost)}{afford}")
        if depth_note:
            print(f"        !! {depth_note}")
    print("\n  economy/farming tracks (not scored):")
    for d in sorted(economy_rows, key=lambda d: d.get("name") or ""):
        print(f"    {d.get('name'):26s} L{d.get('current_level'):>3}  "
              f"next {ihlib.format_cost(d.get('next_cost'))}  "
              f"{(d.get('description') or '')[:60]}")


def cmd_contract(args):
    """Price a §10.1 craft contract by simulation instead of by discount."""

    for _line in ihlib.pending_refit_banner():
        print("  " + _line)
    cap, path = ihlib.load_capture(args.file)
    ladders = ihlib.tier_ladders_archive()
    matches = ihlib.find_items(cap, args.item)
    base_item = next((i for _w, _s, i in matches if (i.get("stability") or 0) > 0),
                     matches[0][2] if matches else None)
    if base_item is None:
        sys.exit(f"no item matching {args.item!r}")
    slot = base_item.get("slot")
    equipped = (cap["state"].get("equipmentData") or {}).get(slot)
    if equipped is None:
        sys.exit(f"nothing equipped in {slot} to compare against")
    baseline = ihlib.weighted_score(ihlib.item_stat_totals(equipped))
    preserve = ihlib.stability_preserve_chance(cap)
    print(f"# {path.name}")
    print(f"  base     {base_item.get('name')}  Stability "
          f"{base_item.get('stability')}  floor {args.floor} -> budget "
          f"{(base_item.get('stability') or 0) - args.floor}")
    print(f"  vs equipped {equipped.get('name')}  score {baseline:.1f}"
          f"   (Snapshot Backups preserve {preserve:.0%})")

    # Phases are carried as affix UIDs, never display names -- two affixes on
    # one item can share a name (ihlib.affix_entries).
    phases = []
    for spec in args.phase:
        name, _, tier = spec.rpartition(":")
        if not name or not tier.strip().lstrip("T").isdigit():
            sys.exit(f"bad --phase {spec!r}; use \"of Haste:4\"")
        try:
            uid = ihlib.resolve_affix_uid(base_item, name.strip())
        except ValueError as exc:
            sys.exit(str(exc))
        phases.append((uid, int(tier.strip().lstrip("T"))))
    if not phases:                       # default to plan_craft's own plan
        plan = ihlib.plan_craft(base_item, ladders, floor=args.floor,
                                preserve=preserve)
        phases = [(uid, to) for uid, _label, _frm, to, _c, _e in plan["steps"]]
        print("  phases taken from plan_craft (pass --phase to override)")
        # `plan_craft` maximises RAW score, so when a flagged family wins the
        # greedy search this default is the contract `suspect_free_weights`
        # calls "one nobody would run under those beliefs". `potential` and
        # `locks` both price the base on the re-planned reading; without this
        # block the one command CLAUDE.md mandates for every craft silently
        # disagreed with both (found in review, 8 Aug 2026).
        eq_totals_c = ihlib.item_stat_totals(equipped)
        bad, labels = ihlib.suspect_share(
            ihlib.score_contributions(plan["totals"], eq_totals_c))
        sf = ihlib.suspect_free_weights()
        plan_sf = ihlib.plan_craft(base_item, ladders, floor=args.floor,
                                   preserve=preserve, weights=sf)
        phases_sf = [(uid, to) for uid, _l, _f, to, _c, _e in plan_sf["steps"]]
        if labels and abs(bad) > 2 and phases_sf and phases_sf != phases:
            d_sf = (ihlib.weighted_score(plan_sf["totals"], sf)
                    - ihlib.weighted_score(eq_totals_c, sf))
            print(f"  !! this plan leans {abs(bad):.1f} on "
                  f"{'/'.join(labels)}. Re-planned without them the base is "
                  f"worth {d_sf:+.1f} on a DIFFERENT contract:")
            print("     " + ", ".join(
                f"{label} T{f}->T{t}" for _uid, label, f, t, _c, _e
                in plan_sf["steps"]))
            print("     rerun with --ex-suspect to price that one instead")
            if args.ex_suspect:
                phases = phases_sf
                print("     --ex-suspect: pricing the re-planned contract")
    if not phases:
        sys.exit("no phases to run")

    tiers_now = {uid: a.get("tier")
                 for uid, _side, a in ihlib.affix_entries(base_item)}
    print("\n  contract (execution order matters -- see best_contract_order):")
    for uid, tier in phases:
        cur = tiers_now.get(uid)
        if cur is None:
            sys.exit(f"{base_item.get('name')} has no affix {uid!r}")
        att = sum(ihlib.version_upgrade_expected_attempts(x) for x in range(tier + 1, cur + 1))
        stab = sum(ihlib.version_upgrade_expected_stability(x, preserve)
                   for x in range(tier + 1, cur + 1))
        print(f"    {ihlib.affix_label(base_item, uid):34s} T{cur} -> T{tier}"
              f"   exp {att:4.1f} attempts / {stab:4.1f} Stability")

    sim = ihlib.simulate_contract(base_item, ladders, phases,
                                  floor=args.floor, preserve=preserve,
                                  trials=args.trials, baseline=baseline)
    print(f"\n  outcome distribution over {sim['trials']:,} runs "
          "(delta vs equipped):")
    print(f"    mean {sim['mean']:+6.2f}   median {sim['median']:+6.2f}   "
          f"p10 {sim['p10']:+6.2f}   p90 {sim['p90']:+6.2f}   "
          f"worst {sim['min']:+6.2f}")
    print(f"    P(> +{ihlib.UPGRADE_BAND:.0f} UPGRADE_BAND) "
          f"{sim['p_upgrade']:6.1%}     P(> 0) {sim['p_positive']:6.1%}"
          f"     P(all phases complete) {sim['p_complete']:6.1%}")
    print("    Prefer this to the flat ~5-point contract discount when the "
          "call is close;\n    a discount cannot see that phases are "
          "non-separable (Stability spent cuts\n    Compile, which multiplies "
          "everything) nor that the downside is bounded.")

    if args.order and len(phases) > 1:
        print("\n  phase-order search (best P(upgrade) first):")
        for order, s in ihlib.best_contract_order(
                base_item, ladders, phases, floor=args.floor,
                preserve=preserve, trials=max(args.trials // 5, 2000),
                baseline=baseline):
            label = " -> ".join(ihlib.affix_label(base_item, u) for u, _ in order)
            print(f"    {label:52s} P(>+{ihlib.UPGRADE_BAND:.0f}) "
                  f"{s['p_upgrade']:5.1%}  "
                  f"mean {s['mean']:+5.2f}  p10 {s['p10']:+5.2f}")
    if getattr(args, "deepen", False):
        print("\n  deeper-than-planned variants (plan_craft stops at the "
              "expected budget; over-committing is bounded-downside):")
        for cand, sim in ihlib.deepen_search(base_item, ladders, phases,
                                             floor=args.floor,
                                             preserve=preserve,
                                             baseline=baseline)[:6]:
            label = ", ".join(f"{ihlib.affix_label(base_item, u)}->T{t}"
                              for u, t in cand)
            print(f"    {label:52s} mean {sim['mean']:+7.2f}  p10 {sim['p10']:+6.2f}"
                  f"  p90 {sim['p90']:+7.2f}  P(>+{ihlib.UPGRADE_BAND:.0f}) "
                  f"{sim['p_upgrade']*100:5.1f}%")



def cmd_cadence(args):
    """Fight cadence from the game's own death clock (mechanics.md §14)."""
    rows = ihlib.fight_cadence()
    if not rows:
        sys.exit("no death records in the stream ledger")
    values = sorted(s for _ms, s in rows)
    mid = statistics.median(values)
    print(f"  n={len(values)}  median {mid:.3f} s/fight  "
          f"sd {statistics.pstdev(values):.3f}  "
          f"range {values[0]:.3f}-{values[-1]:.3f}")
    print(f"  -> {3600 / mid:.0f} fights/hour")
    print("  Fight cadence is a fixed real-time tick. Attack speed does NOT")
    print("  buy fights per hour -- it pays in rounds per fight. Rewards per")
    print("  hour are set by streak depth. (mechanics.md §14)")


def cmd_sims(args):
    """Hacking Simulator runs banked by the userscript (docs/simulator-protocol.md)."""
    rows = ihlib.sim_rows(mode=args.mode)
    crows = ihlib.cicd_rows()
    if not rows and not crows:
        sys.exit(
            "no simulator runs banked yet.\n"
            "  Turn on 'Sim capture' in the IH Capture panel, then press RUN\n"
            "  in the game's Homelab > Hacking Simulator panel. See\n"
            "  docs/simulator-protocol.md.")

    verdict, detail = ihlib.sim_regime_check(rows)
    print(f"REGIME: {verdict} — {detail}\n")

    print(f"{'when':>8}  {'zone':<18} {'gear':<10} {'lvl':>6} "
          f"{'n':>4} {'win%':>6}  {'hit%':>6} {'rounds':>7}  loss-type")
    for row in rows:
        # UTC, matching the day-block grouping below (was local time)
        when = (datetime.fromtimestamp(row["seen_ms"] / 1000,
                                       timezone.utc).strftime("%H:%M:%S")
                if row.get("seen_ms") else "-")
        rate = row.get("win_rate")
        # unbiased per-attack hit rate: 2-attack rounds only (ihlib.unbiased_hit_rate)
        attacks = sum(f["hit_trials"] for f in row["fights"])
        hits = sum(f["hit_hits"] for f in row["fights"])
        rounds = [f["rounds"] for f in row["fights"]]
        arch = (row.get("loss_archetype") or {}).get("class") or "-"
        print(f"{when:>8}  {str(row['zone'] or '-'):<18} "
              f"{str(row['gear']):<10} {row['enemy_level'] or 0:>6} "
              f"{row['n']:>4} "
              f"{(rate * 100 if rate is not None else 0):>5.1f}%  "
              f"{(hits / attacks * 100 if attacks else 0):>5.1f}% "
              f"{(statistics.mean(rounds) if rounds else 0):>7.1f}  {arch}")

    print(f"\n  {len(rows)} run(s), "
          f"{sum(r['n'] for r in rows):,} simulated fights, "
          f"{sum(len(r['fights']) for r in rows)} fully logged")
    levels = sorted({r["enemy_level"] for r in rows if r.get("enemy_level")})
    gears = sorted({r["gear"] for r in rows})
    if levels:
        print(f"  enemy levels covered: {levels[0]}-{levels[-1]} "
              f"({len(levels)} distinct)")
    print(f"  gear configurations: {', '.join(map(str, gears))}")
    if len(gears) == 1:
        print("  NOTE: one gear configuration only — this sample can fit the "
              "enemy-level\n        response but CANNOT price any stat weight. "
              "Create a second gear\n        set that differs in one stat and "
              "re-run at a matched level.")

    if crows:
        print("\n# CI/CD Pipeline — full-streak runs "
              "(each row aggregates `sims` simulated streaks)")
        print(f"{'when':>8}  {'zone':<18} {'set':<10} {'sims':>4} "
              f"{'streak':>7} {'min-max':>9}  final-enemy")
        for r in crows:
            when = (datetime.fromtimestamp(r["seen_ms"] / 1000,
                                           timezone.utc).strftime("%H:%M:%S")
                    if r.get("seen_ms") else "-")
            print(f"{when:>8}  {str(r['zone'] or '-'):<18} "
                  f"{str(r['gear_set']):<10} {r['sims'] or 0:>4} "
                  f"{r['streak_avg'] or 0:>7.1f} "
                  f"{r['streak_min'] or 0:>4}-{r['streak_max'] or 0:<4}  "
                  f"{r['loss_archetype'] or '-'}")
        # Arm summaries are PER UTC DAY-BLOCK, and arms are identified by
        # their player_combat_stats vector, never the label. Until 6 Aug 2026
        # this pooled every day's rows by gear_set label — mixing the 5 Aug
        # driver pair with the 6 Aug kernel pair under the same "A"/"B" and
        # printing a cross-experiment difference that meant nothing.
        by_day = {}
        for r in crows:
            if r.get("streak_avg") is None or not r.get("seen_ms"):
                continue
            day = datetime.fromtimestamp(
                r["seen_ms"] / 1000, timezone.utc).date().isoformat()
            by_day.setdefault(day, []).append(r)
        for day, rs in sorted(by_day.items()):
            arms = {}
            for r in rs:
                fp = tuple(sorted((r.get("player_combat_stats") or {}).items())) \
                    or r["gear_set"]
                arms.setdefault(fp, []).append(r)
            if len(arms) < 2:
                continue
            print(f"\n  {day} block — arms by stat vector (mean of "
                  f"run-averages ± SE; labels shown are display only):")
            named = []
            for _fp, group in sorted(arms.items(),
                                    key=lambda kv: kv[1][0]["seen_ms"]):
                labels = sorted({str(g["gear_set"]) for g in group})
                means = [g["streak_avg"] for g in group]
                se = (statistics.stdev(means) / len(means) ** 0.5
                      if len(means) > 1 else float("nan"))
                named.append(("/".join(labels), means))
                print(f"    {'/'.join(labels):<10} runs={len(means)}  "
                      f"{statistics.mean(means):7.2f} ± {se:.2f}")
            if len(named) == 2:
                (na, ma), (nb, mb) = named
                diff = statistics.mean(ma) - statistics.mean(mb)
                se = ((statistics.variance(ma) / len(ma) +
                       statistics.variance(mb) / len(mb)) ** 0.5
                      if min(len(ma), len(mb)) > 1 else float("nan"))
                print(f"    {na} − {nb} = {diff:+.2f} ± {se:.2f}")
        last = crows[-1]
        if last.get("daily_used") is not None:
            print(f"  daily budget at last run: {last['daily_used']}"
                  f"/{last['daily_limit']} used")


def _hackcoin_per_hour(contract, fights_per_hour):
    """Hackcoin per hour of COMBAT for a contract, 0 if not combat-driven.

    `kills` advances once per won fight. `drops` advances on a contract-item
    drop at CONTRACT_DROP_PER_WIN (0.296/win, re-measured 31 Jul 2026 from
    board accrual with the contract active -- the 29 Jul ledger fit of 0.0534
    pooled mostly-inactive windows and was 5.5x low). `harvest` is gathering,
    not combat -- no rate is measured, so it returns 0 rather than a guess.
    """
    target = contract.get("target") or 0
    hc = (contract.get("rewards") or {}).get("hackcoin") or 0
    done = contract.get("progress") or 0
    left = max(target - done, 0)
    if not left or not hc or not fights_per_hour:
        return 0.0
    kind = contract.get("type")
    if kind == "kills":
        return hc / (left / fights_per_hour)
    if kind == "drops":
        return hc / (left / (fights_per_hour * ihlib.CONTRACT_DROP_PER_WIN))
    return 0.0


# ---- Audit checks -----------------------------------------------------------
# Each check is an independent function `(cap, ctx) -> [(KIND, message)]` so it
# can be unit-tested against a synthetic capture without running the CLI —
# extracted from a single ~330-line cmd_audit in the public-release audit,
# which also converted CLAUDE.md's "if you find an anomaly the audit missed,
# add the check" rule into a testable contract: add a function, register it in
# AUDIT_CHECKS, test it. `ctx` carries the little cross-check state that
# exists (the stream-drift field deltas, consumed by the chips check). Order
# matters and is deliberate: known-wrong constants outrank staleness outranks
# everything else.


def _audit_pending_refits(cap, ctx):
    # Known-wrong constants outrank every other finding: they mean the verdicts
    # this tool is about to print are already known to be false. Listed first,
    # by design -- an unfixed constant is progress being lost silently, which is
    # exactly what this sweep exists to catch.
    return [("KNOWN-WRONG", f"{r['name']} applied as {r['applied']} "
                            f"since {r['opened']}. Blocked on: "
                            f"{r['blocked_on']} UNBLOCK: {r['unblock']}")
            for r in ihlib.pending_refits()]


def _audit_stream_drift(cap, ctx):
    # the whole capture can be stale, not just a panel inside it: the
    # auto-stream keeps running after the last capture click, so its newest
    # `stats` record outranks everything in the file (27 Jul 2026: a capture
    # showing 44,582 unspent chips against a streamed 4,140 — already spent)
    lag, changed = ihlib.capture_stream_drift(cap)
    ctx["stream_changed"] = changed
    if lag is None or lag <= 300:
        return []
    detail = ("; ".join(f"{f} {was:,.0f} -> {now:,.0f}"
                        if isinstance(was, (int, float)) else
                        f"{f} {was} -> {now}"
                        for f, was, now in changed)
              or "no streamed field changed, but homelab job progress and "
                 "hardware levels are not streamed — assume both moved")
    return [("OUTDATED", f"capture is {lag / 60:,.0f} min behind the "
                         f"combat stream ({detail}) — recapture before "
                         f"spending anything")]


def _audit_stale_panels(cap, ctx):
    return [("STALE", f"{section}: {reason} — reopen that game tab "
                      f"and recapture before trusting it")
            for section, reason in ihlib.stale_panels(cap)]


def _audit_capture_integrity(cap, ctx):
    # A truncated capture silently thins the archive-wide tier ladders every
    # craft verdict rests on (`ihlib.LADDER_FIT_SKIPPED` counts skips when a
    # fit runs; `potential`/`contract` print them). This is the cheap standing
    # proxy: a JSON capture that does not end in '}' is truncated — caught
    # without parsing 350MB of archive on every sweep.
    bad = []
    for path in ihlib.capture_paths():
        try:
            with open(path, "rb") as fh:
                fh.seek(0, 2)
                size = fh.tell()
                if size == 0:
                    bad.append((path.name, "empty file"))
                    continue
                fh.seek(-1, 2)
                if fh.read(1) != b"}":
                    bad.append((path.name, "does not end in '}' — truncated"))
        except OSError as error:
            bad.append((path.name, f"unreadable ({error.__class__.__name__})"))
    return [("CORRUPT", f"{name}: {why} — it silently thins the archive tier "
                        f"ladders; repair or remove it")
            for name, why in bad]


def _audit_sim_ledger(cap, ctx):
    # hub-regression sentinel: a duplicate sim row written after the 5 Aug
    # 2026 cross-day dedup fix means the hub is double-ingesting the
    # profiler panel's replayed results again (pre-fix rows are grandfathered
    # and filtered by ihlib.sim_records)
    sim_dupes = ihlib.sim_ledger_duplicates(after="2026-08-05")
    if not sim_dupes:
        return []
    return [("LEDGER", f"{sim_dupes} duplicate sim run(s) written "
                       f"after the 5 Aug 2026 hub dedup fix — "
                       f"capture-hub.py's seen-set has regressed; "
                       f"fix it before trusting sim counts")]


def _audit_stat_model(cap, ctx):
    # model self-check against the game's own numbers: if composed_stat_total cannot
    # reproduce a stat, every swap projection touching it is unsound
    return [("MODEL", f"composed_stat_total({stat}) = {modelled:,.4f} but the "
                      f"game reports {reported:,.4f} — fix its family "
                      f"in ihlib before trusting any projection using it")
            for stat, reported, modelled in ihlib.validate_stat_totals(cap)]


def _audit_hardware(cap, ctx):
    hw = ihlib.hardware_state(cap)
    if not hw:
        return []
    flags = []
    sb = hw.get("stats_breakdown") or {}
    locked = hw.get("locked_resources") or {}
    spendable, free_chips, locked_chips = ihlib.chip_budget(cap)
    # a "spend these chips" flag off an outdated capture is how a balance
    # that is already spent gets re-recommended -- say so on the same line
    changed = ctx.get("stream_changed") or []
    streamed = dict((f, now) for f, _, now in changed).get("chips")
    if spendable > 20000:
        correction = (f"; the stream says {streamed:,.0f} — already spent, "
                      f"recapture" if streamed is not None else "")
        flags.append(("IDLE", f"{spendable:,.0f} chips unspent "
                              f"({locked_chips:,.0f} shop-locked)"
                              f"{correction}"))
    if locked.get("hackcoin"):
        flags.append(("IDLE", f"{locked['hackcoin']} shop-locked hackcoin — "
                              f"unusable outside Hardware; spend or lose it"))
    for d in hw.get("definitions") or []:
        level = d.get("current_level") or 0
        value = ihlib.hardware_track_value(d, sb)
        if level and value == 0:
            flags.append(("DEAD", f"{d.get('name')} L{level} scores 0 — its "
                                  f"multiplicand is zero; those chips do nothing"))
    # A free reset sitting unused is progress already lost, on a monthly
    # clock -- the 10 Aug one had been available since 1 Aug because the
    # sweep announced the refund and never priced it. Priced on the same
    # disbelieving weights the spend plan uses, so the flag can never argue
    # for a re-cut that only a flagged family justifies.
    gain = ihlib.hardware_reset_gain(hw, sb, spendable,
                                     weights=ihlib.suspect_free_weights())
    # Both readings must agree before this becomes an unprompted flag. A
    # re-cut that wins only under disbelief is a real judgement call, and
    # `ih.py hardware` is where it belongs -- not in a sweep whose whole
    # contract is "this is silently costing you progress right now".
    if gain and gain["gain"] > 0 and gain["gain_cross"] > 0:
        flags.append(("RESET", f"a free hardware reset is available and "
                               f"UNUSED — re-cutting all "
                               f"{hw.get('highest_hardware_levels_held')} "
                               f"held levels and re-spending "
                               f"{gain['budget']:,.0f} chips is worth "
                               f"{gain['gain']:+.1f} score over buying on "
                               f"top of what you hold "
                               f"({gain['keep_score']:.1f} -> "
                               f"{gain['reset_score']:.1f}). The refund is "
                               f"full value, so this cannot lose — "
                               f"ih.py hardware"))
    return flags


def _audit_homelab(cap, ctx):
    homelab, definitions, info = ihlib.homelab_state(cap)
    if not homelab:
        return []
    flags = []
    active = len(homelab.get("active_jobs") or [])
    pend = len(homelab.get("pending_jobs") or [])
    free = (info.get("max_build_slots") or 0) - active
    room = (info.get("max_queue_jobs") or 0) - pend
    # CORRECTED 29 Jul 2026. This used to flag every free slot as lost
    # progress. It is not: homelab tick throughput is a FIXED pool split
    # evenly across active jobs (mechanics.md §15), so one job running
    # alone earns exactly what four running together earn. Free slots cost
    # nothing while at least one job is going -- they only buffer work.
    # The real loss is throughput reaching ZERO, i.e. nothing active AND
    # nothing queued. Flag that hard; mention free slots only as coverage.
    if not active and not pend:
        picks = ihlib.homelab_fill_suggestions(cap, limit=3)
        named = "; ".join(
            f"{p['name']} [{p['section']}] -> L{p['target_level']} "
            f"({p['pts_per_hour']:.0f}pts/h, +{p['points']}pts, "
            f"{p['hours']:.1f}h, {ihlib.format_cost(p['cost'])})"
            for p in picks) or "nothing affordable is available"
        flags.append(("IDLE", f"homelab is making NO progress — 0 active "
                              f"jobs and 0 queued. Start: {named}"))
    elif free or room:
        hours_buffered = ihlib.homelab_job_hours(info, sum(
            ((j.get("duration_ticks") or 0) - (j.get("progress_ticks") or 0))
            for j in (homelab.get("active_jobs") or [])
            + (homelab.get("pending_jobs") or [])))
        flags.append(("COVERAGE", f"homelab has {free} slot(s) and {room} "
                                  f"queue place(s) free — this does NOT "
                                  f"slow the running jobs (throughput is "
                                  f"split, not added), but only "
                                  f"~{hours_buffered:.1f}h of work is "
                                  f"buffered before progress stops"))
    gates = [(d.get("name"), (d.get("cost") or {}).get("hackcoin") or 0)
             for d in (definitions.get("installs") or [])
             if not (homelab.get("installed") or {}).get(d.get("type"))]
    need = sum(hc for _, hc in gates)
    # locked hackcoin cannot fund installs (mechanics.md §14) -- free only
    if need and (info.get("hackcoin") or 0) < need:
        flags.append(("RESERVE", f"{info.get('hackcoin')} free hackcoin vs "
                                 f"{need} needed for pending installs"))
    flags.extend(_audit_cicd_budget(cap, homelab, definitions))
    return flags


def _audit_cicd_budget(cap, homelab, definitions):
    # Free measurement capacity that expires daily. Added 6 Aug 2026: the
    # first fresh CI/CD budget after first light went unflagged by this
    # sweep. Runs do not bank across days (checked over the 3-5 Aug gap),
    # and the register's remaining asserted constants all name the
    # pipeline as their unblock -- budget expiring while those fits are
    # pending is progress lost silently: the held Corrupt crafts stay
    # blocked on a number an idle instrument could be measuring.
    #
    # This line used to name the hardware reset re-cut as blocked here too.
    # It is not, and saying so parked a free monthly reset for ten days on a
    # constant that cannot reach it: NO hardware track carries MaxHP
    # (`max_hp.hardware` is 0 and no definition has a max_hp effect), so the
    # MaxHP fit cannot move a chip. Corruption is the one flagged family with
    # a track, and `hardware` now plans under disbelief of it rather than
    # waiting -- see `_print_hardware_plan`.
    if not definitions:
        return []
    cicd_level = next((u["level"] for u in
                       ihlib.iter_homelab_upgrades(homelab, definitions)
                       if u["def"].get("name") == "CI/CD Pipeline"), 0)
    pending_fits = [n.rsplit("[", 1)[-1].rstrip("]")
                    for n, _v, prov, basis, _when, _chk
                    in ihlib.assumptions()
                    if prov == "asserted" and "CI/CD" in (basis or "")]
    if not (cicd_level and pending_fits):
        return []
    note = _audit_cicd_budget_note(cicd_level)
    if note is None:
        return []
    return [("MEASURE", f"CI/CD runs unused today: {note}. They expire at "
                        f"the UTC day reset and do not bank — "
                        f"{', '.join(pending_fits)} still asserted "
                        f"with the pipeline as named unblock, and the "
                        f"held Corrupt crafts wait on that fit")]


def _audit_cicd_budget_note(cicd_level):
    """How many free simulator runs remain today, and how sure we are.

    Split out from `_audit_cicd_budget` so the branching is directly
    testable: every branch below is a 7 Aug 2026 review finding about this
    line over-advertising free capacity. Returns None when nothing is free.
    """
    today_utc = datetime.now(timezone.utc).date()
    today_rows = [r for r in ihlib.cicd_rows()
                  if r.get("seen_ms") and datetime.fromtimestamp(
                      r["seen_ms"] / 1000, timezone.utc).date() == today_utc]
    # The game reports `daily_used` alongside `daily_limit`, so take BOTH
    # halves of the fraction from the same producer. Counting ledger rows
    # instead under-counts whenever a run happened while the capture hub was
    # not streaming, which overstates the free budget -- the same
    # over-advertising this check was fixed to stop, moved into the numerator.
    used = next((r["daily_used"] for r in reversed(today_rows)
                 if r.get("daily_used") is not None), len(today_rows))
    # The game REPORTS its own daily cap on every run. Prefer that to
    # CICD_RUNS_PER_LEVEL * level, and where the two disagree say so rather
    # than picking the optimistic one: whether a mid-day level-up raises the
    # SAME day's budget is explicitly unobserved (the CICD_RUNS_PER_LEVEL
    # registry row, simulator-protocol.md par 9.2), and this check must not
    # quietly answer that open question. On 7 Aug 2026 the pipeline went L3
    # -> L4 after that day's 8 runs, all of which reported daily_limit 15;
    # the model said 20 and the check advertised 12 free runs against a
    # game-reported 7. The next run resolves it for free by reporting the
    # live cap, so name that rather than guessing.
    observed = next((r["daily_limit"] for r in reversed(today_rows)
                     if r.get("daily_limit")), None)
    modelled = ihlib.CICD_RUNS_PER_LEVEL * cicd_level
    cicd_budget = observed or modelled
    certain = max(0, cicd_budget - used)
    upper = max(certain, modelled - used)
    if not certain and not upper:
        return None
    if observed is None:
        note = f"{certain}/{modelled} (modelled from pipeline level)"
    elif observed == modelled:
        note = f"{certain}/{observed} (game-reported)"
    else:
        # Only claim a level-up when the observed cap is consistent with an
        # EARLIER level. Firing this narrative on mere disagreement would
        # assert a mid-day level-up that never happened -- and cite par 9.2
        # in support of it -- whenever CICD_RUNS_PER_LEVEL is simply wrong
        # for this level, or the game changes the cap.
        per = ihlib.CICD_RUNS_PER_LEVEL
        implied = observed / per if per else None
        levelled_up = (implied is not None and implied == int(implied)
                       and int(implied) < cicd_level)
        if levelled_up:
            note = (f"{certain} certain, up to {upper} if the "
                    f"L{int(implied)}->L{cicd_level} level-up raised today's "
                    f"cap — the last game-reported limit is {observed}, "
                    f"consistent with L{int(implied)}, and whether a mid-day "
                    f"level-up lifts the same day's budget is UNOBSERVED "
                    f"(simulator-protocol.md par 9.2). The next run reports "
                    f"the live cap and settles it")
        else:
            note = (f"{certain} (game-reported cap {observed}). NOTE the "
                    f"model says {modelled} ({per}/level x L{cicd_level}) "
                    f"and the game says {observed}, a gap no level-up "
                    f"explains — CICD_RUNS_PER_LEVEL may be wrong at this "
                    f"level. Trusting the game's figure")
    return note


def _audit_contracts(cap, ctx):
    # The board resets daily (UTC): pending contracts are replaced, the ACTIVE
    # one carries through and runs to completion (mechanics.md §20, corrected
    # 6 Aug 2026). Contracts are the only repeatable hackcoin source observed,
    # and hackcoin gates every install. Added 28 Jul 2026 -- the sweep had no
    # contract check at all; an Extended Elimination sat at 658/1424 with 2.4h.
    flags = []
    board = ihlib.contract_board(cap)
    left = board["hours_left"]
    active = board["active"]
    # NOTHING-ACCRUING check, added 31 Jul 2026: when a contract completes,
    # the active slot empties and the board earns nothing until the player
    # activates the next one. The sweep showed the pending list and the
    # unclaimed reward that day but nothing said "the clock is running on an
    # idle board" -- ~2h of board time were lost between Marathon Collection
    # completing and the next capture surfacing it.
    incomplete = [c for c in (board.get("pending") or [])
                  if (c.get("progress") or 0) < (c.get("target") or 0)]
    if not active and incomplete and (left or 0) > 0:
        idle_hc = sum((c.get("rewards") or {}).get("hackcoin") or 0
                      for c in incomplete)
        flags.append(("CONTRACT", f"NOTHING ACCRUING — no active contract "
                                  f"while {idle_hc} hc of incomplete "
                                  f"contracts sit on the board and "
                                  f"{left:.1f}h remain; activate one now"))
    if active and not active.get("completed"):
        done, target = active.get("progress") or 0, active.get("target") or 0
        rew = active.get("rewards") or {}
        pay = (f"{rew.get('credits', 0):,.0f} cr + {rew.get('chips', 0):,} "
               f"chips + {rew.get('hackcoin', 0)} hackcoin")
        window = f"{left:.1f}h left on the board" if left is not None else \
            "reset time unknown"
        if target and done < target:
            flags.append(("CONTRACT", f"{active.get('name')} at {done:,}/"
                                      f"{target:,} ({done / target * 100:.0f}%) "
                                      f"— {window}; the ACTIVE contract "
                                      f"carries through reset and runs to "
                                      f"completion (mechanics.md §20). "
                                      f"Pays {pay}"))
            # Completability, added 29 Jul 2026, CORRECTED same day. The first
            # version asserted "kills accrue only while the tab is open" from a
            # single observation (Marathon at 40/2,848 eight hours into the
            # window). That was a confound: the board holds SEVEN contracts,
            # only the active one accrues, and Marathon had merely been made
            # active minutes earlier. Offline accrual is NOT ruled out by any
            # data here -- do not re-assert it. What is measured is the fight
            # cadence, so quote combat-hours required and nothing more.
            if active.get("type") in ("kills", "drops", "harvest") and left:
                if active.get("type") == "harvest":
                    rate = ihlib.HARVEST_PER_GATHER_HOUR
                    mode = ("ACTIVE gathering (lower-bound rate; passive "
                            "accrual ~0)")
                else:
                    rate = 3600.0 / ihlib.FIGHT_CADENCE_S
                    if active.get("type") == "drops":
                        rate *= ihlib.CONTRACT_DROP_PER_WIN
                    mode = "combat"
                need_h = (target - done) / rate
                # Carry-through model (mechanics.md §20): running past reset
                # is not a loss, it is OCCUPANCY -- the new board idles while
                # the carried contract finishes. Only the clear bonus and the
                # chance to start pending contracts die with the window.
                if need_h <= left * 0.9:
                    verdict = "COMPLETES IN WINDOW"
                    tail = f"in a {left:.1f}h window"
                elif need_h <= left:
                    verdict = "TIGHT"
                    tail = (f"in a {left:.1f}h window — either way it "
                            f"finishes (carries through reset)")
                else:
                    verdict = "CARRIES PAST RESET"
                    tail = (f"vs {left:.1f}h of board — completes "
                            f"~{need_h - left:.1f}h after reset, occupying "
                            f"the slot while the NEW board idles; weigh "
                            f"its remaining hc/h against the new board's "
                            f"best (~{ihlib.BOARD_TYPICAL_BEST_HC_PER_H:.0f} "
                            f"hc/combat-h)")
                flags.append(("CONTRACT", f"  -> {verdict}: {target - done:,} "
                                          f"left = ~{need_h:.1f}h of {mode} "
                                          f"at ~{rate:.0f}/h progress, "
                                          f"{tail}"))
    # The board is not one contract. Only the active one accrues (queue
    # capacity 0), so every pending contract is hackcoin sitting still, and the
    # clear bonus needs ALL of them. Added 29 Jul 2026 after `contract_board`
    # was found to be returning only the active row -- an advisory priced this
    # board at 11 hackcoin when it was worth 25.
    pending = board.get("pending") or []
    if pending:
        rate = 3600.0 / ihlib.FIGHT_CADENCE_S
        hc = sum((c.get("rewards") or {}).get("hackcoin") or 0 for c in pending)
        flags.append(("CONTRACT", f"{len(pending)} other contract(s) on the "
                                  f"board are at 0 and earn NOTHING until made "
                                  f"active — {hc} hackcoin idle. Only the "
                                  f"active contract accrues, and pending "
                                  f"contracts are REPLACED at reset (only the "
                                  f"active one carries — start the largest "
                                  f"keeper just before reset)."))
        for c in sorted(pending, key=lambda c: -_hackcoin_per_hour(c, rate)):
            rew = (c.get("rewards") or {}).get("hackcoin") or 0
            per = _hackcoin_per_hour(c, rate)
            if per:
                eff = f"{per:.2f} hc/combat-h"
            elif c.get("type") == "harvest" and rew:
                left_n = max((c.get("target") or 0) - (c.get("progress") or 0),
                             0)
                gather_h = left_n / ihlib.HARVEST_PER_GATHER_HOUR
                eff = (f"~{rew / gather_h:.2f} hc/gather-h over ~{gather_h:.1f}h "
                       f"of ACTIVE gathering (rate is a lower bound; passive "
                       f"accrual ~0)")
            else:
                eff = "rate unmeasured (non-combat)"
            flags.append(("CONTRACT", f"    {c.get('name')} — "
                                      f"{c.get('target'):,} {c.get('type')}, "
                                      f"pays {rew} hc  [{eff}]"))
    for c in board["unclaimed"]:
        rew = c.get("rewards") or {}
        flags.append(("CONTRACT", f"{c.get('name')} is COMPLETE and unclaimed "
                                  f"— claim it: {rew.get('credits', 0):,.0f} cr "
                                  f"+ {rew.get('chips', 0):,} chips + "
                                  f"{rew.get('hackcoin', 0)} hackcoin"))
    if board["clear_bonus"] and not board["clear_bonus_claimed"]:
        flags.append(("CONTRACT", f"board-clear bonus of {board['clear_bonus']} "
                                  f"unclaimed (only if every contract clears "
                                  f"before reset)"))
    return flags


def _audit_install_budget(cap, ctx):
    # Install gates, priced against the hackcoin-backed budget rather than the
    # credit balance alone (ihlib.HACKCOIN_CREDIT_RATE).
    flags = []
    balance, hours, pending = ihlib.credit_runway(cap)
    if hours > 0:
        names = "; ".join(f"{n} ({c / 1e9:.1f}B cr + {hc} hc)"
                          for n, c, hc in pending if c)
        flags.append(("CREDITS", f"{balance / 1e9:.1f}B of credit-equivalent "
                                 f"budget does not cover the remaining "
                                 f"installs — {names}. At "
                                 f"~{ihlib.CREDITS_PER_HOUR / 1e6:.0f}M/hr "
                                 f"fight income that is {hours:,.0f}h of "
                                 f"banking"))
    # The hackcoin half of an install dwarfs its credit half at the current
    # exchange rate, so the gate to watch is hackcoin, not the credit balance.
    free_hc = (cap["state"].get("currentPlayer") or {}).get("hackcoin") or 0
    need_hc = sum(hc for _, _, hc in pending)
    if need_hc and free_hc < need_hc:
        flags.append(("RESERVE", f"{free_hc} hackcoin vs {need_hc} needed for "
                                 f"the remaining installs — hackcoin is the "
                                 f"binding currency, not credits"))
    return flags


def _audit_zones(cap, ctx):
    # Death streaks are only comparable within one zone: a zone's level_offset
    # shifts enemy level at equal streak (mechanics.md 15), so a baseline that
    # spans a zone change is measuring the move, not the gear.
    deaths = cap["state"].get("recentLossStreaks") or []
    zones = {d.get("zone_name") for d in deaths if d.get("zone_name")}
    if len(zones) <= 1:
        return []
    return [("ZONES", f"the recent death window spans {len(zones)} zones "
                      f"({', '.join(sorted(zones))}) — segment any "
                      f"baseline at the zone change before comparing")]


def _audit_unequipped(cap, ctx):
    flags = []
    equipped = {slot: item for where, slot, item in ihlib.iter_items(cap)
                if where == "equipped"}
    for where, slot, item in ihlib.iter_items(cap):
        if where != "inventory" or slot not in equipped:
            continue
        mine = ihlib.weighted_score(ihlib.item_stat_totals(item))
        theirs = ihlib.weighted_score(ihlib.item_stat_totals(equipped[slot]))
        if mine > theirs + ihlib.UPGRADE_BAND and not item.get("stability"):
            flags.append(("UNEQUIPPED", f"{slot}: {item.get('name')} scores "
                                        f"{mine:.1f} vs equipped {theirs:.1f} and "
                                        f"has 0 Stability (finished) — equip it"))
    return flags


def cmd_locks(args):
    """Daily lock/unlock actions, grouped BY SLOT so the panel is one pass.

    Ordered by `ihlib.SLOT_ORDER` (the game's own inventory order) with LOCK
    and UNLOCK interleaved per slot, at the player's request 7 Aug 2026: a
    list split into a lock block and an unlock block means walking the
    inventory twice. Every line carries the item's CURRENT flag, so the list
    is self-verifying against the panel rather than something to take on
    trust -- and the header states the capture's age, because these actions
    are a snapshot and a half-worked list looks like a wrong one.
    """
    cap, path = ihlib.load_capture(args.file)
    # This command's recommended action is IRREVERSIBLE, so it is the last
    # place a known-wrong constant may render clean (it was the only weight-
    # consuming command missing this banner).
    for _line in ihlib.pending_refit_banner():
        print("  " + _line)
    actions = ihlib.lock_actions(cap, floor=args.floor)
    age = ihlib.capture_age_minutes(cap)
    stamp = f"  (capture {age:.0f} min old)" if age is not None else ""
    print(f"# {path.name}{stamp}")
    print("# Operating model: anything NOT locked is decompiled and lost.")
    print("# Value = the WEAKER of raw Δ and Δ-ex-suspect, so no verdict here")
    print("# rests on a flagged weight. Items already correct are omitted.")
    used, cap_slots, free, price = (actions["inventory_used"],
                                    actions["inventory_cap"],
                                    actions["inventory_free"],
                                    actions["slot_price_hc"])
    if cap_slots:
        cost = f", and a slot costs {price} hackcoin" if price else ""
        print(f"# Holding is NOT free: inventory {used}/{cap_slots} "
              f"({free} free){cost}.")
    # The old header quoted the ~0.92/day keeper arrival rate as the reason
    # for the depth. That rate is real and was the WRONG quantity: it counts
    # every band-clearing base as interchangeable, and top-decile bases
    # arrive ~7x less often (see KEEP_DEPTH_PER_SLOT). Restating a refuted
    # justification in prose is how it survives a fix.
    n = actions["per_slot"]
    print(f"# Depth: keeping the best {n} base{'s' if n != 1 else ''} per "
          f"slot — sized on how long a base of EQUAL QUALITY takes to "
          f"replace\n#         (top-decile ~6.8 days in the measured slot), "
          f"not on the ~0.92/day rate at which\n#         any band-clearing "
          f"base arrives. Anything held beyond that depth is listed AT RISK.")
    print("# 'now' is the item's CURRENT flag in this capture — if it already "
          "reads\n#         the target state you have done it; take a fresh "
          "capture to re-check.")

    by_slot = {}
    for row in actions["lock"]:
        by_slot.setdefault(row["slot"], []).append(("LOCK", row))
    for row in actions["unlock"]:
        by_slot.setdefault(row["slot"], []).append(("UNLOCK", row))
    for row in actions.get("contested") or []:
        by_slot.setdefault(row["slot"], []).append(("KEEP?", row))
    held = {n.lower() for n in actions["protected"]}
    held_rows = [(s, i) for _w, s, i in ihlib.iter_items(cap)
                 if (i.get("name") or "").lower() in held]
    for slot, item in held_rows:
        by_slot.setdefault(slot, []).append(("HELD", {
            "name": item.get("name"), "slot": slot, "worth": None,
            "stability": item.get("stability") or 0,
            "item_level": item.get("item_level") or 0,
            "reason": "revert path for the live A/B gate — do not unlock"}))
    # Instruments are held indefinitely and score as junk, so without a line
    # here the list silently keeps a -70.9 item locked forever and invites the
    # player to release it by hand. Only ALREADY-LOCKED ones: an unlocked arm
    # is a LOCK action above, and printing both is the double-heading defect.
    for name, hold in (actions.get("probe_holds") or {}).items():
        lever, probe = hold["lever"], hold["probe"]
        # A named replication arm carries no purity row -- it is held because
        # the earlier block ran on this exact item. Look its slot and lock
        # flag up directly rather than off a lever that is not there.
        slot, locked = ((lever["slot"], lever["locked"]) if lever
                        else _probe_item_slot_lock(cap, name))
        if not locked:
            continue
        why = (f"Purity {lever['purity']:.1f} ({lever['move']:+.1f} "
               f"{probe['family']} vs {lever['other']:+.1f} signed other, "
               f"{lever['other_abs']:.1f} abs)" if lever else
               "Named arm: the earlier block ran on this exact item, so a "
               "better-ranked substitute would answer a different question")
        by_slot.setdefault(slot, []).append(("HELD", {
            "name": name, "slot": slot, "worth": None,
            "stability": 0, "item_level": 0,
            "reason": f"RESERVED {probe['family']} probe arm — held as an "
                      f"INSTRUMENT, not a craft base, so its craft score is "
                      f"not why it is kept. {why}. Releases when: "
                      f"{probe['unblock']}"}))

    def _print_at_risk():
        """What the depth cap is about to lose, stated rather than implied."""
        risk = actions.get("at_risk") or []
        if not risk:
            return
        # Framing must MATCH the unlock lines above, which release
        # cap-surplus bases with "clears the band but is only #N in slot".
        # Saying "lock any you want kept" here while telling the player to
        # decompile an identically-ranked locked base is one verdict with two
        # opposite recommendations, decided by a flag rather than by value
        # (7 Aug 2026 review). Same verdict; the only difference is that a
        # locked one needs a click and an unlocked one does not.
        print(f"\n  AT RISK — {len(risk)} band-clearing base(s) sit outside "
              f"the depth cap ({actions['per_slot']}/slot) and are already "
              f"UNLOCKED, so the next sweep deletes them without appearing "
              f"in the list above.")
        print("  Same verdict as the UNLOCK lines: the cap releases these. "
              "Listed only so the loss is\n  visible rather than silent — "
              "re-lock one if you disagree with the cap.")
        for r in risk:
            print(f"    {r['name']:44s} keep {r['keep_worth']:+6.1f}  "
                  f"raw {r['raw']:+6.1f}   #{r['slot_rank']} in {r['slot']}")

    if not by_slot:
        print("\n  no lock changes needed — every flag matches its value")
        _print_at_risk()
        return
    n_lock, n_unlock = len(actions["lock"]), len(actions["unlock"])
    n_cont = len(actions.get("contested") or [])
    # "no action" is only true of contested items that are ALREADY locked;
    # unlocked ones are a LOCK action and are counted in n_lock above.
    extra = (f", {n_cont} CONTESTED and already locked (no action — the two "
             f"readings disagree, so they stay as they are)" if n_cont else "")
    print(f"\n  {n_lock} to LOCK, {n_unlock} to UNLOCK+decompile{extra}, "
          f"in inventory slot order:")
    for slot in ihlib.SLOT_ORDER:
        display = ihlib.SLOT_DISPLAY.get(slot, slot)
        rows = by_slot.get(display)
        if not rows:
            continue
        order = {"LOCK": 0, "HELD": 1, "KEEP?": 2, "UNLOCK": 3}
        rows.sort(key=lambda r: (order[r[0]],
                                 -(r[1]["worth"] if r[1]["worth"] is not None
                                   else 0)))
        print(f"\n  ── {display} " + "─" * max(1, 40 - len(display)))
        for action, r in rows:
            now = "locked" if r.get("locked", True) else "unlocked"
            worth = f"{r['worth']:+6.1f}" if r["worth"] is not None else "  hold"
            print(f"    {action:6s} {r['name']:44s} {worth}  "
                  f"(now: {now})")
            print(f"           {r['reason']}")
    _print_at_risk()


def _audit_inventory_capacity(cap, ctx):
    """Inventory space is bought with HACKCOIN — the scarcest currency.

    Added 7 Aug 2026: the first lock sweep recommended holding 13 craft bases
    without checking that inventory was 94/102 and that a slot costs 10
    hackcoin (~83B credit-equivalents). Never recommend a hold without its
    denominator — the standing rule, missed on exactly the resource it is
    written about.
    """
    used, cap_slots, free, price = ihlib.inventory_pressure(cap)
    if not cap_slots:
        return []
    if free is not None and free <= 10:
        cost = (f"; a slot costs {price} hackcoin "
                f"(~{price * ihlib.HACKCOIN_CREDIT_RATE / 1e9:,.0f}B "
                f"credit-equivalents)" if price else "")
        # max_slots is SOFT -- seven 5 Aug captures held 103 against a max of
        # 102 -- so this is spending pressure, not a wall. Said plainly here
        # because the first version called it a hard cap in a player advisory.
        return [("INVENTORY", f"inventory {used}/{cap_slots} ({free} nominal "
                              f"slot(s) free){cost}. NOTE max_slots is soft — "
                              f"the archive has held 103/102 — so this is "
                              f"pressure, not a hard wall. `ih.py locks` "
                              f"lists what to clear")]
    return []


def _audit_decompile_locks(cap, ctx):
    """`decompile_locked` vs actual craft value — a field nobody had ever read.

    Added 7 Aug 2026 after the player asked what to decompile: the item schema
    carries `decompile_locked`, 18 inventory items were locked, and the lock
    set was almost exactly INVERTED against value — 17 of the 18 were
    low-value while 13 band-clearing craft bases sat unlocked. The locks had
    been set by hand over weeks and never revisited, so they encoded old
    verdicts (mostly Corruption-carried Analyzers and Kernels) that the
    re-fitted weights have since demoted. Both directions cost progress: a
    stale lock protects junk and a missing one puts a real base one click from
    deletion.

    DELEGATES to `ihlib.lock_actions` rather than re-deriving the rule. The
    first version duplicated the logic inline and immediately disagreed with
    `ih.py locks` (13 holds vs 6) once the per-slot depth cap landed — the
    same two-panels-drift bug as the homelab ETA, reintroduced within hours of
    fixing it. One implementation, two callers.
    """
    actions = ihlib.lock_actions(cap)
    flags = []
    if actions["unlock"]:
        rows = actions["unlock"]
        flags.append(("LOCKS", f"{len(rows)} decompile-locked item(s) are safe "
                               f"to discard (NEITHER reading defends them, or "
                               f"they are out-ranked in slot) — unlock and "
                               f"decompile: "
                      + "; ".join(f"{r['name']} [{r['slot']}] {r['worth']:+.1f}"
                                  for r in rows[:6])
                      + (f"; +{len(rows) - 6} more — ih.py locks"
                         if len(rows) > 6 else "")))
    if actions["lock"]:
        rows = actions["lock"]
        flags.append(("LOCKS", f"{len(rows)} band-clearing craft base(s) are "
                               f"UNLOCKED and one click from deletion — lock: "
                      + "; ".join(f"{r['name']} [{r['slot']}] {r['worth']:+.1f}"
                                  for r in rows[:6])
                      + (f"; +{len(rows) - 6} more — ih.py locks"
                         if len(rows) > 6 else "")))
    # Contested items are a THIRD outcome and must be reported, not silently
    # omitted. A sweep listing only actionable rows reads as "everything else
    # is fine", when in fact these hold inventory indefinitely while a flagged
    # weight goes unresolved -- which makes the holding cost attributable to a
    # specific missing measurement rather than looking like clutter.
    if actions.get("contested"):
        rows = actions["contested"]
        flags.append(("LOCKS", f"{len(rows)} item(s) are CONTESTED — raw and "
                               f"ex-suspect disagree, so they stay locked and "
                               f"no decompile is advised. They hold inventory "
                               f"until the flagged family is measured (see "
                               f"SUSPECT_WEIGHTS — and note PROBE-GONE above "
                               f"if no instrument for it is owned): "
                      + "; ".join(f"{r['name']} [{r['slot']}] raw "
                                  f"{r['raw']:+.1f} / ex {r['ex_suspect']:+.1f}"
                                  for r in rows[:4])
                      + (f"; +{len(rows) - 4} more — ih.py locks"
                         if len(rows) > 4 else "")))
    return flags


def _probe_item_slot_lock(cap, name):
    """(slot, locked) for a named probe arm, straight off the capture."""
    for _where, slot, item in ihlib.iter_items(cap):
        if (item.get("name") or "").lower() == name.lower():
            return slot, bool(item.get("decompile_locked"))
    return "?", False


def _probe_item_locked(cap, name):
    return _probe_item_slot_lock(cap, name)[1]


def _audit_reserved_probes(cap, ctx):
    """Are the instruments for the open measurements still owned, and held?

    Added 9 Aug 2026, after the reservation that lived as prose in
    docs/candidate-status.md silently emptied out. Five items were named there
    as reserved CI/CD probe arms; by 9 Aug every one was gone, including the
    MaxHP pair -- and MaxHP is still the largest ASSERTED term in the model,
    still waiting on the block those arms existed to run. Nothing flagged it,
    because nothing in the code had ever read that sentence.

    Two distinct findings, and they need separate wording because the loss is
    at a different stage:
      MISSING   -- no owned lever for an open question. The measurement cannot
                   be run today at any price; it waits on a drop.
      UNLOCKED  -- a lever exists and is one sweep from deletion. This is the
                   state the previous five passed through unremarked.

    Reported ABOVE the ordinary lock flags: an instrument is not replaceable
    from the same slot the way a craft base is, so losing one costs a
    measurement rather than a few score points.
    """
    flags = []
    holds = ihlib.reserved_probe_holds(cap)
    for probe in ihlib.reserved_probes():
        family = probe["family"]
        if probe.get("items"):
            # A replication reservation is judged on ITS OWN arms, not on
            # whatever ranks best today. Ranking them would report a healthy
            # instrument while the two items the earlier block actually ran
            # on were being decompiled.
            owned = {name: hold for name, hold in holds.items()
                     if hold["probe"] is probe}
            gone = [n for n in probe["items"]
                    if n.lower() not in {o.lower() for o in owned}]
            if gone:
                flags.append((
                    "PROBE-GONE",
                    f"{family} replication arm(s) NO LONGER OWNED: "
                    f"{'; '.join(gone)} — the earlier block ran on those exact "
                    f"items, so this measurement can no longer be replicated "
                    f"and must be re-fitted from scratch. Why it is held: "
                    f"{probe['reason']}. Needs: {probe['unblock']}"))
            loose = [n for n, _h in owned.items()
                     if not _probe_item_locked(cap, n)]
            if loose:
                flags.append((
                    "PROBE-LOOSE",
                    f"{len(loose)} reserved {family} replication arm(s) are "
                    f"UNLOCKED and one sweep from deletion — lock: "
                    + "; ".join(loose)
                    + f". Needs: {probe['unblock']}"))
            continue
        levers = ihlib.probe_levers(cap, family, top=probe.get("arms", 1))
        if not levers:
            flags.append((
                "PROBE-GONE",
                f"{family} probe reserved but NO owned item moves it purely "
                f"enough to serve as an arm — the measurement cannot run "
                f"until a lever drops. Why it is held: {probe['reason']}. "
                f"Needs: {probe['unblock']}"))
            continue
        loose = [r for r in levers if not r["locked"]]
        if loose:
            flags.append((
                "PROBE-LOOSE",
                f"{len(loose)} reserved {family} probe arm(s) are UNLOCKED "
                f"and one sweep from deletion — lock: "
                + "; ".join(f"{r['name']} [{r['slot']}] purity {r['purity']:.1f}"
                            f" ({r['move']:+.1f} {family} vs {r['other']:+.1f}"
                            f" signed other)" for r in loose)
                + f". Held as instruments, not craft bases — {probe['unblock']}"))
    return flags


AUDIT_CHECKS = [
    _audit_pending_refits,
    _audit_reserved_probes,
    _audit_inventory_capacity,
    _audit_decompile_locks,
    _audit_stream_drift,
    _audit_stale_panels,
    _audit_capture_integrity,
    _audit_sim_ledger,
    _audit_stat_model,
    _audit_hardware,
    _audit_homelab,
    _audit_contracts,
    _audit_install_budget,
    _audit_zones,
    _audit_unequipped,
]


def run_audit(cap):
    """Run every registered check; returns [(KIND, message)] in display order.

    A check that raises is REPORTED, not propagated: on 7 Aug 2026
    `_audit_inventory_capacity` died on a bad call and took the entire sweep
    with it -- losing the KNOWN-WRONG banner, the staleness flags and every
    unrelated check -- and `_audit_decompile_locks` could do the same whenever
    an experiment omits `revert_item`. The sweep exists to surface problems,
    so it must degrade to "this check is broken" rather than to silence.
    """
    flags, ctx = [], {}
    for check in AUDIT_CHECKS:
        try:
            flags.extend(check(cap, ctx))
        except Exception as exc:            # noqa: BLE001 - reported, not raised
            flags.append(("CHECK-BROKEN",
                          f"audit check {check.__name__} failed: "
                          f"{type(exc).__name__}: {exc} — the other checks "
                          f"still ran, but this one is blind until fixed"))
    return flags


def cmd_audit(args):
    """Anomaly sweep: things that are silently costing progress right now.

    Every check here exists because a real one was missed. 27 Jul 2026: four
    homelab build slots idle for 3.5 days; 81K chips on two hardware tracks
    whose multiplicand was zero; a finished craft sitting unequipped; a
    homelabInfo panel 1,348s stale. Run before optimizing anything.
    """
    cap, path = ihlib.load_capture(args.file)
    print(f"# {path.name}")
    flags = run_audit(cap)
    if not flags:
        print("  no anomalies")
        return
    width = max(len(k) for k, _ in flags)
    for kind, message in flags:
        print(f"  [{kind:<{width}}] {message}")


def cmd_calibration(args):
    """Score the prediction ledger: is the planner biased, are its intervals honest?"""
    if args.record:
        row = ihlib.record_prediction(
            item=args.record, slot=args.slot or "?", projected=args.projected,
            realized=args.realized, p10=args.p10, p90=args.p90,
            p_upgrade=args.p_upgrade, date=args.date, note=args.note or "")
        print(f"recorded: {row}")
        return
    eras = ihlib.calibration()
    if not eras:
        sys.exit("no graded predictions in data/predictions.jsonl")
    print("# realized-vs-projected, per planner era. Eras are NOT comparable:")
    print("# removing the T3 cap and lowering COMPILE_FLOOR each moved "
          "projections by more\n# than UPGRADE_BAND, so only the newest era "
          "describes what the tool does today.\n")
    for name, era in eras.items():
        current = "  <-- current" if name == ihlib.CURRENT_MODEL else ""
        print(f"== {name} (n={era['n']}){current}")
        for item, proj, real, err in era["items"]:
            print(f"     {item:<38} projected {proj:+6.1f}  realized "
                  f"{real:+6.1f}  error {err:+6.1f}")
        print(f"     bias {era['bias']:+.1f}   MAE {era['mae']:.1f}   "
              f"over-realized {era['over']}/{era['n']}   "
              f"verdict held {era['agree']}/{era['graded']}")
        if era["with_interval"]:
            print(f"     p10-p90 coverage {era['in_interval']}/"
                  f"{era['with_interval']} (want ~80%)")
        else:
            print("     p10-p90 coverage: no distributions recorded — "
                  "point estimates only")
        print()
    total = sum(e["n"] for e in eras.values())
    over = sum(e["over"] for e in eras.values())
    print(f"  {over}/{total} crafts realized ABOVE projection. The standing "
          f"'~5-point contract-\n  conservatism discount' subtracts from "
          f"projections — check the sign of the bias\n  in the current era "
          f"before applying it. Record every approved craft with\n  "
          f"`ih.py calibration --record` at contract time, then fill "
          f"--realized after.")
    if ihlib.CURRENT_MODEL not in eras:
        print(f"\n  NOTE: zero graded crafts under the current planner "
              f"({ihlib.CURRENT_MODEL}).\n  Every number above describes a "
              f"model that no longer exists. Treat the next two\n  crafts as "
              f"calibration runs and record their full distributions.")


def cmd_assumptions(args):
    """Provenance register for every tunable constant, most-suspect first.

    Exists because every defect found in this workspace has been an inherited
    number that looked reasonable in output: the T3 tier cap, the zone
    transition cost, "attack speed -> fights per hour", Corrupt = 0.6,
    "credits are unlimited", floor = 8. The standing lesson kept being written
    as prose to remember. This runs instead.
    """
    cap, path = ihlib.load_capture(args.file)
    print(f"# {path.name}")
    print("# provenance register — 'asserted' and 'inherited' are guesses "
          "nobody has tested.")
    print("# Every defect found so far has been one of those. Most-suspect "
          "first.\n")
    rows = ihlib.assumptions()
    if args.provenance:
        rows = [r for r in rows if r[2] == args.provenance]
    counts = {}
    shown = None
    for name, value, provenance, basis, validated, check in rows:
        counts[provenance] = counts.get(provenance, 0) + 1
        if provenance != shown:
            shown = provenance
            print(f"── {provenance.upper()} " + "─" * (54 - len(provenance)))
        value = f"{value:g}" if isinstance(value, float) else str(value)
        print(f"  {name:<30} {value:>12}   "
              f"{'validated ' + validated if validated else 'NEVER VALIDATED'}")
        if basis:
            for line in textwrap.wrap(basis, 74):
                print(f"      {line}")
        if check:
            try:
                status, detail = check(cap)
            except Exception as exc:                 # a broken check is a finding
                status, detail = "ERROR", f"{type(exc).__name__}: {exc}"
            print(f"      [{status}] {detail}")
    print("\n  " + "  ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    untested = counts.get("asserted", 0) + counts.get("inherited", 0)
    if untested:
        print(f"  {untested} constant(s) have never been tested against game "
              f"data. Before any\n  verdict rests on one, exercise it at both "
              f"ends of its range — `ih.py contract\n  --floor` sweeps are "
              f"cheap, and the archive usually holds natural variation.")


def cmd_ab(args):
    status = ihlib.experiment_status()
    if status is None:
        concluded = [v for v in vars(ihlib).values()
                     if isinstance(v, dict) and v.get("concluded")]
        last = concluded[-1] if concluded else {}
        print("no active experiment"
              + (f" (last: {last.get('name')} — {last.get('concluded')})"
                 if last else ""))
        return
    exp = status["experiment"]
    pre = status["pre_recent_streaks"] or status["pre_death_streaks"]
    pre_all = status["pre_death_streaks"]
    post = status["post_death_streaks"]
    ph, pm = status["post_hits"]
    # A declaration missing `baseline_hits` used to raise KeyError here and
    # take the whole readout with it -- the gate, the mechanism table and the
    # contamination checks -- for a field that only feeds ONE contamination
    # line. Same lesson as `run_audit`: a sweep exists to surface problems, so
    # it must degrade to "this check is blind" rather than to a traceback.
    bh, bm = exp.get("baseline_hits") or (0, 0)
    pre_mean = sum(pre) / len(pre) if pre else 0
    post_mean = sum(post) / len(post) if post else 0
    base_hit = bh / (bh + bm) * 100 if bh + bm else None
    post_hit = ph / (ph + pm) * 100 if ph + pm else None
    n, target = len(post), exp["target_deaths"]
    if args.brief:
        depth = (f"deaths {n}/{target}: mean {post_mean:.1f} vs {pre_mean:.1f} "
                 f"({post_mean - pre_mean:+.1f})" if post else
                 f"deaths 0/{target}")
        if post_hit is None:
            hit = "hit-rate: NO round data — enable Detailed Logs (Hacking panel)!"
        elif base_hit is None:
            hit = (f"hit {post_hit:.1f}% (n={ph + pm}) vs NO baseline — the "
                   f"declaration omits `baseline_hits`")
        else:
            hit = (f"hit {post_hit:.1f}% (n={ph + pm}) vs baseline "
                   f"{base_hit:.1f}%")
        detail = (f"{status['detailed_fight_count']}/{status['post_fight_count']}"
                  " fights have round detail")
        print(f"A/B {exp['item']}")
        print(depth + " | " + hit)
        # Same experiment-supplied label as the full readout below. This
        # printer kept the hardcoded "post-VLAN" through the first pass of
        # the fix -- one defect, two printers, and only one was corrected.
        seg_label = exp.get("segment_label") or "the declared"
        print(detail + (f" | {status['deaths_after_segment']} deaths after "
                        f"{seg_label} boundary" if status["deaths_after_segment"]
                        else ""))
        if n >= target:
            print("TARGET REACHED — run the keep/revert decision")
        return
    print(f"# A/B: {exp['name']} — {exp['item']} [{exp['slot']}]")
    print(f"  keep rule: {exp['keep_rule']}")
    print(f"  pre-equip deaths, same-loadout window ({len(pre)}): {pre}  "
          f"mean {pre_mean:.1f}")
    if len(pre_all) > len(pre):
        all_mean = sum(pre_all) / len(pre_all)
        print(f"  (wider context: {len(pre_all)} deaths across older loadouts, "
              f"mean {all_mean:.1f})")
    print(f"  post-equip deaths ({n}/{target}): {post}  mean {post_mean:.1f}"
          f"  delta {post_mean - pre_mean:+.1f}")
    straddle = status.get("straddler_streaks") or []
    if straddle:
        # DISCLOSED, never substituted. The declared metric is every
        # post-equip death and it stays that way -- re-specifying a
        # pre-registered rule after seeing the numbers is the one thing
        # CLAUDE.md rules out flatly, and here the change would flatter
        # the result. Both readings are printed so the reader can see
        # whether the verdict depends on the difference.
        clean = status.get("post_death_streaks_clean") or []
        clean_mean = sum(clean) / len(clean) if clean else 0.0
        print(f"  ({len(straddle)} of those streak(s) BEGAN before the "
              f"equip and were fought on the old item: {straddle}. "
              f"Excluding them reads {clean_mean:.1f} "
              f"({clean_mean - pre_mean:+.1f}) over {len(clean)} — this "
              f"is NOT the declared metric, it is the size of a known "
              f"bias toward the pre-equip level)")
    if status["deaths_after_segment"]:
        # Label comes from the experiment's own declaration. It was hardcoded
        # to "VLAN +1% Def" -- one July experiment's boundary -- so every
        # later segmented window would have been mislabelled with it.
        label = status["experiment"].get("segment_label") or "the declared"
        print(f"  ({status['deaths_after_segment']} of them after {label} "
              f"segment boundary — analyse separately)")
    if post_hit is not None and base_hit is not None:
        print(f"  hit rate: {post_hit:.1f}% ({ph}h/{pm}m) vs same-loadout "
              f"baseline {base_hit:.1f}% ({bh}h/{bm}m)")
    elif post_hit is not None:
        print(f"  hit rate: {post_hit:.1f}% ({ph}h/{pm}m) — NO baseline, the "
              f"declaration omits `baseline_hits`, so this is uncheckable")
    else:
        print("  hit rate: no post-equip round data — enable Detailed Logs "
              "in the Hacking panel")
    print(f"  fight coverage: {status['post_fight_count']} post-equip fights "
          f"banked, {status['detailed_fight_count']} with round detail")
    mech = ihlib.experiment_mechanism(status)
    if any(g["brackets"] for g in mech.values()):
        print("\n  mechanism (victorious detailed fights; net = gross damage "
              "- in-fight prg - barrier absorption, directional):")
        for lo, hi in ihlib.MECH_BRACKETS:
            parts = []
            for era in ("pre", "post", "post-seg"):
                b = mech[era]["brackets"].get((lo, hi))
                if b:
                    # hit rate is printed PER BRACKET on purpose: enemy
                    # evasion scales with streak, so a pooled pre/post hit
                    # rate compares streak composition, not accuracy
                    hit = (f" hit {b['hit']*100:.1f}%" if b.get("hit")
                           is not None else "")
                    parts.append(f"{era} n={b['n']} gross {b['gross']:.0f} "
                                 f"net {b['net']:.0f} rnds {b['rounds']:.1f}"
                                 f"{hit}")
            if parts:
                print(f"    streak {lo}-{hi}:  " + "  |  ".join(parts))
        onset_parts = [f"{era} {mech[era]['onsets']}"
                       for era in ("pre", "post", "post-seg")
                       if mech[era]["onsets"]]
        if onset_parts:
            print("    attrition onset (first start-HP <90%, streak >10): "
                  + "  |  ".join(onset_parts))
        prg_parts = [f"{era} {mech[era]['prg_per_round']:.1f}"
                     for era in ("pre", "post", "post-seg")
                     if mech[era]["prg_per_round"]]
        if prg_parts:
            print("    realized regen/round, streak >=60: "
                  + "  |  ".join(prg_parts))


def _section_output(argv):
    """Run one subcommand in-process and return its stdout."""
    args = build_parser().parse_args(argv)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            args.fn(args)
    except (SystemExit, FileNotFoundError, ValueError) as e:
        # a missing panel or empty ledger must not kill the digest
        buf.write(f"  [unavailable: {e}]\n")
    return buf.getvalue()


def _is_refit_banner(line):
    """True for any line of the PENDING_REFITS warning block.

    The banner is multi-line (header, one row per refit, blocked_on, unblock)
    and every line must survive digest filtering — a half-printed warning is
    worse than none, because it looks like a formatting artefact.
    """
    probe = line.lstrip("# ").strip().lower()
    return (probe.startswith("!!")
            or probe.startswith("blocked on:")
            or probe.startswith("unblock by:")
            or "known-wrong" in probe
            or "applied " in probe and "since " in probe)


def _brief_potential(text):
    """Best band-clearing candidate per slot, verdict-bearing lines only.

    Candidates print best-first, so the digest keeps the first UPGRADE block
    per slot (its ceiling / from: / !! / low: lines — the parts a verdict
    reads) and counts everything else, saying how many of the suppressed also
    clear the band. Unrecognized top-level lines are KEPT — a printer format
    change degrades to verbosity, never to silent loss.
    """
    out, slot, keep, kept_one = [], None, True, False
    below = {}
    more_up = {}

    def note():
        if not slot:
            return
        parts = []
        if more_up.get(slot):
            parts.append(f"{more_up[slot]} further band-clearing")
        if below.get(slot):
            parts.append(f"{below[slot]} below-band")
        if parts:
            out.append(f"  ({' + '.join(parts)} candidate(s) suppressed — "
                       f"ih.py potential --slot {slot.lower()})")

    for line in text.splitlines():
        stripped = line.strip()
        if line.startswith("== "):
            note()
            slot, keep, kept_one = line.strip("= ").strip(), True, False
            out.append(line)
        elif line.startswith("# "):
            # capture name and the KNOWN-WRONG banner survive; static
            # boilerplate does not. The banner was being stripped here, which
            # let craft ceilings computed from a known-wrong constant render
            # clean in the digest that drives the advisory.
            if "idle-hacking" in line or _is_refit_banner(line):
                out.append(line)
        elif stripped.startswith(("ceiling", "~ceiling")):
            if "UPGRADE" in line and not kept_one:
                keep, kept_one = True, True
                out.append(line)
            else:
                key = more_up if "UPGRADE" in line else below
                key[slot] = key.get(slot, 0) + 1
                keep = False
        elif stripped.startswith("equipped"):
            keep = True
            out.append(line)
        elif keep and stripped.startswith(("plan:", "proj:", "econ")):
            continue                     # contract-time detail, not triage
        elif keep:
            out.append(line)
    note()
    return "\n".join(out)


def _brief_assumptions(text):
    """Keep asserted/supplied rows and DRIFTing measured rows; count the rest."""
    out, block, in_measured, ok_rows = [], [], False, 0

    def flush():
        nonlocal ok_rows
        if not block:
            return
        if not in_measured or "[DRIFT" in "\n".join(block):
            out.extend(block)
        else:
            ok_rows += 1
        block.clear()

    for line in text.splitlines():
        if line.startswith("── "):
            flush()
            in_measured = "MEASURED" in line
            out.append(line)
        elif not line.strip():
            flush()
            out.append(line)
        elif (line.startswith("  ") and len(line) > 2 and line[2] != " "
              and "VALIDATED" in line.upper()):
            flush()
            block.append(line)
        elif block:
            block.append(line)
        else:
            out.append(line)
    flush()
    if ok_rows:
        out.append(f"  ({ok_rows} measured row(s) with no drift suppressed "
                   f"— ih.py assumptions for the full register)")
    return "\n".join(out)


def _brief_calibration(text):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "<-- current" in line:
            return "\n".join(
                ["  (earlier planner eras suppressed — ih.py calibration)"]
                + lines[i:])
    return text


def _brief_homelab(text):
    out, dropping = [], False
    for line in text.splitlines():
        head = line.lstrip()
        if head.startswith("purchasable now"):
            dropping = True
            out.append("  (purchasable list suppressed — ih.py homelab)")
            continue
        if head.startswith("unlocks at level"):
            dropping = False
        if not dropping:
            out.append(line)
    return "\n".join(out)


def _brief_hardware(text):
    out, in_tracks, kept, dropped = [], False, 0, 0
    rebuys = 0
    for line in text.splitlines():
        # The re-buy schedule is a do-list, not a verdict: the RESET headline
        # above it carries the decision, so keep the three largest and count
        # the rest rather than spending 10 digest lines on chip amounts.
        if line.lstrip().startswith("re-buy "):
            rebuys += 1
            if rebuys > 3:
                if rebuys == 4:
                    out.append("    (further re-buy lines suppressed "
                               "— ih.py hardware)")
                continue
        if "combat tracks by value" in line:
            in_tracks = True
            out.append(line)
        elif in_tracks and line.startswith("  economy/farming"):
            out.append(f"  ({dropped} lower-value combat track(s) and the "
                       f"economy tracks suppressed — ih.py hardware)")
            break
        elif in_tracks and line.strip().startswith("!!"):
            # a track's depth-suspect note belongs to the row ABOVE it and is
            # not a track of its own -- counting it as one silently dropped a
            # real track and skewed the suppressed count
            if kept and kept <= 3:
                out.append(line)
        elif in_tracks and line.startswith("    ") and line.strip():
            if kept < 3:
                out.append(line)
                kept += 1
            else:
                dropped += 1
        else:
            out.append(line)
    return "\n".join(out)


def _brief_ab(text):
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("keep rule:"):
            head = line.split("Contamination")[0].rstrip()
            out.append(head + " (full rule + pre-registered predictions: "
                              "ih.py ab)")
        elif "deaths" in line and "[" in line and "pre-equip" in line:
            out.append(re.sub(r"\[.*?\]", "[…]", line))
        elif line.lstrip().startswith("attrition onset"):
            out.append(re.sub(r"\[.*?\]", "[…]", line, count=1))
        elif line.lstrip().startswith("(wider context"):
            continue
        else:
            out.append(line)
    return "\n".join(out)


def _brief_diff(text):
    lines = text.splitlines()
    if len(lines) > 21:
        lines = lines[:21] + [f"  (+{len(lines) - 21} more changes "
                              f"— ih.py diff)"]
    return "\n".join(lines)


def cmd_brief(args):
    """One-process advisory digest: the whole gather, compressed for triage.

    Motivated 31 Jul 2026: the mandated advisory gather was ~10 separate
    commands emitting ~72KB, of which the verdict-bearing content was a
    fraction. This digest suppresses only what it can COUNT (and says so
    inline), keeps every audit flag verbatim, and defaults to keeping lines
    its filters do not recognize. It is a triage layer: anything flagged,
    close, or surprising gets the full command — never conclude from a
    thing's absence in this output.
    """
    # Pin the capture ONCE and pass it to every section that reads one. The
    # hub routes captures asynchronously: on 6 Aug 2026 a capture landed
    # mid-digest and the audit section ran on the previous file while stats
    # ran on the new one — a torn read that printed already-resolved STALE
    # flags with no indication the sections disagreed.
    paths = ihlib.capture_paths()
    latest = paths[-1] if paths else None
    prev = paths[-2] if len(paths) > 1 else None
    print("# ih.py brief — triage digest. Full commands remain canonical; "
          "drill into anything flagged or close.")
    if latest:
        m = re.search(r"(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})",
                      latest.name)
        if m:
            ts = datetime.fromisoformat(
                f"{m.group(1)}T{m.group(2)}:{m.group(3)}:{m.group(4)}+00:00")
            age_h = (time.time() - ts.timestamp()) / 3600
            stale = "  ** capture is stale — ask for a fresh one **" \
                if age_h > 12 else ""
            print(f"# latest capture is {age_h:.1f}h old{stale}")
    pin = ["--file", str(latest)] if latest else []
    sections = [
        ("audit — outranks everything below", ["audit"] + pin, None),
        ("freshness", ["captures"],
         lambda t: "\n".join(t.splitlines()[-1:])),
        ("stats", ["stats"] + pin, None),
        ("assumptions (asserted/supplied/drifting only)",
         ["assumptions"] + pin, _brief_assumptions),
        ("calibration (current era)", ["calibration"], _brief_calibration),
        ("potential (band-clearing candidates only)", ["potential"] + pin,
         _brief_potential),
        ("locks (lock/unlock actions — everything unlocked is decompiled)",
         ["locks"] + pin, None),
        ("homelab", ["homelab"] + pin, _brief_homelab),
        ("hardware (top tracks)", ["hardware"] + pin, _brief_hardware),
        ("ab", ["ab"], _brief_ab),
        ("diff vs previous capture",
         ["diff"] + ([str(prev), str(latest)] if prev else []), _brief_diff),
    ]
    for title, argv, filt in sections:
        text = _section_output(argv)
        if filt:
            text = filt(text)
        print(f"\n───── {title} " + "─" * max(1, 60 - len(title)))
        print(text.rstrip("\n"))


def build_parser():
    parser = argparse.ArgumentParser(prog="ih.py")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("captures",
                       help="list captures and which lazy panels each contains").set_defaults(fn=cmd_captures)

    p = sub.add_parser("loadout",
                       help="the eight equipped items with their affixes and totals")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_loadout)

    p = sub.add_parser("item",
                       help="full detail for one item: affixes, rolls, craft costs")
    p.add_argument("query")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_item)

    p = sub.add_parser("candidates",
                       help="inventory items ranked against what is equipped")
    p.add_argument("--slot")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_candidates)

    p = sub.add_parser("compare",
                       help="two items side by side")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("diff",
                       help="what changed between two captures")
    p.add_argument("old", nargs="?")
    p.add_argument("new", nargs="?")
    p.set_defaults(fn=cmd_diff)

    p = sub.add_parser("stats",
                       help="headline player state: level, currencies, streak, zone")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_stats)

    p = sub.add_parser("history",
                       help="how one item or stat moved across the capture archive")
    p.add_argument("query")
    p.set_defaults(fn=cmd_history)

    p = sub.add_parser("homelab",
                       help="level, running jobs, queue suggestions, purchasable upgrades")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_homelab)

    p = sub.add_parser("hardware",
                       help="chip balance and combat tracks ranked by value per chip")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_hardware)

    p = sub.add_parser("audit",
                       help="anomaly sweep: what is silently costing progress right now")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_audit)

    p = sub.add_parser("locks",
                       help="daily lock/unlock actions (deltas only)")
    p.add_argument("--file")
    p.add_argument("--floor", type=int, default=ihlib.COMPILE_FLOOR)
    p.set_defaults(fn=cmd_locks)

    p = sub.add_parser("ab",
                       help="the live A/B gate: keep rule, deaths banked, mechanism table")
    p.add_argument("--brief", action="store_true")
    p.set_defaults(fn=cmd_ab)

    p = sub.add_parser("contract", help="simulate a craft contract's outcome")
    p.add_argument("item")
    p.add_argument("--phase", action="append", default=[],
                   metavar="'of Haste:4'",
                   help="affix:target_tier, repeatable, in execution order; "
                        "defaults to plan_craft's own plan")
    p.add_argument("--floor", type=int, default=ihlib.COMPILE_FLOOR)
    p.add_argument("--trials", type=int, default=20000)
    p.add_argument("--order", action="store_true",
                   help="search every phase permutation")
    p.add_argument("--file")
    p.add_argument("--deepen", action="store_true",
                   help="also test plans deeper than plan_craft proposes")
    p.add_argument("--ex-suspect", action="store_true",
                   help="price the plan built WITHOUT the flagged families "
                        "instead of plan_craft's raw-optimal one")
    p.set_defaults(fn=cmd_contract)

    p = sub.add_parser("calibration",
                       help="score the prediction ledger (bias, coverage)")
    p.add_argument("--record", metavar="ITEM",
                   help="append a prediction for ITEM")
    p.add_argument("--slot")
    p.add_argument("--projected", type=float)
    p.add_argument("--realized", type=float)
    p.add_argument("--p10", type=float)
    p.add_argument("--p90", type=float)
    p.add_argument("--p-upgrade", dest="p_upgrade", type=float)
    p.add_argument("--date")
    p.add_argument("--note")
    p.set_defaults(fn=cmd_calibration)

    p = sub.add_parser("assumptions",
                       help="provenance register for tunable constants")
    p.add_argument("--provenance", choices=("measured", "asserted",
                                            "inherited", "supplied"),
                   help="show only constants of one provenance")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_assumptions)

    p = sub.add_parser("cadence", help="measured seconds per fight")
    p.set_defaults(fn=cmd_cadence)

    p = sub.add_parser("sims", help="Hacking Simulator runs banked so far")
    p.add_argument("--mode", default="software_profiler",
                   choices=("software_profiler", "cicd_pipeline"))
    p.set_defaults(fn=cmd_sims)

    p = sub.add_parser("potential",
                       help="projected post-craft ceilings per slot (the craft verdict)")
    p.add_argument("--slot")
    p.add_argument("--file")
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--floor", type=int, default=ihlib.COMPILE_FLOOR)
    p.add_argument("--cap", type=int, default=1,
                   help="deepest tier to plan to (default 1 = the game max; "
                        "pass 3 to reproduce pre-27-Jul-2026 projections)")
    p.set_defaults(fn=cmd_potential)

    p = sub.add_parser("brief",
                       help="one-process advisory digest — triage only; the "
                            "full commands remain canonical for drill-down")
    p.set_defaults(fn=cmd_brief)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.fn(args)
    except (FileNotFoundError, ValueError) as error:
        # The library raises real exceptions (never SystemExit — that poisoned
        # importers and pytest); the CLI translates them here, once.
        sys.exit(str(error))


if __name__ == "__main__":
    main()
