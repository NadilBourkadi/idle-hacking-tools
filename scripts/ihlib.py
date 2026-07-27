"""Shared helpers for querying Idle Hacking full-state captures.

Encodes the slot mapping and the fitted models from
docs/static-analysis-2026-07-22.md so analyses never re-derive them.
Used by ih.py; import directly for bespoke analysis.
"""

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAPTURES_DIR = ROOT / "data" / "captures"

SLOT_DISPLAY = {
    "main_hand": "Payload",
    "off_hand": "Firewall",
    "head": "Analyzer",
    "chest": "Shell",
    "gloves": "Driver",
    "boots": "Router",
    "acc1": "Daemon",
    "acc2": "Kernel",
}
DISPLAY_SLOT = {v.lower(): k for k, v in SLOT_DISPLAY.items()}
SLOT_ORDER = list(SLOT_DISPLAY)

STAT_LABELS = {
    "attack_damage": "AtkDmg",
    "attack_speed": "AtkSpd",
    "accuracy": "Acc",
    "crit_chance": "CritCh",
    "crit_damage": "CritDmg",
    "armor_penetration": "ArmorPen",
    "max_hp": "MaxHP",
    "defense": "Def",
    "evasion": "Eva",
    "regeneration": "Regen",
    "hp_regen": "Regen",
    "damage_barrier": "Barrier",
    "thorns": "Thorns",
    "corruption": "Corrupt",
}
COMBAT_ORDER = [
    "Acc", "AtkDmg", "AtkSpd", "CritCh", "CritDmg", "ArmorPen",
    "MaxHP", "Def", "Eva", "Regen", "Barrier", "Thorns", "Corrupt",
]


def stat_label(resource):
    if resource in STAT_LABELS:
        return STAT_LABELS[resource]
    return resource.replace("_multi", "").replace("_", " ")


def is_combat_stat(label):
    return label in COMBAT_ORDER


# ---- Fitted models (docs/static-analysis-2026-07-22.md) -------------------

def mult_scale(item_level):
    """Percentage-affix magnitude relative to the ilvl-1000 reference."""
    return ((item_level + 125) / 1125) ** 0.391


def flat_scale(item_level):
    """Flat-affix magnitude relative to reference (noisier fit)."""
    return ((item_level + 100) / 1021) ** 0.7849


def stability_cost_multiplier(spent):
    """Credit-cost escalation per Stability spent (exact)."""
    return 1.03 ** spent


def base_cost_estimate(required_level):
    """Approximate crafting base cost (R^2 0.995)."""
    return 1.586 * required_level ** 1.765


# ---- Capture loading -------------------------------------------------------

def capture_paths():
    return sorted(CAPTURES_DIR.glob("idle-hacking-state-*.json"))


def load_capture(path=None):
    """Load a capture (latest by default). Returns (data, path)."""
    if path is None:
        paths = capture_paths()
        if not paths:
            raise SystemExit(f"no captures in {CAPTURES_DIR}")
        path = paths[-1]
    path = Path(path)
    return json.loads(path.read_text()), path


def iter_items(capture):
    """Yield (where, slot_display, item) for equipped + inventory items."""
    state = capture["state"]
    equipment = state.get("equipmentData") or {}
    for slot in SLOT_ORDER:
        item = equipment.get(slot)
        if item:
            yield "equipped", SLOT_DISPLAY[slot], item
    for item in (state.get("inventoryData") or {}).get("items") or []:
        yield "inventory", SLOT_DISPLAY.get(item.get("slot"), item.get("slot")), item


def find_items(capture, query):
    """Match items by name substring or id prefix (case-insensitive)."""
    q = query.lower()
    return [
        (where, slot, item)
        for where, slot, item in iter_items(capture)
        if q in (item.get("name") or "").lower()
        or (item.get("id") or "").lower().startswith(q)
    ]


# ---- Item inspection -------------------------------------------------------

def iter_effects(item):
    """Yield (resource, effect_type, value) incl. the implicit."""
    implicit = item.get("implicit_info")
    if implicit:
        yield implicit.get("stat_type"), implicit.get("effect_type"), implicit.get("value", 0)
    for side in ("prefixes", "suffixes"):
        for affix in item.get(side) or []:
            for effect in affix.get("effects") or []:
                yield effect.get("resource"), effect.get("type"), effect.get("value", 0)


def stat_totals(item):
    """Aggregate item stats -> {label: (pct_total, flat_total)}."""
    totals = {}
    for resource, effect_type, value in iter_effects(item):
        label = stat_label(resource or "?")
        pct, flat = totals.get(label, (0.0, 0.0))
        if effect_type == "flat_add":
            flat += value
        else:
            pct += value
        totals[label] = (pct, flat)
    return totals


def merge_totals(items):
    merged = {}
    for item in items:
        for label, (pct, flat) in stat_totals(item).items():
            mp, mf = merged.get(label, (0.0, 0.0))
            merged[label] = (mp + pct, mf + flat)
    return merged


def fmt_totals(totals, combat_only=True):
    parts = []
    labels = [l for l in COMBAT_ORDER if l in totals]
    if not combat_only:
        labels += sorted(l for l in totals if l not in COMBAT_ORDER)
    for label in labels:
        pct, flat = totals[label]
        chunk = []
        if abs(pct) > 1e-9:
            chunk.append(f"{pct * 100:+.2f}%")
        if abs(flat) > 1e-9:
            chunk.append(f"{flat:+g}")
        if chunk:
            parts.append(f"{label} {'/'.join(chunk)}")
    return "  ".join(parts)


def roll_position(effect):
    lo, hi = effect.get("value_min"), effect.get("value_max")
    v = effect.get("value")
    if lo is None or hi is None or v is None or hi <= lo:
        return None
    return (v - lo) / (hi - lo)


def affix_lines(item):
    """Compact per-affix description lines."""
    lines = []
    for side, tag in (("prefixes", "P"), ("suffixes", "S")):
        for affix in item.get(side) or []:
            effects = []
            for effect in affix.get("effects") or []:
                label = stat_label(effect.get("resource") or "?")
                value = effect.get("value", 0)
                text = (
                    f"{label} {value:+g}"
                    if effect.get("type") == "flat_add"
                    else f"{label} {value * 100:+.2f}%"
                )
                pos = roll_position(effect)
                if pos is not None:
                    text += f" [roll {pos * 100:.0f}%]"
                effects.append(text)
            tier = affix.get("tier")
            chance = affix.get("tier_promotion_chance") or 0
            vu = f"VU {chance * 100:.0f}%" if tier != 1 else "T1 max"
            lines.append(
                f"  {tag} T{tier} {affix.get('name')} ({affix.get('group')}): "
                f"{', '.join(effects)}  ({vu})"
            )
    return lines


def item_header(item, slot=None, where=None):
    bits = [
        item.get("name"),
        f"[{slot}]" if slot else None,
        where,
        item.get("rarity"),
        f"ilvl {item.get('item_level')}",
        f"req {item.get('required_hack_level')}",
        f"stab {item.get('stability')}/{item.get('stability_max')}",
        f"scale x{mult_scale(item.get('item_level') or 0):.3f}",
    ]
    return "  ".join(str(b) for b in bits if b)


# ---- Craft-potential projection (empirical tier ladders) -------------------
#
# Inventory items are crafting BASES (docs/crafting.md §1): with 25-30
# Stability they can Version-Upgrade key affixes several tiers and Compile.
# Comparing current rolls against equipped items systematically understates
# candidates — candidate decisions must use projected ceilings
# (`ih.py potential`), never raw `compare`/`candidates` output alone.
#
# Tier ladders are EMPIRICAL: normalized per-tier value midpoints are read
# from every affix instance in the capture (actual value = normalized value
# x mult/flat_scale(ilvl); verified to reproduce across items within ~1%).
# Tiers nobody owns are log-linearly interpolated between observed
# neighbours and marked "~" — a measurement gap, not a mechanic claim.

# Planning weights for scalar ranking ONLY — a strategy heuristic encoding
# the current bottleneck model (late-streak attrition: sustain + tempo, see
# docs/current-state.md), NOT a game formula. Retune when the bottleneck
# changes. Keys are display labels (STAT_LABELS values).
CRAFT_WEIGHTS_PCT = {   # value per +1 percentage point
    "Def": 1.0, "Eva": 1.0, "Acc": 1.0, "AtkSpd": 0.9,
    "AtkDmg": 0.7, "CritCh": 0.7, "MaxHP": 0.5, "CritDmg": 0.35,
}
CRAFT_WEIGHTS_FLAT = {  # value per +1 flat point
    # Corrupt recalibrated 22 Jul: outgoing DoT ~15.6% of total output from 12
    # points in the streak-96 death fight (sum(ecd) 990 vs direct 5368) — ~1%
    # of output per point in long fights; 0.6 is deliberately conservative.
    "Regen": 0.6, "Corrupt": 0.6, "ArmorPen": 0.05,
    "Thorns": 0.05, "Barrier": 0.02,
}

# Verdict bands for ceiling-vs-equipped score deltas, calibrated against the
# realized Vital Driver craft (projected +3.9, realized -2): treat small
# positive deltas as noise/contract-shortfall, not upgrades.
UPGRADE_BAND = 5.0   # delta > +5 -> genuine upgrade candidate
INFERIOR_BAND = -5.0  # delta < -5 -> inferior; between -> sidegrade

DEFAULT_TIER_STEP = 1.4  # mean observed adjacent-tier ratio; last-resort fallback


def weighted_score(totals):
    """Scalar bottleneck score of a {label: (pct, flat)} totals dict."""
    score = 0.0
    for label, (pct, flat) in totals.items():
        score += pct * 100 * CRAFT_WEIGHTS_PCT.get(label, 0.0)
        score += flat * CRAFT_WEIGHTS_FLAT.get(label, 0.0)
    return score


def vu_expected_attempts(tier):
    """Expected Version-Upgrade attempts Tn -> T(n-1); chance = tier x 10%.

    ATTEMPTS, not Stability — the two diverge once Snapshot Backups is above
    level 0. Use this for a contract's attempt caps (what the player counts at
    the panel) and `vu_expected_stability` for budget arithmetic.
    """
    return 10.0 / tier


def vu_expected_stability(tier, preserve=0.0):
    """Expected Stability spent promoting Tn -> T(n-1).

    The success always costs 1; each failure costs 1 only when Snapshot
    Backups does not trigger. Homelab `tier_promotion_stability_preserve` is
    5%/level, so at L2 (10%) a deep chase is ~6% cheaper than the attempt
    count implies, and the saving grows with depth (3% at T7->T6, 8% at
    T2->T1) because deeper steps fail more often.
    """
    p = tier / 10.0
    return 1.0 + ((1.0 - p) / p) * (1.0 - preserve)


def stability_preserve_chance(capture):
    """Chance a failed Version Upgrade preserves Stability, from the capture.

    Read from the homelab upgrade's own effect value x its level — never
    hard-coded, because this silently changed under us: it was level 0 when
    the craft cost model was written on 22 Jul 2026 and reached level 2 by
    27 Jul, making every Stability budget since then ~6% over-conservative.
    Returns 0.0 when homelabInfo is absent (conservative).
    """
    homelab, definitions, _ = homelab_state(capture)
    if not homelab or not definitions:
        return 0.0
    for upgrade in iter_homelab_upgrades(homelab, definitions):
        for effect in upgrade["def"].get("effects") or []:
            per_level = effect.get("tier_promotion_stability_preserve")
            if per_level:
                return per_level * (upgrade.get("level") or 0)
    return 0.0


def tier_ladders(capture):
    """Empirical {(affix_id, resource, type): {tier: normalized mid value}}."""
    raw = {}
    for _, _, item in iter_items(capture):
        for side in ("prefixes", "suffixes"):
            for affix in item.get(side) or []:
                ilvl = affix.get("item_level") or item.get("item_level") or 0
                for e in affix.get("effects") or []:
                    if not e.get("value_max"):
                        continue
                    scale = (flat_scale(ilvl) if e.get("type") == "flat_add"
                             else mult_scale(ilvl))
                    mid = (e["value_min"] + e["value_max"]) / 2 / scale
                    key = (affix.get("affix_id"), e.get("resource"), e.get("type"))
                    raw.setdefault(key, {}).setdefault(affix["tier"], []).append(mid)
    return {key: {t: sum(v) / len(v) for t, v in tiers.items()}
            for key, tiers in raw.items()}


def ladder_value(ladder, tier):
    """(normalized mid value at tier, measured?) — log-linear interp/extrap."""
    import math
    if tier in ladder:
        return ladder[tier], True
    ts = sorted(ladder)
    if len(ts) == 1:
        return ladder[ts[0]] * DEFAULT_TIER_STEP ** (ts[0] - tier), False
    if tier < ts[0]:
        a, b = ts[0], ts[1]
    elif tier > ts[-1]:
        a, b = ts[-2], ts[-1]
    else:
        a = max(t for t in ts if t < tier)
        b = min(t for t in ts if t > tier)
    la, lb = math.log(ladder[a]), math.log(ladder[b])
    slope = (lb - la) / (b - a)
    return math.exp(la + slope * (tier - a)), False


def augment_state(item):
    """(slot_open?, forced_side) per docs/crafting.md §2."""
    n_pre = len(item.get("prefixes") or [])
    n_suf = len(item.get("suffixes") or [])
    if n_pre + n_suf >= item.get("max_normal_affixes", 6):
        return False, None
    if n_pre >= item.get("max_prefixes", 3):
        return True, "suffix"
    if n_suf >= item.get("max_suffixes", 3):
        return True, "prefix"
    return True, "either"


def plan_craft(item, ladders, floor=8, tier_cap=1, preserve=0.0):
    """Greedy expected-Stability Version-Upgrade plan + Compile projection.

    Model assumptions (conservative, documented):
      - upgraded affixes land at the target tier midpoint (roll-reset
        semantics unknown, docs/crafting.md §12);
      - unchanged affixes keep their current roll;
      - Compile multiplies explicit affixes only (implicit treatment unknown);
      - one Stability is reserved for Augment when a slot is open, but the
        unknown augmented affix contributes NO projected value (pure upside);
      - `floor` Stability is preserved for Compile (+0.5%/point).

    `tier_cap` defaults to T1 — the game's own maximum — so the Stability
    budget alone decides depth. It used to default to T3, which was wrong in
    the expensive direction: gain per expected Stability point RISES all the
    way down the ladder and peaks at exactly the excluded step.

        T9->T8 0.360   T7->T6 0.549   T5->T4 0.768   T3->T2 0.904  <- peak
        T8->T7 0.448   T6->T5 0.659   T4->T3 0.861   T2->T1 0.843

    (affix value compounds ~1.4x per tier while expected attempts only grow as
    10/tier). Measured 27 Jul 2026 across 50 candidate plans: uncapping raised
    the best candidate in every slot, flipped Firewall and Kernel from
    sidegrade/inferior to UPGRADE and lifted the Router candidate +8.3 -> +22.8,
    while leaving reliance on interpolated ladder points unchanged at 43/50 —
    so the "no data that deep" objection does not hold. Pass tier_cap=3 to
    reproduce pre-27-Jul projections.

    Note the calibration consequence: the cap was a systematic UNDER-projection
    that partly cancelled the contract-conservatism OVER-projection. With it
    gone, the ~5-point discount for contract conservatism matters MORE, not
    less — a §10.1 contract with attempt caps and a hard floor is deliberately
    less ambitious than this plan.
    Returns dict with steps, expected_spend, augment info, compile_pct,
    projected totals {label: (pct, flat)} and weighted scores.
    """
    stability = item.get("stability") or 0
    ilvl = item.get("item_level") or 0
    open_slot, forced_side = augment_state(item)
    reserve = 1 if (open_slot and stability > floor) else 0
    budget = stability - floor - reserve

    # mutable affix state: [side, affix, current_tier, upgraded?]
    state = []
    for side in ("prefixes", "suffixes"):
        for affix in item.get(side) or []:
            state.append({"affix": affix, "tier": affix.get("tier"), "up": False})

    def step_gain(entry):
        """Weighted gain of upgrading this affix one tier from its planned tier."""
        tier = entry["tier"]
        if tier is None or tier <= tier_cap:
            return None
        gain, estimated = 0.0, False
        for e in entry["affix"].get("effects") or []:
            key = (entry["affix"].get("affix_id"), e.get("resource"), e.get("type"))
            ladder = ladders.get(key)
            if not ladder:
                continue
            cur, m1 = ladder_value(ladder, tier)
            nxt, m2 = ladder_value(ladder, tier - 1)
            estimated = estimated or not (m1 and m2)
            label = stat_label(e.get("resource") or "?")
            if e.get("type") == "flat_add":
                gain += (nxt - cur) * flat_scale(ilvl) * CRAFT_WEIGHTS_FLAT.get(label, 0.0)
            else:
                gain += (nxt - cur) * mult_scale(ilvl) * 100 * CRAFT_WEIGHTS_PCT.get(label, 0.0)
        return gain, estimated

    steps, spend, attempts = [], 0.0, 0.0
    if stability > 0:
        while True:
            best, best_ratio = None, 0.0
            for entry in state:
                res = step_gain(entry)
                if not res:
                    continue
                gain, estimated = res
                # budget in Stability, not attempts -- they differ once
                # Snapshot Backups is above level 0
                cost = vu_expected_stability(entry["tier"], preserve)
                if cost > budget - spend or gain <= 0:
                    continue
                if gain / cost > best_ratio:
                    best, best_ratio = (entry, gain, estimated, cost), gain / cost
            if best is None:
                break
            entry, gain, estimated, cost = best
            spend += cost
            attempts += vu_expected_attempts(entry["tier"])
            entry["tier"] -= 1
            entry["up"] = True
            steps.append((entry["affix"].get("name"), entry["affix"].get("tier"),
                          entry["tier"], cost, estimated))

    compile_left = max(0.0, stability - reserve - spend)
    # Compiled (stability-0) items already carry their bonus baked into the
    # effect values (confirmed 22 Jul: Compile multiplies explicit values in
    # place, implicit untouched, ranges unchanged) — never re-apply it.
    compile_pct = 0.005 * compile_left if stability > 0 else 0.0

    # projected totals
    totals = {}
    def add(label, etype, value):
        pct, flat = totals.get(label, (0.0, 0.0))
        if etype == "flat_add":
            flat += value
        else:
            pct += value
        totals[label] = (pct, flat)

    implicit = item.get("implicit_info")
    if implicit:
        add(stat_label(implicit.get("stat_type") or "?"),
            implicit.get("effect_type"), implicit.get("value", 0))
    any_estimated = False
    for entry in state:
        affix = entry["affix"]
        for e in affix.get("effects") or []:
            label = stat_label(e.get("resource") or "?")
            if entry["up"]:
                key = (affix.get("affix_id"), e.get("resource"), e.get("type"))
                ladder = ladders.get(key)
                if ladder:
                    norm, measured = ladder_value(ladder, entry["tier"])
                    any_estimated = any_estimated or not measured
                    scale = (flat_scale(ilvl) if e.get("type") == "flat_add"
                             else mult_scale(ilvl))
                    value = norm * scale
                else:
                    value = e.get("value", 0)
            else:
                value = e.get("value", 0)
            add(label, e.get("type"), value * (1 + compile_pct))

    # merge upgraded steps per affix for compact display
    merged = {}
    for name, t_from, t_to, cost, estimated in steps:
        cur = merged.setdefault(name, [t_from, t_to, 0.0, False])
        cur[1] = min(cur[1], t_to)
        cur[2] += cost
        cur[3] = cur[3] or estimated
    plan_steps = [(name, f, t, c, est) for name, (f, t, c, est) in merged.items()]

    return {
        "steps": plan_steps,
        "expected_spend": spend,          # Stability
        "expected_attempts": attempts,    # panel clicks; > spend when preserve > 0
        "preserve": preserve,
        "augment_open": open_slot,
        "augment_side": forced_side,
        "compile_pct": compile_pct,
        "totals": totals,
        "score": weighted_score(totals),
        "estimated": any_estimated,
    }


# ---- Homelab and hardware (lazy bindings; schema notes in
# docs/game-client-internals.md). These read capture values only; costs and
# gates always come from the capture, never re-derived. -----------------------

RESOURCE_SHORT = {
    "credits": "cr", "chips": "chips", "hackcoin": "hc",
    "snippets": "snip", "cycles": "cyc", "hashes": "hash", "packets": "pkt",
}


def fmt_cost(cost):
    """Compact '500M cr + 1M pkt + 1 hc' rendering of a cost dict."""
    def compact(n):
        for div, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
            if abs(n) >= div:
                value = n / div
                return f"{value:.3g}{suffix}"
        return f"{n:g}"
    parts = [f"{compact(v)} {RESOURCE_SHORT.get(k, k)}"
             for k, v in (cost or {}).items() if v]
    return " + ".join(parts) if parts else "free"


def homelab_state(capture):
    """(homelab, definitions, info) from a capture, or (None, None, {})."""
    info = capture["state"].get("homelabInfo") or {}
    return info.get("homelab"), info.get("definitions"), info


def homelab_fill_suggestions(capture, limit=3, allow_hackcoin=False):
    """Concrete jobs to put in free build slots / queue places, best first.

    Ranked by **total progress points**, not points per slot-hour. For a slot
    that will run unattended the idle time after a short job costs more than
    its better nominal rate: a 1.0h/95pt job beats a 0.5h/110pt-per-hour job
    outright if nobody is there to refill at the 30-minute mark. Excludes jobs
    already active or queued, gated jobs, and (by default) anything costing
    hackcoin, which is reserved for install gates.
    """
    homelab, definitions, info = homelab_state(capture)
    if not homelab:
        return []
    level = homelab.get("level", 0)
    tick_s = info.get("tick_seconds") or 5
    busy = {j.get("target") for j in (homelab.get("active_jobs") or [])
            + (homelab.get("pending_jobs") or [])}
    out = []
    for u in iter_homelab_upgrades(homelab, definitions):
        d, nxt = u["def"], u["next"]
        if (d.get("unlock_level", 0) > level or not u["install_present"]
                or not nxt or d["type"] in busy):
            continue
        cost = nxt.get("cost") or {}
        if cost.get("hackcoin") and not allow_hackcoin:
            continue
        if (cost.get("credits") or 0) > (info.get("credits") or 0):
            continue
        out.append({
            "name": d.get("name"), "type": d["type"],
            "level": u["level"], "target_level": u["level"] + 1,
            "points": nxt.get("progress_points", 0),
            "hours": (nxt.get("duration_ticks") or 0) * tick_s / 3600,
            "cost": cost, "description": d.get("description") or "",
        })
    out.sort(key=lambda r: (-r["points"], -r["hours"]))
    return out[:limit]


def homelab_level_threshold(definitions, target_level):
    """Progress points required to reach target_level (None if uncharted)."""
    thresholds = definitions.get("level_thresholds") or []
    idx = target_level - 1
    return thresholds[idx] if 0 <= idx < len(thresholds) else None


def iter_homelab_upgrades(homelab, definitions):
    """Yield per-upgrade dicts with current level and next-level details.

    next: {level, cost, duration_ticks, progress_points, estimated} — exact
    when the definition carries a per-level table, otherwise extrapolated
    from base cost/progress fields (estimated=True).
    """
    current = homelab.get("upgrade_levels") or {}
    installed = homelab.get("installed") or {}
    for group in definitions.get("upgrade_groups") or []:
        for upg in group.get("upgrades") or []:
            level = current.get(upg["type"], 0)
            max_level = upg.get("max_level") or 0
            nxt = None
            if not max_level or level < max_level:
                for entry in upg.get("levels") or []:
                    if entry.get("level") == level + 1:
                        nxt = dict(entry, estimated=False)
                        break
                if nxt is None:
                    # Scaling verified against the 23 Jul active-job cost
                    # snapshots: cost = base_cost x target_level (hackcoin
                    # capped at hackcoin_cost_cap), progress = base + per x
                    # target_level.
                    target = level + 1
                    cost = {k: v * target
                            for k, v in (upg.get("base_cost") or {}).items()}
                    cap = upg.get("hackcoin_cost_cap")
                    if cap and cost.get("hackcoin"):
                        cost["hackcoin"] = min(cost["hackcoin"], cap)
                    nxt = {
                        "level": target,
                        "cost": cost,
                        "duration_ticks": (upg.get("duration_base_ticks", 0)
                                           + upg.get("duration_ticks_per_level", 0)
                                           * (target - 1)),
                        "progress_points": (upg.get("progress_base", 0)
                                            + upg.get("progress_per_level", 0) * target),
                        "estimated": True,
                    }
            yield {
                "def": upg,
                "install": group.get("install"),
                "install_present": bool(installed.get(group.get("install"))),
                "level": level,
                "max_level": max_level,
                "next": nxt,
            }


def hardware_state(capture):
    return capture["state"].get("hardwareInfo") or None


def hardware_track_value(defn, stats_breakdown):
    """Heuristic bottleneck value of +1 level, on the CRAFT_WEIGHTS scale.

    Returns None for pure economy tracks (no combat_stat effect).

    Hardware %, homelab % and equipment % share ONE additive pool — confirmed
    formula-level 27 Jul 2026 (`docs/mechanics.md` §13), so the pooling
    assumption here is no longer a guess; only the CRAFT_WEIGHTS behind it
    remain heuristic. Scores are in gear-affix units:

    - percentage stats: a gear affix of +1% adds 0.01 to the pool, so a level
      granting `additive_per_level` is worth `per_level * 100` affix points.
    - gear-flat stats (Regen, Corrupt, Thorns, Barrier, ArmorPen): the pool
      multiplies the item flat total, so a level yields
      `equipment_flat * per_level` realised points; dividing by the pool
      multiplier converts back to affix points (a gear +1 becomes 1*pool
      realised). A track whose `equipment_flat` is 0 is worth exactly 0 —
      e.g. Packet Shield and Exploit Framework on 27 Jul 2026, which were
      multiplying zero while holding 81K chips.
    """
    value = None
    for effect in defn.get("effects") or []:
        stat = effect.get("combat_stat")
        if not stat:
            continue
        label = stat_label(stat)
        per_level = effect.get("additive_per_level") or effect.get("mult_per_level") or 0
        # `combat_stat` also covers drop-economy multipliers (item_rarity,
        # drop_boost) that CRAFT_WEIGHTS does not model and that have no
        # stats_breakdown entry. Leave those unscored (None) rather than 0, so
        # callers can tell "not modelled" from "modelled and worth nothing".
        if label not in CRAFT_WEIGHTS_PCT and label not in CRAFT_WEIGHTS_FLAT:
            continue
        value = value or 0.0
        if label in CRAFT_WEIGHTS_PCT:
            value += per_level * 100 * CRAFT_WEIGHTS_PCT[label]
        else:
            b = (stats_breakdown or {}).get(stat) or {}
            flat = b.get("equipment_flat") or 0
            pool = (1 + (b.get("equipment_pct") or 0) + (b.get("hardware") or 0)
                    + (b.get("homelab") or 0))
            value += per_level * flat * CRAFT_WEIGHTS_FLAT[label] / pool
    return value


# ---- Panel freshness -------------------------------------------------------
# Lazy sections hold whatever the game panel last read, which can badly predate
# the capture click (observed 27 Jul 2026: a homelabInfo block 1,348s stale, and
# a hardwareInfo block reporting a credit balance 3.5B out of date). Two
# independent detectors, because only homelabInfo carries a server clock.

def panel_freshness(capture):
    """[(section, age_seconds_or_None, credits_or_None)] for lazy sections.

    `age` compares the section's own server clock to the capture timestamp.
    Differing `credits` across sections proves at least one is stale even when
    no clock is present.
    """
    state = capture["state"]
    stamp = capture.get("capturedAt")
    captured_ms = None
    if stamp:
        captured_ms = datetime.fromisoformat(
            stamp.replace("Z", "+00:00")).timestamp() * 1000
    rows = []
    for section in ("homelabInfo", "hardwareInfo"):
        info = state.get(section) or {}
        if not info:
            continue
        server_ms = info.get("server_time_ms")
        age = ((captured_ms - server_ms) / 1000
               if server_ms and captured_ms else None)
        rows.append((section, age, info.get("credits")))
    return rows


def stale_panels(capture, max_age_s=300, credit_tolerance=0.005):
    """Sections that look stale, as [(section, reason)]."""
    rows = panel_freshness(capture)
    credits = [c for _, _, c in rows if c]
    worst = []
    for section, age, credit in rows:
        if age is not None and age > max_age_s:
            worst.append((section, f"panel data {age:,.0f}s older than capture"))
        elif credits and credit and max(credits) - min(credits) > \
                credit_tolerance * max(credits) and credit != min(credits):
            worst.append((section, f"reports {credit:,.0f} credits vs "
                                   f"{min(credits):,.0f} elsewhere"))
    return worst


# ---- Stat composition (mechanics.md §13, formula-level) --------------------
# Hardware %, homelab % and equipment % share ONE additive pool. Three families
# differ only in what that pool multiplies.
SCALING_STATS = {"max_hp", "defense", "accuracy", "evasion"}
DIRECT_STATS = {"attack_speed", "crit_chance", "crit_damage"}
# everything else in stats_breakdown is gear-flat (regeneration, corruption,
# thorns, damage_barrier, armor_penetration) -> pool multiplies equipment_flat.


def stat_pool(breakdown):
    """Additive pool multiplier for one stats_breakdown entry."""
    return (1 + (breakdown.get("equipment_pct") or 0)
            + (breakdown.get("hardware") or 0) + (breakdown.get("homelab") or 0))


def stat_total(breakdown, stat, d_equipment_pct=0.0, d_hardware=0.0,
               d_homelab=0.0, d_equipment_flat=0.0):
    """Recompute a stat under pool/flat deltas. Reproduces the live total at 0.

    Verified against every stat in the 27 Jul 2026 capture; use this instead of
    re-deriving the arithmetic per analysis.
    """
    b = breakdown or {}
    pool = stat_pool(b) + d_equipment_pct + d_hardware + d_homelab
    if stat in DIRECT_STATS:
        return (b.get("base") or 0) + pool - 1
    flat = (b.get("equipment_flat") or 0) + d_equipment_flat
    if stat in SCALING_STATS:
        return ((b.get("base") or 0) + (b.get("level") or 0) + flat) * pool
    return flat * pool


# ---- Hardware shop cost model and allocation planner -----------------------
# Chip cost per level is a clean power law, fitted live off next_cost so it
# tracks the game rather than a hard-coded constant. Validated 27 Jul 2026:
# whole-build cumulative predicted 1,012,105 chips vs the game's own reset
# refund of 1,002,284 (+1.0%).

GATHER_RESOURCES = ("snippets", "cycles", "hashes", "packets")


def hardware_cost_family(defn):
    """'combat' | 'economy' | 'special', by the SHAPE of next_cost.

    Tracks sharing a cost shape share a cost curve; mixing them wrecks the fit
    (spread 13x when all tracks are pooled). Combat tracks bill chips+credits,
    economy tracks bill chips+one gathering resource, and the hackcoin-gated
    drop/rarity/XP tracks are on their own much steeper curve.
    """
    cost = defn.get("next_cost") or {}
    if cost.get("hackcoin"):
        return "special"
    resources = sum(1 for r in GATHER_RESOURCES if cost.get(r))
    if resources > 1:
        return "special"
    return "economy" if resources else "combat"


def hardware_cost_curve(hardware_info, types=None, key="chips",
                        family="combat", min_level=10):
    """Fit cost(L) = A * L**p over one cost family. Returns (A, p, spread).

    `spread` is max/min of the implied A across the sampled tracks — a fit
    quality check. Under ~1.05 is a good single-family fit; higher means the
    sample does not share one curve and the result should not be trusted.
    Pass `types` to override the family selection explicitly. Tracks below
    `min_level` are excluded from the sample: they carry a cost floor that
    bends the low end (fitting them in moved whole-build error 1.0% -> 4.1%).
    """
    defs = [d for d in hardware_info.get("definitions") or []
            if (d.get("type") in types if types is not None
                else hardware_cost_family(d) == family)
            and (d.get("current_level") or 0) >= min_level
            and (d.get("next_cost") or {}).get(key)]
    if len(defs) < 2:
        return None
    best = None
    for p in (x / 2000 for x in range(1400, 3000)):
        implied = [d["next_cost"][key] / d["current_level"] ** p for d in defs]
        spread = max(implied) / min(implied)
        if best is None or spread < best[2]:
            best = (sum(implied) / len(implied), p, spread)
    return best


def hardware_cumulative(curve, level):
    """Total cost to take a track from 0 to `level` under a fitted curve."""
    A, p, _ = curve
    return A * level ** (p + 1) / (p + 1) if level > 0 else 0.0


def hardware_plan(hardware_info, stats_breakdown, budget_chips, curve=None):
    """Equal-marginal-value-per-chip allocation across combat tracks.

    Returns [(name, type, current_level, target_level, value_per_level,
    chip_delta)] sorted by value. `budget_chips` is spendable chips (locked +
    free); current levels are never reduced, so this plans purchases only --
    for a full re-allocation, call it with the post-reset level-0 state.
    """
    rows = []
    for d in hardware_info.get("definitions") or []:
        value = hardware_track_value(d, stats_breakdown)
        if value is None:
            continue
        rows.append([d.get("name"), d.get("type"), d.get("current_level") or 0,
                     value])
    if curve is None:
        curve = hardware_cost_curve(hardware_info, family="combat")
    if curve is None:
        return []
    p = curve[1]
    sunk = sum(hardware_cumulative(curve, r[2]) for r in rows)
    lo, hi = 0.0, 10.0
    for _ in range(300):                     # bisect the marginal-value line
        lam = (lo + hi) / 2
        cost = sum(hardware_cumulative(curve, (r[3] / lam) ** (1 / p))
                   for r in rows if r[3] > 0)
        lo, hi = (lam, hi) if cost > sunk + budget_chips else (lo, lam)
    lam = (lo + hi) / 2
    out = []
    for name, typ, level, value in rows:
        target = max(level, round((value / lam) ** (1 / p)) if value > 0 else 0)
        out.append((name, typ, level, target, value,
                    hardware_cumulative(curve, target)
                    - hardware_cumulative(curve, level)))
    return sorted(out, key=lambda r: -r[4])


# ---- Active A/B experiment tracking ----------------------------------------
# The experiment definition is code-as-record (like the cost model). When an
# A/B concludes, move the outcome to docs/decision-log.md and replace/clear
# this block. Aggregation walks ALL captures and dedupes, so every capture
# permanently banks whatever the rolling combat windows held at click time.

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

# No experiment currently running (set to a dict like the concluded ones
# above when the next A/B starts). Concluded experiments stay importable for
# retrospective analysis: experiment_status(SHELL_AB_2026_07_23).
ACTIVE_EXPERIMENT = None


STREAM_DIR = ROOT / "data" / "combat-stream"


def fight_key(f):
    """Content identity for a combat-log fight entry. Fight ids are
    PER-SESSION (the client counter resets on reload) — never treat them as
    global; this key is what makes cross-capture/stream dedupe safe."""
    return (f.get("id"), f.get("enemy_name"), f.get("current_win_streak"),
            f.get("rounds"), f.get("damage_dealt"))


def _fight_record(f, post, ms=None):
    rounds = f.get("combat_log") or []
    shp, mhp = f.get("starting_hp"), f.get("max_hp")
    return {
        "id": f.get("id"),
        "post": post,
        "ms": ms,
        "streak": f.get("current_win_streak"),
        "victory": f.get("victory"),
        "rounds": f.get("rounds"),
        "detail": bool(rounds),
        "ph": sum(r.get("ph") or 0 for r in rounds),
        "pm": sum(1 for r in rounds if r.get("pm")),
        # gross intake + recovery components (see data-dictionary: net drain
        # = dmg - rg - soak is directional; the identity does not close
        # exactly, suspected overheal capping in prg)
        "dmg": f.get("damage_taken") or 0,
        "rg": sum(r.get("prg") or 0 for r in rounds),
        "soak": sum(r.get("pbs") or 0 for r in rounds),
        "sfrac": (shp / mhp) if shp is not None and mhp else None,
        "eva": (f.get("enemy_stats") or {}).get("effective_evasion", 0),
        "enemy": f.get("enemy_name"),
    }


def _absorb_fight(fights, f, post, ms=None):
    key = fight_key(f)
    known = fights.get(key)
    if known and known["detail"]:
        if post and not known["post"]:
            known["post"] = True
        return
    fights[key] = _fight_record(f, post, ms)


def stream_records():
    """Yield deduped ledger records from data/combat-stream/*.jsonl."""
    for path in sorted(STREAM_DIR.glob("*.jsonl")):
        for line in path.read_text().splitlines():
            line = line.strip()
            if line:
                yield json.loads(line)


def experiment_status(experiment=None):
    """Aggregate the active A/B across all captures + the stream ledger.

    Deaths dedupe by ended_at_ms; fights by fight_key (see above). Each
    capture classifies its own fights: captures taken before equip are pre;
    captures after equip use boundary_fight_id only if their window still
    reaches ids above it (same session as the equip), otherwise the session
    restarted post-equip and every fight is post. Ledger records carry a
    seen_ms and classify by that (streaming postdates any equip by design).
    Round-level detail exists only for fights run with the Hacking panel's
    "Detailed Logs" checkbox enabled (verified 23 Jul; it records regardless
    of the visible screen).
    """
    exp = experiment or ACTIVE_EXPERIMENT
    if exp is None:
        return None
    deaths = {}       # ended_at_ms -> entry
    fights = {}       # content key -> compact record (+ post flag)
    for record in stream_records():
        if record.get("kind") == "death":
            entry = record.get("death") or {}
            if entry.get("ended_at_ms"):
                deaths[entry["ended_at_ms"]] = entry
        elif record.get("kind") == "fight":
            f = record.get("fight") or {}
            post = (record.get("seen_ms") or 0) >= exp["equip_ms"]
            _absorb_fight(fights, f, post, record.get("seen_ms"))
    for path in capture_paths():
        cap, _ = load_capture(path)
        state = cap["state"]
        captured_ms = None
        stamp = cap.get("capturedAt")
        if stamp:
            captured_ms = int(datetime.fromisoformat(
                stamp.replace("Z", "+00:00")).timestamp() * 1000)
        for entry in state.get("recentLossStreaks") or []:
            ms = entry.get("ended_at_ms")
            if ms:
                deaths[ms] = entry
        log = state.get("combatLog") or []
        ids = [f.get("id") for f in log if f.get("id") is not None]
        capture_pre = captured_ms is not None and captured_ms < exp["equip_ms"]
        same_session_as_equip = bool(ids) and max(ids) > exp["boundary_fight_id"]
        for f in log:
            fid = f.get("id")
            if fid is None:
                continue
            if capture_pre:
                post = False
            elif same_session_as_equip:
                post = fid > exp["boundary_fight_id"]
            else:
                post = True  # session restarted after equip
            _absorb_fight(fights, f, post, captured_ms)
    post_deaths = sorted(
        (e for ms, e in deaths.items() if ms >= exp["equip_ms"]),
        key=lambda e: e["ended_at_ms"])
    pre_deaths = sorted(
        (e for ms, e in deaths.items() if ms < exp["equip_ms"]),
        key=lambda e: e["ended_at_ms"])
    post_fights = [f for f in fights.values() if f["post"]]
    detailed = [f for f in post_fights if f["detail"]]
    ph = sum(f["ph"] for f in detailed)
    pm = sum(f["pm"] for f in detailed)
    segmented = [e for e in post_deaths if e["ended_at_ms"] >= exp["segment_ms"]]
    recent_ms = exp.get("baseline_recent_ms", 0)
    return {
        "experiment": exp,
        "pre_death_streaks": [e["streak_ended"] for e in pre_deaths],
        "pre_recent_streaks": [e["streak_ended"] for e in pre_deaths
                               if e["ended_at_ms"] >= recent_ms],
        "post_death_streaks": [e["streak_ended"] for e in post_deaths],
        "post_deaths": post_deaths,
        "deaths_after_segment": len(segmented),
        "post_fight_count": len(post_fights),
        "detailed_fight_count": len(detailed),
        "post_hits": (ph, pm),
        "fights": list(fights.values()),
    }


MECH_BRACKETS = ((24, 42), (60, 85), (86, 105))


def experiment_mechanism(status):
    """Mechanism-metric readout for an A/B (locked as tooling 23 Jul 2026
    after the Phoenix Shell keep-rule amendment).

    Judge crafts on these, not on death streak alone: net drain/fight
    (gross damage_taken minus in-fight prg and barrier absorption —
    directional, see data-dictionary), attrition onset (first fight of a
    run starting below 90% HP — exact), and realized regen per round.
    Eras: pre = same-loadout window [baseline_recent_ms, equip); post is
    split at segment_ms into post / post-seg.
    """
    exp = status["experiment"]
    lo_ms = exp.get("baseline_recent_ms", 0)
    groups = {"pre": [], "post": [], "post-seg": []}
    for f in status["fights"]:
        ms = f["ms"]
        if f["post"]:
            era = "post-seg" if ms and ms >= exp["segment_ms"] else "post"
        elif ms and lo_ms <= ms < exp["equip_ms"]:
            era = "pre"
        else:
            continue  # older loadouts or unknown timestamp
        groups[era].append(f)

    out = {}
    for era, rows in groups.items():
        det = [f for f in rows if f["detail"] and f["victory"]]
        brackets = {}
        for lo, hi in MECH_BRACKETS:
            sel = [f for f in det if lo <= (f["streak"] or 0) <= hi]
            if sel:
                n = len(sel)
                brackets[(lo, hi)] = {
                    "n": n,
                    "gross": sum(f["dmg"] for f in sel) / n,
                    "net": sum(f["dmg"] - f["rg"] - f["soak"]
                               for f in sel) / n,
                    "rounds": sum(f["rounds"] or 0 for f in sel) / n,
                }
        deep_rounds = sum(f["rounds"] or 0 for f in det
                          if (f["streak"] or 0) >= 60)
        deep_rg = sum(f["rg"] for f in det if (f["streak"] or 0) >= 60)
        onsets = []
        cur, last_streak = None, -1
        for f in sorted(rows, key=lambda f: (f["ms"] or 0, f["streak"] or 0)):
            st = f["streak"] or 0
            if st < last_streak:
                if cur is not None:
                    onsets.append(cur)
                cur = None
            last_streak = st
            # streak > 10 skips the post-death heal-up artifact
            if cur is None and st > 10 and f["sfrac"] is not None \
                    and f["sfrac"] < 0.90:
                cur = st
        if cur is not None:
            onsets.append(cur)
        out[era] = {
            "brackets": brackets,
            "onsets": sorted(onsets),
            "prg_per_round": (deep_rg / deep_rounds) if deep_rounds else None,
        }
    return out
