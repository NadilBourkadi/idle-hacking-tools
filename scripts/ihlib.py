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
