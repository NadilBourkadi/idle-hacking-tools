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
  cadence                  measured seconds per fight from the death clock
                           (fixed ~4.87s tick; attack speed is NOT income)

Output is deliberately compact; prefer this over ad-hoc capture parsing.
"""

import argparse
import statistics
import sys

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
    print("  totals:", ihlib.fmt_totals(ihlib.stat_totals(item), combat_only=False))
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
              f"{ihlib.fmt_totals(ihlib.stat_totals(item))}")
    print(f"({len(rows)} items)")


def cmd_compare(args):
    cap, path = ihlib.load_capture(args.file)
    where_a, slot_a, a = resolve_one(cap, args.a)
    where_b, slot_b, b = resolve_one(cap, args.b)
    print(f"# {path.name}")
    print("A:", ihlib.item_header(a, slot_a, where_a))
    print("B:", ihlib.item_header(b, slot_b, where_b))
    ta, tb = ihlib.stat_totals(a), ihlib.stat_totals(b)
    labels = [l for l in ihlib.COMBAT_ORDER if l in ta or l in tb]
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
    print("# These are optimal-plan ceilings; a §10.1 contract with attempt "
          "caps and a hard floor lands ~5 points lower — discount accordingly.")
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
            base = ihlib.weighted_score(ihlib.stat_totals(equipped))
            print(f"  equipped  {equipped.get('name'):<44} score {base:6.1f}  "
                  f"{ihlib.fmt_totals(ihlib.stat_totals(equipped))}")
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
        eq_totals = ihlib.stat_totals(equipped) if equipped else {}
        for score, item, plan in rows[: args.top]:
            delta = score - base
            verdict = ("UPGRADE" if delta > ihlib.UPGRADE_BAND
                       else "inferior" if delta < ihlib.INFERIOR_BAND
                       else "sidegrade")
            marker = "~" if plan["estimated"] else " "
            steps = ", ".join(
                f"{name} T{f}->T{t}{'~' if est else ''}"
                for name, f, t, c, est in plan["steps"])
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
    tick_s = info.get("tick_seconds") or 5
    in_flight_points = 0
    for label, group in (("active jobs", jobs), ("queued jobs", pending)):
        if not group:
            continue
        print(f"\n  {label}:")
        for job in group:
            done = job.get("progress_ticks") or 0
            total = job.get("duration_ticks") or 1
            pts = job.get("progress_points") or 0
            in_flight_points += pts
            eta = f"{(total - done) * tick_s / 60:.0f}min"
            when = f"{done / total * 100:3.0f}%  ~{eta}" if group is jobs \
                else f"     {eta} once started"
            print(f"    {names.get(job.get('target'), job.get('target')):28s} "
                  f"-> L{job.get('target_level')}  {when}  +{pts}pts  "
                  f"[{ihlib.fmt_cost(job.get('cost_snapshot'))}]")
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
    tick_s = info.get("tick_seconds") or 5
    free = (info.get("max_build_slots") or 0) - len(jobs)
    room = (info.get("max_queue_jobs") or 0) - len(pending)
    if free or room:
        picks = ihlib.homelab_fill_suggestions(cap, limit=free + room)
        print(f"\n  FILL NOW ({free} slot(s), {room} queue place(s) free) — "
              f"ranked by total points, because an idle slot costs more than a "
              f"better hourly rate:")
        for p in picks:
            print(f"    {p['name']:26s} -> L{p['target_level']:<4} "
                  f"+{p['points']:>3}pts  {p['hours']:.1f}h  "
                  f"{ihlib.fmt_cost(p['cost'])}")
            print(f"        under [{p['section']}]  {p['description'][:70]}")
        if not picks:
            print("    nothing affordable left un-queued")

    print("\n  purchasable now (gate <= level, install present, below max),")
    print("  by progress points per slot-hour (slot time, not cost, is the")
    print("  binding constraint on progress while credits are plentiful):")
    rows = []
    for u in ihlib.iter_homelab_upgrades(homelab, definitions):
        gate = u["def"].get("unlock_level", 0)
        if gate > level or not u["install_present"] or not u["next"]:
            continue
        hours = (u["next"].get("duration_ticks") or 0) * tick_s / 3600
        pts = u["next"].get("progress_points", 0)
        rows.append((pts / hours if hours else 0, hours, u))
    for pts_hr, hours, u in sorted(rows, key=lambda r: -r[0]):
        d, nxt = u["def"], u["next"]
        section = install_names.get(u["install"], u["install"])
        queued = "  [QUEUED]" if d["type"] in queued_targets else ""
        est = "~" if nxt.get("estimated") else ""
        maxed = f"/{u['max_level']}" if u["max_level"] else ""
        print(f"    {d.get('name'):26s} L{u['level']}{maxed:<5} "
              f"+{nxt.get('progress_points', 0):>3}pts "
              f"{est}{hours:4.1f}h  {pts_hr:5.0f}pts/h  "
              f"{est}{ihlib.fmt_cost(nxt.get('cost'))}{queued}")
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
            print(f"    {d.get('name'):28s} {ihlib.fmt_cost(d.get('cost')):<24} ({state})")


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
    print(f"  chips {free_chips:,.0f}{locked_note}  "
          f"hackcoin {hw.get('hackcoin')}  "
          f"levels held {hw.get('hardware_purchased')}{stale_note}")
    if hw.get("can_reset"):
        refund = next((o.get("refund") for o in hw.get("reset_section_options") or []
                       if o.get("section") == "all"), None)
        print(f"  RESET AVAILABLE ({hw.get('reset_preview_mode')}, "
              f"{hw.get('reset_cooldown_mode')}): all-hardware refund "
              f"{ihlib.fmt_cost(refund)}")
    print("\n  combat tracks by value per 1K chips (CRAFT_WEIGHTS heuristic on the")
    print("  current build; additive pooling confirmed — mechanics.md §13):")
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
        print(f"    {d.get('name'):26s} L{d.get('current_level'):>3}  "
              f"value/lvl {value:5.2f}  per-1K-chips {per_1k:6.2f}  "
              f"next {ihlib.fmt_cost(cost)}{afford}")
    print("\n  economy/farming tracks (not scored):")
    for d in sorted(economy_rows, key=lambda d: d.get("name") or ""):
        print(f"    {d.get('name'):26s} L{d.get('current_level'):>3}  "
              f"next {ihlib.fmt_cost(d.get('next_cost'))}  "
              f"{(d.get('description') or '')[:60]}")


def cmd_contract(args):
    """Price a §10.1 craft contract by simulation instead of by discount."""
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
    baseline = ihlib.weighted_score(ihlib.stat_totals(equipped))
    preserve = ihlib.stability_preserve_chance(cap)
    print(f"# {path.name}")
    print(f"  base     {base_item.get('name')}  Stability "
          f"{base_item.get('stability')}  floor {args.floor} -> budget "
          f"{(base_item.get('stability') or 0) - args.floor}")
    print(f"  vs equipped {equipped.get('name')}  score {baseline:.1f}"
          f"   (Snapshot Backups preserve {preserve:.0%})")

    phases = []
    for spec in args.phase:
        name, _, tier = spec.rpartition(":")
        if not name or not tier.strip().lstrip("T").isdigit():
            sys.exit(f"bad --phase {spec!r}; use \"of Haste:4\"")
        phases.append((name.strip(), int(tier.strip().lstrip("T"))))
    if not phases:                       # default to plan_craft's own plan
        plan = ihlib.plan_craft(base_item, ladders, floor=args.floor,
                                preserve=preserve)
        phases = [(name, to) for name, _frm, to, _c, _e in plan["steps"]]
        print(f"  phases taken from plan_craft (pass --phase to override)")
    if not phases:
        sys.exit("no phases to run")

    print("\n  contract (execution order matters -- see best_contract_order):")
    for name, tier in phases:
        cur = next((a.get("tier") for side in ("prefixes", "suffixes")
                    for a in base_item.get(side) or []
                    if a.get("name") == name), None)
        if cur is None:
            sys.exit(f"{base_item.get('name')} has no affix {name!r}")
        att = sum(ihlib.vu_expected_attempts(x) for x in range(tier + 1, cur + 1))
        stab = sum(ihlib.vu_expected_stability(x, preserve)
                   for x in range(tier + 1, cur + 1))
        print(f"    {name:22s} T{cur} -> T{tier}   exp {att:4.1f} attempts / "
              f"{stab:4.1f} Stability")

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
            label = " -> ".join(n for n, _ in order)
            print(f"    {label:52s} P(>+5) {s['p_upgrade']:5.1%}  "
                  f"mean {s['mean']:+5.2f}  p10 {s['p10']:+5.2f}")


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


def cmd_audit(args):
    """Anomaly sweep: things that are silently costing progress right now.

    Every check here exists because a real one was missed. 27 Jul 2026: four
    homelab build slots idle for 3.5 days; 81K chips on two hardware tracks
    whose multiplicand was zero; a finished craft sitting unequipped; a
    homelabInfo panel 1,348s stale. Run before optimizing anything.
    """
    cap, path = ihlib.load_capture(args.file)
    print(f"# {path.name}")
    flags = []

    # the whole capture can be stale, not just a panel inside it: the
    # auto-stream keeps running after the last capture click, so its newest
    # `stats` record outranks everything in the file (27 Jul 2026: a capture
    # showing 44,582 unspent chips against a streamed 4,140 — already spent)
    lag, changed = ihlib.capture_stream_drift(cap)
    if lag is not None and lag > 300:
        detail = ("; ".join(f"{f} {was:,.0f} -> {now:,.0f}"
                            if isinstance(was, (int, float)) else
                            f"{f} {was} -> {now}"
                            for f, was, now in changed)
                  or "no streamed field changed, but homelab job progress and "
                     "hardware levels are not streamed — assume both moved")
        flags.append(("OUTDATED", f"capture is {lag / 60:,.0f} min behind the "
                                  f"combat stream ({detail}) — recapture before "
                                  f"spending anything"))

    for section, reason in ihlib.stale_panels(cap):
        flags.append(("STALE", f"{section}: {reason} — reopen that game tab "
                               f"and recapture before trusting it"))

    # model self-check against the game's own numbers: if stat_total cannot
    # reproduce a stat, every swap projection touching it is unsound
    for stat, reported, modelled in ihlib.validate_stat_totals(cap):
        flags.append(("MODEL", f"stat_total({stat}) = {modelled:,.4f} but the "
                               f"game reports {reported:,.4f} — fix its family "
                               f"in ihlib before trusting any projection using it"))

    hw = ihlib.hardware_state(cap)
    if hw:
        sb = hw.get("stats_breakdown") or {}
        locked = hw.get("locked_resources") or {}
        spendable, free_chips, locked_chips = ihlib.chip_budget(cap)
        # a "spend these chips" flag off an outdated capture is how a balance
        # that is already spent gets re-recommended -- say so on the same line
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

    homelab, definitions, info = ihlib.homelab_state(cap)
    if homelab:
        active = len(homelab.get("active_jobs") or [])
        pend = len(homelab.get("pending_jobs") or [])
        free = (info.get("max_build_slots") or 0) - active
        room = (info.get("max_queue_jobs") or 0) - pend
        if free or room:
            picks = ihlib.homelab_fill_suggestions(cap, limit=free + room)
            if picks:
                # name the exact jobs -- "refill them" is not an action
                named = "; ".join(
                    f"{p['name']} [{p['section']}] -> L{p['target_level']} "
                    f"(+{p['points']}pts, {p['hours']:.1f}h, "
                    f"{ihlib.fmt_cost(p['cost'])})"
                    for p in picks)
                flags.append(("IDLE", f"homelab has {free} build slot(s) and "
                                      f"{room} queue place(s) empty — fill with: "
                                      f"{named}"))
            else:
                flags.append(("IDLE", f"homelab has {free} build slot(s) and "
                                      f"{room} queue place(s) empty, and nothing "
                                      f"affordable is left un-queued"))
        gates = [(d.get("name"), (d.get("cost") or {}).get("hackcoin") or 0)
                 for d in (definitions.get("installs") or [])
                 if not (homelab.get("installed") or {}).get(d.get("type"))]
        need = sum(hc for _, hc in gates)
        # locked hackcoin cannot fund installs (mechanics.md §14) -- free only
        if need and (info.get("hackcoin") or 0) < need:
            flags.append(("RESERVE", f"{info.get('hackcoin')} free hackcoin vs "
                                     f"{need} needed for pending installs"))

    # Death streaks are only comparable within one zone: a zone's level_offset
    # shifts enemy level at equal streak (mechanics.md 15), so a baseline that
    # spans a zone change is measuring the move, not the gear.
    deaths = cap["state"].get("recentLossStreaks") or []
    zones = {d.get("zone_name") for d in deaths if d.get("zone_name")}
    if len(zones) > 1:
        flags.append(("ZONES", f"the recent death window spans {len(zones)} zones "
                               f"({', '.join(sorted(zones))}) — segment any "
                               f"baseline at the zone change before comparing"))

    equipped = {slot: item for where, slot, item in ihlib.iter_items(cap)
                if where == "equipped"}
    for where, slot, item in ihlib.iter_items(cap):
        if where != "inventory" or slot not in equipped:
            continue
        mine = ihlib.weighted_score(ihlib.stat_totals(item))
        theirs = ihlib.weighted_score(ihlib.stat_totals(equipped[slot]))
        if mine > theirs + ihlib.UPGRADE_BAND and not item.get("stability"):
            flags.append(("UNEQUIPPED", f"{slot}: {item.get('name')} scores "
                                        f"{mine:.1f} vs equipped {theirs:.1f} and "
                                        f"has 0 Stability (finished) — equip it"))

    if not flags:
        print("  no anomalies")
        return
    width = max(len(k) for k, _ in flags)
    for kind, message in flags:
        print(f"  [{kind:<{width}}] {message}")


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
    bh, bm = exp["baseline_hits"]
    pre_mean = sum(pre) / len(pre) if pre else 0
    post_mean = sum(post) / len(post) if post else 0
    base_hit = bh / (bh + bm) * 100
    post_hit = ph / (ph + pm) * 100 if ph + pm else None
    n, target = len(post), exp["target_deaths"]
    if args.brief:
        depth = (f"deaths {n}/{target}: mean {post_mean:.1f} vs {pre_mean:.1f} "
                 f"({post_mean - pre_mean:+.1f})" if post else
                 f"deaths 0/{target}")
        hit = (f"hit {post_hit:.1f}% (n={ph + pm}) vs baseline {base_hit:.1f}%"
               if post_hit is not None else
               "hit-rate: NO round data — enable Detailed Logs (Hacking panel)!")
        detail = (f"{status['detailed_fight_count']}/{status['post_fight_count']}"
                  " fights have round detail")
        print(f"A/B {exp['item']}")
        print(depth + " | " + hit)
        print(detail + (f" | {status['deaths_after_segment']} deaths post-VLAN"
                        if status["deaths_after_segment"] else ""))
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
    if status["deaths_after_segment"]:
        print(f"  ({status['deaths_after_segment']} of them after the VLAN "
              f"+1% Def segment boundary — analyse separately)")
    if post_hit is not None:
        print(f"  hit rate: {post_hit:.1f}% ({ph}h/{pm}m) vs old-Payload "
              f"deep-streak baseline {base_hit:.1f}% ({bh}h/{bm}m)")
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


def main():
    parser = argparse.ArgumentParser(prog="ih.py")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("captures").set_defaults(fn=cmd_captures)

    p = sub.add_parser("loadout")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_loadout)

    p = sub.add_parser("item")
    p.add_argument("query")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_item)

    p = sub.add_parser("candidates")
    p.add_argument("--slot")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_candidates)

    p = sub.add_parser("compare")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("diff")
    p.add_argument("old", nargs="?")
    p.add_argument("new", nargs="?")
    p.set_defaults(fn=cmd_diff)

    p = sub.add_parser("stats")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_stats)

    p = sub.add_parser("history")
    p.add_argument("query")
    p.set_defaults(fn=cmd_history)

    p = sub.add_parser("homelab")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_homelab)

    p = sub.add_parser("hardware")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_hardware)

    p = sub.add_parser("audit")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_audit)

    p = sub.add_parser("ab")
    p.add_argument("--brief", action="store_true")
    p.set_defaults(fn=cmd_ab)

    p = sub.add_parser("contract", help="simulate a craft contract's outcome")
    p.add_argument("item")
    p.add_argument("--phase", action="append", default=[],
                   metavar="'of Haste:4'",
                   help="affix:target_tier, repeatable, in execution order; "
                        "defaults to plan_craft's own plan")
    p.add_argument("--floor", type=int, default=8)
    p.add_argument("--trials", type=int, default=20000)
    p.add_argument("--order", action="store_true",
                   help="search every phase permutation")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_contract)

    p = sub.add_parser("cadence", help="measured seconds per fight")
    p.set_defaults(fn=cmd_cadence)

    p = sub.add_parser("potential")
    p.add_argument("--slot")
    p.add_argument("--file")
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--floor", type=int, default=8)
    p.add_argument("--cap", type=int, default=1,
                   help="deepest tier to plan to (default 1 = the game max; "
                        "pass 3 to reproduce pre-27-Jul-2026 projections)")
    p.set_defaults(fn=cmd_potential)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
