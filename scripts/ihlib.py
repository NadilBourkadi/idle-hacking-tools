"""Shared helpers for querying Idle Hacking full-state captures.

Encodes the slot mapping and the fitted models from
docs/static-analysis-2026-07-22.md so analyses never re-derive them.
Used by ih.py; import directly for bespoke analysis.
"""

import itertools
import json
import random
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
# Two of these are under active challenge as of 27 Jul 2026 -- values left
# UNCHANGED on purpose, because driver-ab-2026-07-27 is mid-flight and moving
# weights would break comparability with its own baseline:
#   AtkSpd 0.9 -- the reason was wrong, the number may be right. Attack speed
#     buys NO extra fights per hour (cadence is a fixed 4.872 s tick,
#     mechanics.md §14); it pays by shortening fights in ROUNDS (-2% to -5%
#     measured), which cuts enemy attacks per fight. It is a mitigation stat,
#     not an economy one, and the 22 Jul "tempo does not move the death
#     ceiling" law is in question (open-questions.md).
#   Acc 1.0 -- probably TOO HIGH. Cutting Accuracy 7,595 -> 7,265 (-4.35%)
#     produced no hit-rate loss at matched streak band (+0.9 to +1.7pp across
#     three bands, 8,195 attacks) against a linear prediction of -1.7pp.
#     Accuracy looks saturated in this region. Resolve with the Software
#     Profiler before re-weighting; see open-questions.md.
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

# Stability held back for Compile. Was 8 ("+4% Compile") from 22 Jul 2026 to
# 28 Jul 2026 -- a default nobody ever tested, and it was suppressing EVERY
# craft verdict in this workspace by more than UPGRADE_BAND itself.
#
# Compile pays 0.5% per preserved point, spread across all affixes. One deeper
# Version-Upgrade step multiplies ONE affix by 1.26-1.40x, and affix value is
# concentrated in one or two lines -- so a tier step beats 0.5%-of-everything
# almost always. `simulate_contract` swept floor 0/2/4/6/8/10 over three live
# candidates on 28 Jul 2026 and lower was better on mean, median, p10 AND p90
# in every case, with the worst case essentially flat:
#
#   Assault Kernel of Corruption    floor 8 mean +14.9  ->  floor 0 mean +26.3
#   Titanic Firewall of Sandboxing  floor 8 mean +15.5  ->  floor 0 mean +28.3
#   Untouchable Payload of Lightning floor 8 mean +11.0 ->  floor 0 mean +19.0
#
# Confirmed live the same evening: the Hearty Firewall contract was written to
# floor 8 (projected mean +15.1, p90 +18.9), the player crossed the floor and
# ran to 1 Stability, and the item realized **+44.6** -- above even the
# floor-1 simulation's p90 (+40.3).
#
# Set to 2 rather than 0 to keep one Refactor/retry in hand (see crafting.md
# 10.1 phase 7, which needs floor + 1); that option costs ~1-2 score points
# against floor 0 and the simulator does not value it.
COMPILE_FLOOR = 2

# Adjacent-tier value ratio. NOT one constant: measured within-family across
# every percentage affix in the 27 Jul 2026 capture, the step is region-
# dependent, and the single 1.4 that stood here was fitted on shallow tiers
# only -- the exact regime error this workspace keeps repeating.
#
#   upper tier >= 6   n=50   median 1.398   p25 1.341  p75 1.415
#   upper tier <= 5   n=25   median 1.263   p25 1.250  p75 1.288
#
# Over a full T6->T1 chase, 1.4 instead of 1.263 over-projects the affix by
# (1.4/1.263)^5 = 1.90x. Deep steps are also far more family-dependent than
# shallow ones (1.15 on suffix_attack, 1.41 on suffix_adaptive_shell), so a
# ceiling resting on an extrapolated deep ladder carries real spread -- see
# `plan_craft`'s conservative score.
TIER_STEP_SHALLOW = 1.398
TIER_STEP_DEEP = 1.263
TIER_STEP_DEEP_LOW = 1.250   # p25 -- the conservative bound for verdicts
DEEP_TIER = 5                # tiers <= this promote at the deep step


def tier_step(upper_tier, deep=TIER_STEP_DEEP):
    """Value ratio for the promotion T(upper) -> T(upper - 1)."""
    return TIER_STEP_SHALLOW if upper_tier > DEEP_TIER else deep


def fit_tier_steps(capture, min_obs=6, ladders=None):
    """(shallow, deep) adjacent-tier ratios measured from the ladder data.

    Self-validating replacement for the hard-coded constants: re-fits from
    every within-family adjacent-tier pair present, so the law cannot rot as
    the inventory turns over. Falls back to the module constants for a region
    with fewer than `min_obs` observations. Pass `ladders` (normally
    `tier_ladders_archive()`) so the fit does not lose pairs to decompiling.
    """
    if ladders is None:
        ladders = tier_ladders(capture)
    shallow, deep = [], []
    for key, ladder in ladders.items():
        if key[2] != "mult_add":   # flat affixes scale too noisily to fit on
            continue
        tiers = sorted(ladder)
        for lo, hi in zip(tiers, tiers[1:]):
            step = (ladder[lo] / ladder[hi]) ** (1.0 / (hi - lo))
            (shallow if hi > DEEP_TIER else deep).append(step)

    def median(values, fallback):
        if len(values) < min_obs:
            return fallback
        values = sorted(values)
        mid = len(values) // 2
        return (values[mid] if len(values) % 2
                else (values[mid - 1] + values[mid]) / 2)

    return (median(shallow, TIER_STEP_SHALLOW), median(deep, TIER_STEP_DEEP))


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


def _collect_ladder_obs(capture, raw):
    """Accumulate {(affix_id, resource, type): {tier: [normalized mids]}}."""
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
    return raw


def tier_ladders(capture):
    """Empirical {(affix_id, resource, type): {tier: normalized mid value}}.

    Single-capture view: only tiers currently sitting on an owned item. Prefer
    `tier_ladders_archive` for craft planning -- see the warning there.
    """
    return {key: {t: sum(v) / len(v) for t, v in tiers.items()}
            for key, tiers in _collect_ladder_obs(capture, {}).items()}


_LADDER_ARCHIVE_CACHE = {}


def tier_ladders_archive(paths=None):
    """Tier ladders unioned over EVERY capture, not just the latest.

    An affix's per-tier value range is a game constant, so an observation stays
    valid after the item carrying it is gone -- but `tier_ladders(capture)`
    forgets it, which makes craft verdicts silently decay as inventory is
    cleared. Measured 27 Jul 2026: decompiling `Elusive Kernel of Regeneration`
    (a +1.7 sidegrade) removed the ONLY `suffix_adaptive_shell` T7 observation
    owned, and the Bastioned Firewall of Infection verdict fell +9.0 -> +4.6 an
    hour later with no game state changed at all. Unioning the archive makes
    the ladder monotonically improve and immune to decompiling.

    Regime: valid only while the game does not rebalance affix ranges. If it
    ever does, old captures become contaminating rather than informative --
    re-fit from captures after the change and note the boundary here.
    """
    paths = [Path(p) for p in (paths if paths is not None else capture_paths())]
    signature = tuple(sorted(str(p) for p in paths))
    if signature in _LADDER_ARCHIVE_CACHE:
        return _LADDER_ARCHIVE_CACHE[signature]
    raw = {}
    for path in paths:
        try:
            _collect_ladder_obs(json.loads(path.read_text()), raw)
        except (OSError, ValueError, KeyError):
            continue                 # a malformed capture must not blind the fit
    ladders = {key: {t: sum(v) / len(v) for t, v in tiers.items()}
               for key, tiers in raw.items()}
    _LADDER_ARCHIVE_CACHE[signature] = ladders
    return ladders


def _walk_tiers(value, from_tier, to_tier, deep_step):
    """Extrapolate a ladder value between tiers, one region-aware step at a time."""
    tier = from_tier
    while tier > to_tier:            # going deeper: value grows
        value *= tier_step(tier, deep_step)
        tier -= 1
    while tier < to_tier:            # going shallower: value shrinks
        tier += 1
        value /= tier_step(tier, deep_step)
    return value


def ladder_value(ladder, tier, deep_step=TIER_STEP_DEEP):
    """(normalized mid value at tier, measured?).

    Log-linear *interpolation* between two observations — bounded by data, so
    the region question does not arise. *Extrapolation* beyond the observed
    range instead walks the region-aware `tier_step` ladder: projecting a
    shallow-fitted slope into T1-T5 was a systematic ~1.9x over-projection at
    full depth (see TIER_STEP_SHALLOW/DEEP).
    """
    import math
    if tier in ladder:
        return ladder[tier], True
    ts = sorted(ladder)
    if tier < ts[0]:                                   # deeper than observed
        return _walk_tiers(ladder[ts[0]], ts[0], tier, deep_step), False
    if tier > ts[-1]:                                  # shallower than observed
        return _walk_tiers(ladder[ts[-1]], ts[-1], tier, deep_step), False
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


def plan_craft(item, ladders, floor=COMPILE_FLOOR, tier_cap=1, preserve=0.0,
               deep_step=TIER_STEP_DEEP, deep_step_low=TIER_STEP_DEEP_LOW):
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

    (affix value compounds per tier while expected attempts only grow as
    10/tier). Measured 27 Jul 2026 across 50 candidate plans: uncapping raised
    the best candidate in every slot, flipped Firewall and Kernel from
    sidegrade/inferior to UPGRADE and lifted the Router candidate +8.3 -> +22.8.
    Pass tier_cap=3 to reproduce pre-27-Jul projections.

    Note the calibration consequence: the cap was a systematic UNDER-projection
    that partly cancelled the contract-conservatism OVER-projection. With it
    gone, the ~5-point discount for contract conservatism matters MORE, not
    less — a §10.1 contract with attempt caps and a hard floor is deliberately
    less ambitious than this plan.

    The uncapping argument above was defended at the time on the grounds that
    reliance on interpolated ladder points was "unchanged at 43/50". That
    counted interpolated points without checking their BIAS, and the bias is
    the whole problem: deep tiers advance ~1.263x per step, not the ~1.4x
    fitted on shallow tiers. `score` uses the measured deep median;
    `score_low` re-values the SAME plan at the p25 deep step
    (`deep_step_low`). A candidate whose verdict does not survive `score_low`
    is resting on extrapolation, not on evidence — check `deep_reliance`,
    which counts planned promotions into tiers the ladder has never observed.

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
            cur, m1 = ladder_value(ladder, tier, deep_step)
            nxt, m2 = ladder_value(ladder, tier - 1, deep_step)
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

    # projected totals, valued twice: at the median deep step and at the p25
    # deep step, so the verdict carries the ladder's own extrapolation spread
    totals, totals_low = {}, {}
    def add(label, etype, value, value_low=None):
        for target, v in ((totals, value),
                          (totals_low, value if value_low is None else value_low)):
            pct, flat = target.get(label, (0.0, 0.0))
            if etype == "flat_add":
                flat += v
            else:
                pct += v
            target[label] = (pct, flat)

    implicit = item.get("implicit_info")
    if implicit:
        add(stat_label(implicit.get("stat_type") or "?"),
            implicit.get("effect_type"), implicit.get("value", 0))
    any_estimated, deep_reliance = False, 0
    for entry in state:
        affix = entry["affix"]
        for e in affix.get("effects") or []:
            label = stat_label(e.get("resource") or "?")
            value_low = None
            if entry["up"]:
                key = (affix.get("affix_id"), e.get("resource"), e.get("type"))
                ladder = ladders.get(key)
                if ladder:
                    norm, measured = ladder_value(ladder, entry["tier"], deep_step)
                    low, _ = ladder_value(ladder, entry["tier"], deep_step_low)
                    any_estimated = any_estimated or not measured
                    if not measured and entry["tier"] <= DEEP_TIER:
                        deep_reliance += 1
                    scale = (flat_scale(ilvl) if e.get("type") == "flat_add"
                             else mult_scale(ilvl))
                    value = norm * scale
                    value_low = low * scale
                else:
                    value = e.get("value", 0)
            else:
                value = e.get("value", 0)
            add(label, e.get("type"), value * (1 + compile_pct),
                None if value_low is None else value_low * (1 + compile_pct))

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
        "totals_low": totals_low,
        "score": weighted_score(totals),
        "score_low": weighted_score(totals_low),
        "deep_reliance": deep_reliance,   # promotions into unobserved deep tiers
        "estimated": any_estimated,
    }


# ---- Homelab and hardware (lazy bindings; schema notes in
# docs/game-client-internals.md). These read capture values only; costs and
# gates always come from the capture, never re-derived. -----------------------

RESOURCE_SHORT = {
    "credits": "cr", "chips": "chips", "hackcoin": "hc",
    "snippets": "snip", "cycles": "cyc", "hashes": "hash", "packets": "pkt",
}


def score_tiers(item, ladders, tiers, stability_left, deep_step=TIER_STEP_DEEP):
    """Weighted score of `item` with affixes forced to `tiers` and a Compile.

    `tiers` maps affix display name -> target tier; affixes absent from it keep
    their current tier and roll. Promoted affixes are valued at the target
    tier MIDPOINT (roll is lost on promotion, crafting.md §12.2). Compile adds
    0.5% per remaining Stability to every explicit affix.

    Companion to `plan_craft`: that one CHOOSES a plan greedily, this one
    PRICES a plan you specify -- which is what `simulate_contract` needs to
    value the many partial outcomes a real contract actually produces.
    """
    ilvl = item.get("item_level") or 0
    compile_pct = 0.005 * max(stability_left, 0.0)
    totals = {}

    def add_effect(label, etype, value):
        pct, flat = totals.get(label, (0.0, 0.0))
        if etype == "flat_add":
            flat += value
        else:
            pct += value
        totals[label] = (pct, flat)

    implicit = item.get("implicit_info")
    if implicit:                      # implicit is NOT compiled (22 Jul)
        add_effect(stat_label(implicit.get("stat_type") or "?"),
                   implicit.get("effect_type"), implicit.get("value", 0))
    for side in ("prefixes", "suffixes"):
        for affix in item.get(side) or []:
            target = tiers.get(affix.get("name"))
            promoted = target is not None and target != affix.get("tier")
            for e in affix.get("effects") or []:
                label = stat_label(e.get("resource") or "?")
                if promoted:
                    key = (affix.get("affix_id"), e.get("resource"),
                           e.get("type"))
                    ladder = ladders.get(key)
                    if ladder:
                        norm, _ = ladder_value(ladder, target, deep_step)
                        scale = (flat_scale(ilvl) if e.get("type") == "flat_add"
                                 else mult_scale(ilvl))
                        value = norm * scale
                    else:
                        value = e.get("value", 0)
                else:
                    value = e.get("value", 0)
                add_effect(label, e.get("type"), value * (1 + compile_pct))
    return weighted_score(totals)


def simulate_contract(item, ladders, phases, floor=COMPILE_FLOOR, preserve=0.0,
                      trials=20000, seed=1, baseline=None):
    """Monte-Carlo a §10.1 craft contract. Returns the OUTCOME DISTRIBUTION.

    `phases` is [(affix display name, target tier), ...] IN EXECUTION ORDER.
    Each promotion succeeds with chance tier/10; a failure costs 1 Stability
    unless Snapshot Backups preserves it. The run stops when the next attempt
    would break the Compile `floor`, so partial contracts are priced the way
    they actually happen -- including the fact that a run which stalls early
    also SPENDS less and therefore keeps more Compile.

    Why this exists (27 Jul 2026): the standing practice was to take
    `plan_craft`'s optimal-plan ceiling and subtract a flat ~5 points for
    "contract conservatism". On the Aegisbound Driver that heuristic said
    +9.1 - 5 = +4.1, a sidegrade, and the craft was held. Simulating the same
    contract said mean +8.4, median +9.6, p10 +6.1, **P(delta > +5) = 90.8%**
    -- and it was approved and realized +16.7. A blanket discount cannot see
    that the phases are not separable (Stability spent cuts Compile, which
    multiplies everything, so each phase alone is worth far less than in
    combination) nor that the downside is bounded. Prefer this to the
    discount whenever the decision is close.

    `baseline` defaults to the equipped item's score if you pass one; results
    are expressed as deltas against it.
    """
    rng = random.Random(seed)
    start = {a.get("name"): a.get("tier")
             for side in ("prefixes", "suffixes")
             for a in item.get(side) or []}
    stability = item.get("stability") or 0
    budget = stability - floor
    results, completed = [], 0
    for _ in range(trials):
        spent, tiers = 0.0, dict(start)
        finished = True
        for name, target in phases:
            tier = start.get(name)
            if tier is None:
                continue
            while tier > target:
                won = False
                while spent + 1 <= budget:
                    spent += 1                      # the attempt itself
                    if rng.random() < tier / 10.0:
                        won = True
                        break
                    if rng.random() < preserve:     # failure refunded
                        spent -= 1
                if not won:
                    finished = False
                    break
                tier -= 1
                tiers[name] = tier
            if not finished:
                break
        completed += finished
        results.append(score_tiers(item, ladders, tiers,
                                   max(stability - spent, 0.0)))
    results.sort()
    if baseline is not None:
        results = [r - baseline for r in results]
    n = len(results)
    return {
        "mean": sum(results) / n,
        "median": results[n // 2],
        "p10": results[n // 10],
        "p90": results[(9 * n) // 10],
        "min": results[0],
        "max": results[-1],
        "p_upgrade": sum(1 for r in results if r > UPGRADE_BAND) / n,
        "p_positive": sum(1 for r in results if r > 0) / n,
        "p_complete": completed / trials,
        "trials": trials,
    }


def best_contract_order(item, ladders, phases, **kw):
    """[(order, sim)] over every phase permutation, best P(upgrade) first.

    Order is not cosmetic. On the Aegisbound Driver the best ordering scored
    P(>+5) 90.8% and the worst 81.0% on identical phases -- an expensive
    single low-probability step belongs LAST, where it absorbs whatever
    Stability the earlier phases left rather than starving them.
    """
    out = [(order, simulate_contract(item, ladders, list(order), **kw))
           for order in itertools.permutations(phases)]
    out.sort(key=lambda r: (-r[1]["p_upgrade"], -r[1]["mean"]))
    return out


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
    # Every purchasable carries the install (UI section) it lives under -- an
    # upgrade name alone still means hunting through panels to find it.
    installs = definitions.get("installs") or []
    section_names = {d.get("type"): d.get("name") for d in
                     (installs if isinstance(installs, list) else installs.values())}
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
            "section": section_names.get(u["install"], u["install"]),
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


def chip_budget(capture):
    """(spendable, free, locked) chips, preferring the live `currentPlayer`.

    `hardwareInfo.chips` is a panel snapshot and understates the balance
    whenever the Hardware tab was opened before the capture click -- 37,443 vs
    a live 44,582 on 27 Jul 2026, a 19% under-plan. `locked_resources` exists
    only on the panel, so that half stays panel-sourced (it changes only on a
    reset, so it cannot drift the same way).
    """
    hw = hardware_state(capture) or {}
    player = capture["state"].get("currentPlayer") or {}
    free = player.get("chips")
    if free is None:
        free = hw.get("chips") or 0
    locked = (hw.get("locked_resources") or {}).get("chips") or 0
    return free + locked, free, locked


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
# a hardwareInfo block reporting a credit balance 3.5B out of date). Three
# independent detectors, because only homelabInfo carries a server clock.
#
# The third is the strongest and the only one with a game-provided ground truth:
# `currentPlayer` is a live binding, so any currency a panel also reports must
# match it. Added 27 Jul 2026 after the two clock/credit detectors both passed a
# hardwareInfo block whose chip balance was 16% low (37,443 vs a live 44,582) --
# credits had drifted only 0.26%, under the cross-panel tolerance, because
# credits are huge and chips are small. Cross-panel agreement proves nothing
# when both panels were read at the same stale moment.

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


# Currencies a lazy panel snapshots that `currentPlayer` also holds live.
# Chips are the sensitive probe: they accrue continuously from combat drops and
# the balance is small, so a stale panel shows percent-level drift while credits
# (11 figures, spent in lumps) stay inside any sane tolerance.
PANEL_LIVE_CURRENCIES = ("chips", "hackcoin", "credits")


def panel_currency_drift(capture, tolerance=0.01, min_abs=1):
    """[(section, currency, panel_value, live_value)] where a panel disagrees.

    `currentPlayer` is live at capture time; a lazy panel holds whatever the
    game tab last read. Any gap beyond `tolerance` (relative) and `min_abs`
    (absolute) means the panel is stale, regardless of what its clock says.
    """
    state = capture["state"]
    player = state.get("currentPlayer") or {}
    rows = []
    for section in ("homelabInfo", "hardwareInfo"):
        info = state.get(section) or {}
        if not info:
            continue
        for currency in PANEL_LIVE_CURRENCIES:
            panel = info.get(currency)
            live = player.get(currency)
            if panel is None or live is None:
                continue
            gap = abs(panel - live)
            if gap >= min_abs and gap > tolerance * max(abs(live), 1):
                rows.append((section, currency, panel, live))
    return rows


def stale_panels(capture, max_age_s=300, credit_tolerance=0.005,
                 drift_tolerance=0.01):
    """Sections that look stale, as [(section, reason)].

    Three detectors, strongest last: the panel's own server clock (homelabInfo
    only), cross-panel credit disagreement, and disagreement with the live
    `currentPlayer` currencies. One reason per section -- the worst one.
    """
    rows = panel_freshness(capture)
    credits = [c for _, _, c in rows if c]
    drift = {}
    for section, currency, panel, live in panel_currency_drift(
            capture, tolerance=drift_tolerance):
        pct = (panel - live) / max(abs(live), 1) * 100
        # keep the largest relative gap per section -- it is the clearest signal
        if abs(pct) > abs(drift.get(section, (0, ""))[0]):
            drift[section] = (pct, f"reports {panel:,.0f} {currency} vs a live "
                                   f"{live:,.0f} ({pct:+.0f}%)")
    worst = []
    for section, age, credit in rows:
        if age is not None and age > max_age_s:
            worst.append((section, f"panel data {age:,.0f}s older than capture"))
        elif section in drift:
            worst.append((section, drift[section][1]))
        elif credits and credit and max(credits) - min(credits) > \
                credit_tolerance * max(credits) and credit != min(credits):
            worst.append((section, f"reports {credit:,.0f} credits vs "
                                   f"{min(credits):,.0f} elsewhere"))
    return worst


# ---- Capture freshness vs the stream ledger --------------------------------
# `stale_panels` only ever compares a capture against ITSELF, so a capture whose
# panels all agree reads as clean no matter how old the whole file is. The
# auto-stream keeps running after the last capture click, which makes its newest
# `stats` record a live ground truth for the capture as a whole.
#
# Added 27 Jul 2026 after the audit passed a 19:54Z capture as "44,582 chips
# unspent" while the 20:44Z stream record showed 4,140 -- the ECC Memory buy had
# already been made an hour earlier, and every hardware number in the advisory
# was about to be re-derived from a spent balance. The capture was internally
# consistent; only the ledger knew.

# Scalars the stream's `stats` record and `currentPlayer` both carry.
STREAM_LIVE_FIELDS = ("chips", "hackcoin", "credits", "hack_level",
                      "current_zone")
# Discrete counters where a relative tolerance is meaningless -- 1,054 -> 1,058
# hack levels is four levels of scaling, not a 0.4% rounding wobble.
STREAM_EXACT_FIELDS = {"hack_level", "current_zone"}


def latest_stream_player(before_ms=None):
    """(seen_ms, player) of the newest ledger `stats` record, or (None, None)."""
    best_ms, best = None, None
    for record in stream_records():
        if record.get("kind") != "stats":
            continue
        ms, player = record.get("seen_ms"), record.get("player") or {}
        if ms is None or not player:
            continue
        if before_ms is not None and ms > before_ms:
            continue
        if best_ms is None or ms > best_ms:
            best_ms, best = ms, player
    return best_ms, best


def captured_ms(capture):
    stamp = capture.get("capturedAt")
    if not stamp:
        return None
    return datetime.fromisoformat(
        stamp.replace("Z", "+00:00")).timestamp() * 1000


def measured_credits_per_hour(max_gap_s=300):
    """Credits/hr from the ledger's own fight rewards, or None.

    Gap-aware, and it has to be: the ledger spans six days of wall clock but
    only ~13 hours of play, so dividing total rewards by (last - first) reports
    ~0.8M/hr against a true ~10M/hr. Same trap `fight_cadence` documents -- a
    ledger timestamp range is not playing time. Elapsed accrues only across
    consecutive fights less than `max_gap_s` apart (the stream polls every
    150 s, so 300 s spans a normal poll without spanning a closed browser).
    """
    rows, seen = [], set()
    for record in stream_records():
        if record.get("kind") != "fight":
            continue
        key = tuple(record.get("key") or ())
        if key in seen:
            continue
        seen.add(key)
        ms = record.get("seen_ms")
        if ms:
            rows.append((ms, (record.get("fight") or {}).get("credits_gained") or 0))
    rows.sort()
    total, seconds, prev = 0.0, 0.0, None
    for ms, credits in rows:
        total += credits
        if prev is not None and (ms - prev) / 1000 <= max_gap_s:
            seconds += (ms - prev) / 1000
        prev = ms
    return (total / (seconds / 3600)) if seconds > 600 else None


# ---- Assumption register --------------------------------------------------
# Every defect in this workspace so far has been an INHERITED NUMBER: written
# once, plausible in output forever after, and load-bearing for everything
# downstream. The T3 tier cap, the zone transition cost, "attack speed -> fights
# per hour", `Corrupt = 0.6`, "credits are unlimited" and `floor = 8` all failed
# the same way, and the standing lesson kept being recorded as prose to remember
# rather than as a check that runs. This is the check that runs.
#
# `provenance` is the only field that matters:
#   measured  - fitted or tested against game data, with the test named
#   asserted  - someone's reasonable guess; never tested
#   inherited - asserted, and now depended on by code that predates any test
#   supplied  - given by the player; true when stated, not a game constant
#
# A `check` runs live and reports drift. Constants with no possible check are
# not thereby fine -- they are the ones to be most suspicious of.

def _chk_stat_families(cap):
    bad = validate_stat_totals(cap)
    return ("OK", "reproduces every stat in statsBreakdown") if not bad else \
        ("FAIL", f"{len(bad)} stat(s) mismatch: {[b[0] for b in bad]}")


def _chk_tier_steps(cap):
    shallow, deep = fit_tier_steps(cap, ladders=tier_ladders_archive())
    drift = max(abs(shallow - TIER_STEP_SHALLOW), abs(deep - TIER_STEP_DEEP))
    return (("OK" if drift < 0.02 else "DRIFT"),
            f"archive refit {shallow:.3f}/{deep:.3f} vs constants "
            f"{TIER_STEP_SHALLOW:.3f}/{TIER_STEP_DEEP:.3f}")


def _chk_hardware_curve(cap):
    hw = hardware_state(cap)
    if not hw:
        return ("SKIP", "no hardwareInfo in this capture")
    _a, _p, spread = hardware_cost_curve(hw)
    return (("OK" if spread < 1.05 else "DRIFT"),
            f"single-family fit spread {spread:.3f} (want < 1.05); the whole-"
            f"build total self-checked to +1.0% vs the game's reset refund")


def _chk_cadence(cap):
    rows = fight_cadence()
    if not rows:
        return ("SKIP", "no death records in the ledger")
    values = sorted(s for _ms, s in rows)
    mid = values[len(values) // 2]
    return (("OK" if abs(mid - 4.872) < 0.15 else "DRIFT"),
            f"n={len(values)} median {mid:.3f} s/fight vs recorded 4.872")


def _chk_credits_hr(cap):
    rate = measured_credits_per_hour()
    if rate is None:
        return ("SKIP", "no fight rewards in the ledger")
    return (("OK" if abs(rate - CREDITS_PER_HOUR) / CREDITS_PER_HOUR < 0.35
             else "DRIFT"),
            f"ledger says {rate / 1e6:.1f}M/hr vs constant "
            f"{CREDITS_PER_HOUR / 1e6:.0f}M/hr")


def assumptions():
    """[(name, value, provenance, basis, validated_on, check)] — the register.

    Ordered most-suspect first: anything `inherited` or `asserted`, then
    `supplied`, then `measured`.
    """
    w, f = CRAFT_WEIGHTS_PCT, CRAFT_WEIGHTS_FLAT
    rows = [
        # --- planning weights: a bottleneck heuristic, not a game formula ---
        ("CRAFT_WEIGHTS_PCT[Acc]", w["Acc"], "asserted",
         "CHALLENGED and now actionable: cutting Accuracy 7,595 -> 7,265 "
         "(-4.35%) produced NO hit-rate loss over 8,195 attacks at matched "
         "streak band. Left unchanged only because driver-ab-2026-07-27 was "
         "mid-flight; that A/B closed 28 Jul, so this weight is free to move "
         "and is probably far too high", "27 Jul 2026 (falsified)", None),
        ("CRAFT_WEIGHTS_PCT[AtkSpd]", w["AtkSpd"], "asserted",
         "right number, wrong reason: buys NO extra fights/hour (cadence is a "
         "fixed 4.872 s tick); pays -2% to -5% rounds per fight, i.e. it is a "
         "mitigation stat", "27 Jul 2026 (rationale corrected)", None),
        ("CRAFT_WEIGHTS_FLAT[Corrupt]", f["Corrupt"], "measured",
         "~0.5% of output per point in the deep streak bands -- HALF its "
         "stated rationale -- and NOT LINEAR. Fitted range is 12-25 points; "
         "do not apply above ~25 (two candidates scored as upgrades purely on "
         "extrapolation to 57.8)", "28 Jul 2026", None),
        ("CRAFT_WEIGHTS_FLAT[Regen]", f["Regen"], "asserted",
         "DIRECTION is measured -- regeneration moved the death ceiling twice "
         "(+20.5 streaks on +35.3% realized prg; +7.0 on the Shell) -- but the "
         "0.6 scalar has never been fitted, and 28 Jul showed it is NOT FLAT: "
         "a +29.7% listed buy realized +0.4% / +4.7% / +11.5% of prg/round at "
         "streak bands 60-85 / 86-105 / 106-130. Realization rises with "
         "depletion (overheal capping, open-questions.md), so a flat weight "
         "over-prices regen shallow and a second large buy will realize less "
         "again", "direction only; magnitude falsified as flat 28 Jul", None),
        ("CRAFT_WEIGHTS_PCT[Def]", w["Def"], "asserted",
         "first isolated read 28 Jul: gross damage/round at streak 106-130 "
         "went 349.0 -> 368.6 (+5.6%) against Defense -6.05%, i.e. roughly 1:1 "
         "elasticity -- but n=35 fights, one window, and Evasion +4.4% pushed "
         "the other way. Every earlier Defense change arrived bundled with "
         "regen or barrier", "directional only, 28 Jul 2026", None),
        ("CRAFT_WEIGHTS_PCT[Eva]", w["Eva"], "asserted",
         "only ever moved bundled with Regen (Citadel Shell)", None, None),
        ("CRAFT_WEIGHTS_PCT[AtkDmg]", w["AtkDmg"], "asserted", "", None, None),
        ("CRAFT_WEIGHTS_PCT[CritCh]", w["CritCh"], "asserted", "", None, None),
        ("CRAFT_WEIGHTS_PCT[MaxHP]", w["MaxHP"], "asserted",
         "guardrail says Max HP is a buffer, not mitigation or recovery",
         None, None),
        ("CRAFT_WEIGHTS_PCT[CritDmg]", w["CritDmg"], "asserted", "", None, None),
        ("CRAFT_WEIGHTS_FLAT[ArmorPen]", f["ArmorPen"], "inherited",
         "never tested; the multiplicand was 0 until 28 Jul, so it has never "
         "even been exercised", None, None),
        ("CRAFT_WEIGHTS_FLAT[Thorns]", f["Thorns"], "inherited",
         "never tested", None, None),
        ("CRAFT_WEIGHTS_FLAT[Barrier]", f["Barrier"], "inherited",
         "never tested; Barrier arrived bundled in the 27 Jul package",
         None, None),
        # --- verdict bands ---
        ("UPGRADE_BAND", UPGRADE_BAND, "inherited",
         "STALE: calibrated 22 Jul against the Vital Driver under the old "
         "Compile floor of 8. Lowering the floor to 2 raised every projection "
         "~11-13 points, so this threshold no longer means what it did. "
         "Re-derive from crafts executed after 28 Jul", "22 Jul 2026", None),
        ("INFERIOR_BAND", INFERIOR_BAND, "inherited",
         "same calibration as UPGRADE_BAND, same staleness", "22 Jul 2026",
         None),
        # --- supplied ---
        ("HACKCOIN_CREDIT_RATE", HACKCOIN_CREDIT_RATE, "supplied",
         "player-supplied exchange rate, not derivable from any capture. An "
         "exchange rate is NOT a game constant -- re-confirm before leaning "
         "on it", "28 Jul 2026", None),
        # --- measured, with live checks ---
        ("COMPILE_FLOOR", COMPILE_FLOOR, "measured",
         "swept 0/2/4/6/8/10 over three live candidates: lower better on "
         "mean, median, p10 AND p90 in every case. 2 rather than 0 keeps one "
         "Refactor in hand", "28 Jul 2026", None),
        ("plan_craft tier_cap default", 1, "measured",
         "was 3 and untested, which excluded the two best steps on the "
         "ladder; gain per expected Stability point peaks at T3->T2",
         "27 Jul 2026", None),
        ("CREDITS_PER_HOUR", CREDITS_PER_HOUR, "measured",
         "fight rewards only; homelab jobs outspend it ~10x, and contracts "
         "add lumpy income on top. The live check pools the whole ledger and "
         "so runs BEHIND the current rate (6.6M/hr on 23 Jul, 9.6M on 27 Jul, "
         "13.1M on 28 Jul as the build deepened) -- do not 'correct' the "
         "constant down to the pooled figure", "28 Jul 2026", _chk_credits_hr),
        ("TIER_STEP_SHALLOW / _DEEP", f"{TIER_STEP_SHALLOW}/{TIER_STEP_DEEP}",
         "measured", "fitted archive-wide and re-fitted on every run by "
         "fit_tier_steps, so it cannot rot as the inventory turns over",
         "27 Jul 2026", _chk_tier_steps),
        ("DEEP_TIER", DEEP_TIER, "measured",
         "the step is region-dependent; one constant 1.4 was fitted on "
         "shallow tiers only and over-projected a T6->T1 chase by 1.9x",
         "27 Jul 2026", None),
        ("fight cadence 4.872 s", 4.872, "measured",
         "from the game's own death clock, never the stream's poll interval",
         "27 Jul 2026", _chk_cadence),
        ("hardware cost curve", "A*L**p", "measured",
         "fitted live off next_cost and self-validates against the game's own "
         "reset refund", "27 Jul 2026", _chk_hardware_curve),
        ("stat_total stat families", "SCALING/DIRECT/economy", "measured",
         "self-validates against the game's reported totals for every stat",
         "27 Jul 2026", _chk_stat_families),
    ]
    order = {"inherited": 0, "asserted": 1, "supplied": 2, "measured": 3}
    return sorted(rows, key=lambda r: order.get(r[2], 9))


# ---- Prediction ledger ----------------------------------------------------
# The realized-vs-projected table lived in prose in crafting.md 13 for six
# days, which meant nobody could score it. The "~5-point contract-conservatism
# discount" and `UPGRADE_BAND` were both folklore derived by eyeballing it --
# and the discount points the WRONG WAY for the current planner (six of nine
# crafts over-realized). A model you cannot score is a model you cannot improve.
#
# `model` tags the planner era. Rows from different eras are NOT comparable:
# removing the T3 cap (27 Jul) and lowering COMPILE_FLOOR 8 -> 2 (28 Jul) each
# shifted projections by more than UPGRADE_BAND.
PREDICTIONS_PATH = ROOT / "data" / "predictions.jsonl"
CURRENT_MODEL = "uncapped+floor2+archive"


def prediction_records(path=PREDICTIONS_PATH):
    """[record] from the prediction ledger, oldest first."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def record_prediction(item, slot, projected, realized=None, p10=None, p90=None,
                      p_upgrade=None, date=None, model=CURRENT_MODEL, note="",
                      path=PREDICTIONS_PATH):
    """Append one prediction. Call at contract time, fill `realized` after."""
    row = {"date": date, "item": item, "slot": slot, "projected": projected,
           "p10": p10, "p90": p90, "p_upgrade": p_upgrade,
           "realized": realized, "model": model, "note": note}
    with path.open("a") as handle:
        handle.write(json.dumps(row) + "\n")
    return row


def calibration(records=None):
    """Per-model-era scoring of the prediction ledger.

    Returns {model: {...}} with signed bias (realized - projected), MAE,
    verdict agreement against UPGRADE_BAND, and interval coverage where a
    distribution was recorded. Coverage is the number that matters once
    `simulate_contract` is the standard instrument: an 80% p10-p90 interval
    should contain the truth ~80% of the time, and if it does not, every
    P(upgrade) the tool prints is miscalibrated by a knowable amount.
    """
    rows = [r for r in (records or prediction_records())
            if r.get("realized") is not None and r.get("projected") is not None]
    out = {}
    for row in rows:
        era = out.setdefault(row.get("model", "?"),
                             {"n": 0, "errors": [], "agree": 0, "graded": 0,
                              "in_interval": 0, "with_interval": 0,
                              "items": []})
        era["n"] += 1
        error = row["realized"] - row["projected"]
        era["errors"].append(error)
        era["items"].append((row["item"], row["projected"], row["realized"],
                             error))
        # did the UPGRADE/not verdict survive realization?
        era["graded"] += 1
        if (row["projected"] > UPGRADE_BAND) == (row["realized"] > UPGRADE_BAND):
            era["agree"] += 1
        if row.get("p10") is not None and row.get("p90") is not None:
            era["with_interval"] += 1
            if row["p10"] <= row["realized"] <= row["p90"]:
                era["in_interval"] += 1
    for era in out.values():
        errors = era["errors"]
        era["bias"] = sum(errors) / len(errors)
        era["mae"] = sum(abs(e) for e in errors) / len(errors)
        era["over"] = sum(1 for e in errors if e > 0)
    return out


def score_contributions(projected, equipped_totals):
    """[(value, label)] — which stat each point of a ceiling Δ came from.

    A ceiling Δ is a scalar and a scalar hides which weight is carrying it. On
    28 Jul 2026 the top two candidates on the board scored +22.1 and +16.2, and
    a decomposition showed +23.1 and +17.6 of that was Corruption alone — a
    weight fitted on one fight and extrapolated 2.3x past its observed range.
    Both were sidegrades once that term was removed. Nothing in the output said
    so, because the output was one number.

    Read it against `ih.py assumptions`: a Δ carried by an `asserted` or
    `inherited` weight is a hypothesis, not a verdict.
    """
    out = []
    for label in set(projected) | set(equipped_totals):
        p_pct, p_flat = projected.get(label, (0.0, 0.0))
        c_pct, c_flat = equipped_totals.get(label, (0.0, 0.0))
        value = ((p_pct - c_pct) * 100 * CRAFT_WEIGHTS_PCT.get(label, 0.0)
                 + (p_flat - c_flat) * CRAFT_WEIGHTS_FLAT.get(label, 0.0))
        if abs(value) > 0.05:
            out.append((value, label))
    return sorted(out, reverse=True)


# Weights whose value is known to be unreliable, so a Δ leaning on one gets
# called out at the point of use rather than in a doc nobody re-reads.
SUSPECT_WEIGHTS = {
    "Corrupt": "fitted on n=1 at 12 points; ~2x too generous and NON-LINEAR "
               "— invalid above ~25 points",
    "Acc": "measured saturated 27 Jul (-4.35% Acc, zero hit-rate loss)",
}


def suspect_share(contributions):
    """(suspect_total, [labels]) for the part of a Δ resting on bad weights."""
    rows = [(v, l) for v, l in contributions if l in SUSPECT_WEIGHTS]
    return sum(v for v, _ in rows), [l for _, l in rows]


def contract_board(capture):
    """Daily contract board state: reset clock, live progress, unclaimed pay.

    Added 28 Jul 2026 after the sweep missed it. The board resets at a fixed
    UTC hour and **unfinished progress is destroyed** -- and contracts are the
    game's only observed repeatable hackcoin source (1-5 hc each plus a
    board-clear bonus), which is the scarcest currency in the model. Nothing
    else in the capture surfaces that deadline.

    Returns {reset_ms, hours_left, active, unclaimed, clear_bonus,
    clear_bonus_claimed} where `active` is the in-progress contract (or None)
    and `unclaimed` is [completed but not claimed].
    """
    board = ((capture["state"].get("currentPlayer") or {}).get("contracts")
             or {})
    rows = board.get("contracts") or []
    reset_ms = board.get("next_reset_at_ms")
    now = captured_ms(capture)
    active_id = board.get("active_contract_id")
    active = next((c for c in rows if c.get("id") == active_id), None)
    return {
        "reset_ms": reset_ms,
        "hours_left": ((reset_ms - now) / 3.6e6
                       if reset_ms and now else None),
        "active": active,
        "unclaimed": [c for c in rows
                      if c.get("completed") and not c.get("claimed")],
        "clear_bonus": board.get("clear_bonus_amount") or 0,
        "clear_bonus_claimed": bool(board.get("clear_bonus_claimed")),
    }


# Credit income, measured from the stream ledger rather than assumed.
CREDITS_PER_HOUR = 12e6

# Hackcoin sells for credits, so the credit balance is NOT the credit budget.
# Player-supplied rate, 28 Jul 2026. This single number reprices the whole
# game: at 8.33B/hc the credit half of every install is rounding error next to
# its hackcoin half (Hacking Simulator = 5B cr + 3 hc = 0.60 + 3.00 hc), so
# credits should be spent freely and HACKCOIN is the only real currency.
# Re-check it before leaning on it -- an exchange rate is not a game constant.
HACKCOIN_CREDIT_RATE = 8_332_642_927


def hackcoin_equivalent(cost, rate=HACKCOIN_CREDIT_RATE, resource_rate=2.0):
    """Total price of a cost dict in hackcoin, the actually-scarce currency.

    Gathering resources convert at ~`resource_rate` credits/unit on the
    marketplace (CLAUDE.md), credits convert at `rate` credits per hackcoin.
    """
    cost = cost or {}
    credits = (cost.get("credits") or 0) + resource_rate * sum(
        cost.get(r) or 0 for r in GATHER_RESOURCES)
    return credits / rate + (cost.get("hackcoin") or 0)


def credit_runway(capture, per_hour=CREDITS_PER_HOUR,
                  rate=HACKCOIN_CREDIT_RATE):
    """(balance, hours_of_income_to_afford, [(name, credits, hackcoin)]).

    Lists homelab installs not yet affordable, with how long fight income alone
    would take to cover the credit shortfall. `balance` counts hackcoin at
    `rate`, because the player sells it: a 5.7B credit balance next to 28
    hackcoin is really a ~239B budget, and treating it as 5.7B produced exactly
    one wrong recommendation (deferring the Hacking Simulator, 28 Jul 2026).
    Pass rate=None to score the raw credit balance instead.
    """
    player = capture["state"].get("currentPlayer") or {}
    balance = player.get("credits") or 0
    if rate:
        balance += (player.get("hackcoin") or 0) * rate
    homelab, definitions, _ = homelab_state(capture)
    installed = (homelab or {}).get("installed") or {}
    pending = []
    for d in definitions.get("installs") or []:
        if installed.get(d.get("type")):
            continue
        cost = d.get("cost") or {}
        pending.append((d.get("name"), cost.get("credits") or 0,
                        cost.get("hackcoin") or 0))
    short = sum(c for _, c, _ in pending) - balance
    return balance, (short / per_hour if short > 0 else 0.0), pending


def capture_stream_drift(capture, tolerance=0.01, min_abs=1):
    """(lag_seconds, [(field, capture_value, stream_value)]) vs the ledger.

    Returns (None, []) when the ledger holds nothing newer than the capture.
    `lag_seconds` is how far the capture trails the newest streamed state; the
    field list is what demonstrably changed since. An empty field list with a
    large lag still matters -- homelab job progress and hardware levels are not
    streamed, so they can only be assumed stale.
    """
    cap_ms = captured_ms(capture)
    stream_ms, player = latest_stream_player()
    if cap_ms is None or stream_ms is None or stream_ms <= cap_ms:
        return None, []
    live = capture["state"].get("currentPlayer") or {}
    changed = []
    for field in STREAM_LIVE_FIELDS:
        was, now = live.get(field), player.get(field)
        if was is None or now is None:
            continue
        if isinstance(was, str) or isinstance(now, str):
            if was != now:
                changed.append((field, was, now))
            continue
        gap = abs(now - was)
        if gap < min_abs:
            continue
        if field in STREAM_EXACT_FIELDS or gap > tolerance * max(abs(was), 1):
            changed.append((field, was, now))
    return (stream_ms - cap_ms) / 1000, changed


# ---- Stat composition (mechanics.md §13, formula-level) --------------------
# Hardware %, homelab % and equipment % share ONE additive pool. Four families
# differ only in what that pool multiplies. Membership is not guessable from the
# stat name -- always confirm with `validate_stat_totals` against the capture's
# own `total`, which is the ground truth. `attack_damage` sat outside all three
# families until 27 Jul 2026 and silently returned 0 (its real total is 2,050),
# which is exactly the stat the AtkDmg guardrail depends on.
SCALING_STATS = {"max_hp", "defense", "accuracy", "evasion",
                 "attack_damage", "post_combat_heal"}
DIRECT_STATS = {"attack_speed", "crit_chance", "crit_damage"}
# Economy stats (credits, cycles, hashes, packets, snippets) use a DIFFERENT
# schema: no `equipment_pct`/`level`, an `equipment` key instead. Most
# components sum on top of base, but two of them multiply the sum instead --
# see ECONOMY_MULT_KEYS. Detected by key, not by name, so a new economy stat is
# handled automatically.
ECONOMY_KEY = "equipment"
# Multiplicative, NOT additive, on top of the economy additive bracket:
#   total = (base + additive components) * (1 + participation) * (1 + cache)
# Confirmed formula-level 27 Jul 2026 against the game's own totals on the
# 21:07 capture -- all five economy stats reproduce to <1e-9 with this and to
# -11% .. -23% without it. Identifiable because the capture carries both a
# firewall_cache=0.15 case (the four gathering resources) and a
# firewall_cache=0 case (credits) against a constant participation_bonus=0.5;
# every additive reading of either term fails both. Regime: only these two
# values have been observed -- if a capture ever shows a different
# participation_bonus or firewall_cache, `validate_stat_totals` re-checks it.
ECONOMY_MULT_KEYS = ("participation_bonus", "firewall_cache")
# everything else in stats_breakdown is gear-flat (regeneration, corruption,
# thorns, damage_barrier, armor_penetration) -> pool multiplies equipment_flat.


def is_economy_breakdown(breakdown):
    """True for the additive multiplier schema (credits, cycles, ...)."""
    return ECONOMY_KEY in (breakdown or {})


def stat_pool(breakdown):
    """Additive pool multiplier for one stats_breakdown entry.

    For economy stats this is the additive bracket only -- the two
    ECONOMY_MULT_KEYS terms multiply it and are applied by `economy_multiplier`.
    """
    b = breakdown or {}
    if is_economy_breakdown(b):
        # every numeric component except the reported total and the
        # multiplicative terms is additive here; `flat`/`homelab_flat` are both
        # 0 in every capture so far, so their footing is unconfirmed -- revisit
        # if either ever goes non-zero.
        return sum(v for k, v in b.items()
                   if k != "total" and k not in ECONOMY_MULT_KEYS
                   and isinstance(v, (int, float)))
    return (1 + (b.get("equipment_pct") or 0)
            + (b.get("hardware") or 0) + (b.get("homelab") or 0))


def economy_multiplier(breakdown):
    """Product of the multiplicative economy terms; 1.0 for combat stats."""
    b = breakdown or {}
    if not is_economy_breakdown(b):
        return 1.0
    mult = 1.0
    for key in ECONOMY_MULT_KEYS:
        mult *= 1 + (b.get(key) or 0)
    return mult


def stat_total(breakdown, stat, d_equipment_pct=0.0, d_hardware=0.0,
               d_homelab=0.0, d_equipment_flat=0.0):
    """Recompute a stat under pool/flat deltas. Reproduces the live total at 0.

    Use this instead of re-deriving the arithmetic per analysis. Correctness is
    not assumed: `validate_stat_totals(capture)` checks every stat against the
    game's own reported `total` and is the check that caught `attack_damage`.
    """
    b = breakdown or {}
    pool = stat_pool(b) + d_equipment_pct + d_hardware + d_homelab
    if is_economy_breakdown(b):
        # deltas land inside the additive bracket, so they scale with it
        return pool * economy_multiplier(b)
    if stat in DIRECT_STATS:
        return (b.get("base") or 0) + pool - 1
    flat = (b.get("equipment_flat") or 0) + d_equipment_flat
    if stat in SCALING_STATS:
        return ((b.get("base") or 0) + (b.get("level") or 0) + flat) * pool
    return flat * pool


def validate_stat_totals(capture, tolerance=1e-6):
    """[(stat, reported, modelled)] where `stat_total` misses the game's total.

    Self-validation against a game-provided ground truth. An empty list means
    every stat in `statsBreakdown` is reproduced; anything returned is a stat
    whose family membership above is wrong, and any analysis touching it is
    unsound until fixed.
    """
    breakdowns = capture["state"].get("statsBreakdown") or {}
    bad = []
    for stat, b in sorted(breakdowns.items()):
        if not isinstance(b, dict) or "total" not in b:
            continue
        reported, modelled = b["total"], stat_total(b, stat)
        scale = max(abs(reported), 1e-9)
        if abs(modelled - reported) / scale > tolerance:
            bad.append((stat, reported, modelled))
    return bad


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

    def spend(lam):
        """Incremental chips to buy up to the lambda-optimal levels.

        Levels can never be reduced, so a track already above its optimum
        contributes zero rather than a refund. Solving without that clamp
        lets the optimiser "fund" purchases by notionally selling down
        over-levelled tracks — it returned a 108K-chip plan against a 37K
        budget before this was fixed.
        """
        total = 0.0
        for _n, _t, level, value in rows:
            if value <= 0:
                continue
            target = max(level, (value / lam) ** (1 / p))
            total += (hardware_cumulative(curve, target)
                      - hardware_cumulative(curve, level))
        return total

    lo, hi = 1e-9, 10.0
    for _ in range(300):                     # bisect the marginal-value line
        lam = (lo + hi) / 2
        lo, hi = (lam, hi) if spend(lam) > budget_chips else (lo, lam)
    lam = (lo + hi) / 2
    out = []
    for name, typ, level, value in rows:
        # floor, not round: rounding up a fractional optimum put the plan ~3%
        # over budget, and a plan you cannot afford is not a plan
        target = max(level, int((value / lam) ** (1 / p)) if value > 0 else 0)
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
    "segment_ms": 1785189000000,        # = equip; no mid-test segment declared
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
}

# Concluded experiments stay importable for retrospective analysis:
# experiment_status(SHELL_AB_2026_07_23).
ACTIVE_EXPERIMENT = FIREWALL_AB_2026_07_28


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


def fight_cadence(since_ms=None, zone="corporate_network", max_gap_s=900):
    """[(ended_at_ms, seconds_per_fight)] measured from the game's own clock.

    Elapsed between consecutive deaths divided by the fights between them
    (`streak_ended` + 1). Deaths carry a server `ended_at_ms`, so this is the
    only wall-clock measure in the toolkit that does not go through the
    auto-stream's 150 s polling interval -- pooling `seen_ms` gaps instead
    just re-measures the poll rate, which is how this was nearly got wrong.

    Measured 27 Jul 2026: **4.872 s/fight, sd 0.053, n=29 -> 739 fights/hour,
    invariant** across every loadout change that day, including a +9.9%
    Attack Speed equip that moved it 0%. See mechanics.md §14: fight cadence
    is a fixed real-time tick, so **attack speed is not income** -- it pays in
    rounds per fight, i.e. fewer enemy attacks per fight, i.e. mitigation.
    Anything claiming a stat buys "fights per hour" is wrong until this
    function says otherwise.
    """
    deaths = {}
    for record in stream_records():
        if record.get("kind") != "death":
            continue
        entry = record.get("death") or {}
        if entry.get("ended_at_ms"):
            deaths[entry["ended_at_ms"]] = entry
    out = []
    ordered = sorted(deaths.items())
    for (ms0, _prev), (ms1, entry) in zip(ordered, ordered[1:]):
        if since_ms is not None and ms1 < since_ms:
            continue
        if zone and entry.get("zone_id") != zone:
            continue
        gap = (ms1 - ms0) / 1000.0
        fights = (entry.get("streak_ended") or 0) + 1
        if 0 < gap <= max_gap_s and fights > 1:
            out.append((ms1, gap / fights))
    return out


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
        # `boundary_fight_id` splits the one capture that STRADDLES the equip:
        # fight ids are per-session, so within that session the id orders
        # fights either side of it. Optional -- when the equip was not caught
        # mid-session there is nothing to straddle, and capture time alone
        # segments correctly.
        boundary = exp.get("boundary_fight_id")
        same_session_as_equip = (boundary is not None and bool(ids)
                                 and max(ids) > boundary)
        for f in log:
            fid = f.get("id")
            if fid is None:
                continue
            if capture_pre:
                post = False
            elif same_session_as_equip:
                post = fid > boundary
            else:
                post = True  # session restarted after equip, or no boundary set
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


# Deaths now land at 113-120, so a ladder stopping at 105 misses the band
# where the run actually ends. 106-130 added 27 Jul 2026.
MECH_BRACKETS = ((24, 42), (60, 85), (86, 105), (106, 130))


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
                ph = sum(f["ph"] for f in sel)
                pm = sum(f["pm"] for f in sel)
                brackets[(lo, hi)] = {
                    "n": n,
                    "gross": sum(f["dmg"] for f in sel) / n,
                    "net": sum(f["dmg"] - f["rg"] - f["soak"]
                               for f in sel) / n,
                    "rounds": sum(f["rounds"] or 0 for f in sel) / n,
                    # hit rate MUST be compared within a bracket: enemy
                    # evasion scales with streak, so a pooled pre/post hit
                    # rate is confounded by streak composition alone. This
                    # is the comparison that falsified "Accuracy -4.35%
                    # costs ~1.7pp of hit rate" on 27 Jul 2026.
                    "ph": ph, "pm": pm,
                    "hit": ph / (ph + pm) if ph + pm else None,
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
