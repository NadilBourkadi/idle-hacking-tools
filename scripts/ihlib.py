"""Shared helpers for querying Idle Hacking full-state captures.

Encodes the slot mapping and the fitted models from
docs/static-analysis-2026-07-22.md so analyses never re-derive them.
Used by ih.py; import directly for bespoke analysis.
"""

import json
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
    """Expected Version-Upgrade attempts Tn -> T(n-1); chance = tier x 10%."""
    return 10.0 / tier


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


def plan_craft(item, ladders, floor=8, tier_cap=3):
    """Greedy expected-Stability Version-Upgrade plan + Compile projection.

    Model assumptions (conservative, documented):
      - upgraded affixes land at the target tier midpoint (roll-reset
        semantics unknown, docs/crafting.md §12);
      - unchanged affixes keep their current roll;
      - Compile multiplies explicit affixes only (implicit treatment unknown);
      - one Stability is reserved for Augment when a slot is open, but the
        unknown augmented affix contributes NO projected value (pure upside);
      - targets capped at T{tier_cap}; T2/T1 chase deliberately excluded;
      - `floor` Stability is preserved for Compile (+0.5%/point).
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

    steps, spend = [], 0.0
    if stability > 0:
        while True:
            best, best_ratio = None, 0.0
            for entry in state:
                res = step_gain(entry)
                if not res:
                    continue
                gain, estimated = res
                cost = vu_expected_attempts(entry["tier"])
                if cost > budget - spend or gain <= 0:
                    continue
                if gain / cost > best_ratio:
                    best, best_ratio = (entry, gain, estimated, cost), gain / cost
            if best is None:
                break
            entry, gain, estimated, cost = best
            spend += cost
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
        "expected_spend": spend,
        "augment_open": open_slot,
        "augment_side": forced_side,
        "compile_pct": compile_pct,
        "totals": totals,
        "score": weighted_score(totals),
        "estimated": any_estimated,
    }
