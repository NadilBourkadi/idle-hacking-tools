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

Output is deliberately compact; prefer this over ad-hoc capture parsing.
"""

import argparse
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
                        "combatLog", "homelabInfo")
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
        interesting = ["base_cost_with_stability", "augment_cost",
                       "augment_credit_cost", "tier_promotion_primary_cost",
                       "tier_promotion_secondary_cost", "compile_cost"]
        print("  costs:", "  ".join(
            f"{k.replace('_cost', '').replace('_', ' ')} {round(preview[k]):,}"
            for k in interesting if preview.get(k)))


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
    ladders = ihlib.tier_ladders(cap)
    print(f"# {path.name}")
    print("# Projected post-craft ceilings (Version Upgrade to T"
          f"{args.cap} cap, Compile floor {args.floor}); score = bottleneck "
          "planning heuristic (ihlib.CRAFT_WEIGHTS_*), not a game formula.")
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
            plan = ihlib.plan_craft(item, ladders, floor=args.floor, tier_cap=args.cap)
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
                  f"spend ~{plan['expected_spend']:.1f}  {aug}  "
                  f"Compile +{plan['compile_pct'] * 100:.1f}%")
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

    p = sub.add_parser("potential")
    p.add_argument("--slot")
    p.add_argument("--file")
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--floor", type=int, default=8)
    p.add_argument("--cap", type=int, default=3)
    p.set_defaults(fn=cmd_potential)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
