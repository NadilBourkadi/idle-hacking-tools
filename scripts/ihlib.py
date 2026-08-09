"""Shared helpers for querying Idle Hacking full-state captures.

Encodes the slot mapping and the fitted models from
docs/static-analysis-2026-07-22.md so analyses never re-derive them.
Used by ih.py; import directly for bespoke analysis.
"""

import hashlib
import itertools
import json
import math
import os
import random
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every on-disk location hangs off ONE overridable root. `IH_DATA_DIR` exists
# so tests can point at an empty tree: without it the suite silently read the
# developer's live captures and passed, while CI -- where `data/` is
# git-ignored and a clone has none -- failed on the same commit (7 Aug 2026).
# A test that can see ambient data is not testing what CI runs.
DATA_ROOT = Path(os.environ.get("IH_DATA_DIR") or (ROOT / "data"))
CAPTURES_DIR = DATA_ROOT / "captures"

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

# Affix-magnitude scaling laws. REFIT 7 Aug 2026 against the game's own
# `value_min`/`value_max` fields across the whole capture archive (138 flat and
# 645 percent affix/tier groups, ilvl 314-4767) -- see the register entries.
#
# These were inline literals until this refit, which is why the total
# registry test never saw them: it walks module-level bare numerics, and a
# constant living inside a function body is invisible to it. Same escape
# route ENEMY_LEVEL_GROWTH_PER_STREAK used until 6 Aug.
#
# Only OFFSET and EXPONENT are load-bearing. Every consumer normalises an
# observed value by scale(source_ilvl) and re-multiplies by scale(target_ilvl),
# so the REF denominators cancel in the ratio and are cosmetic (they set what
# `ih.py item` prints as "scale x...").
SCALE_PCT_OFFSET, SCALE_PCT_REF, SCALE_PCT_EXPONENT = 250, 1125, 0.4333
SCALE_FLAT_OFFSET, SCALE_FLAT_REF, SCALE_FLAT_EXPONENT = 250, 1021, 1.0


def scale_percent_value(item_level):
    """Percentage-affix magnitude relative to the ilvl-1000 reference."""
    return ((item_level + SCALE_PCT_OFFSET)
            / SCALE_PCT_REF) ** SCALE_PCT_EXPONENT


def scale_flat_value(item_level):
    """Flat-affix magnitude relative to reference.

    LINEAR in (ilvl + 250). The previous `((ilvl+100)/1021)**0.7849` was a
    power fit over a much narrower ilvl range and decayed badly above it:
    extrapolating from ilvl 445-2912 observations to the ilvl-4240 Kernel
    crafted on 7 Aug 2026 it under-predicted the game's own stated affix
    midpoint by 19.0%, against +0.6% for this law.
    """
    return ((item_level + SCALE_FLAT_OFFSET)
            / SCALE_FLAT_REF) ** SCALE_FLAT_EXPONENT


# The two fitted-cost helpers below have no CLI callers by design: they are
# part of the documented bespoke-analysis API (CLAUDE.md), kept for import
# from ad-hoc scripts pricing craft actions.
def stability_cost_multiplier(spent):
    """Credit-cost escalation per Stability spent (exact)."""
    return 1.03 ** spent


def base_cost_estimate(required_level):
    """Approximate crafting base cost (R^2 0.995)."""
    return 1.586 * required_level ** 1.765


# ---- Capture loading -------------------------------------------------------

def capture_paths():
    return sorted(CAPTURES_DIR.glob("idle-hacking-state-*.json"))


# Bounded parse cache: (path, mtime_ns, size) -> parsed dict, newest-last.
# `brief` loads the same ~2.5MB latest capture once per section without it.
# Eight entries ≈ 20MB ceiling; entries are SHARED — treat captures as
# read-only, same contract as the stream cache.
_CAPTURE_CACHE = {}
_CAPTURE_CACHE_MAX = 8


def load_capture(path=None):
    """Load a capture (latest by default). Returns (data, path)."""
    if path is None:
        paths = capture_paths()
        if not paths:
            # Library code raises real exceptions; the CLI boundary (ih.py
            # main) translates them to exit messages. SystemExit here poisoned
            # importers and was un-catchable by pytest (public-release audit).
            raise FileNotFoundError(
                f"no captures in {CAPTURES_DIR} — take one with the capture "
                f"panel (see README quickstart)")
        path = paths[-1]
    path = Path(path)
    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    if key not in _CAPTURE_CACHE:
        while len(_CAPTURE_CACHE) >= _CAPTURE_CACHE_MAX:
            _CAPTURE_CACHE.pop(next(iter(_CAPTURE_CACHE)))
        _CAPTURE_CACHE[key] = json.loads(path.read_text())
    return _CAPTURE_CACHE[key], path


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


def item_stat_totals(item):
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
        for label, (pct, flat) in item_stat_totals(item).items():
            mp, mf = merged.get(label, (0.0, 0.0))
            merged[label] = (mp + pct, mf + flat)
    return merged


def fmt_totals(totals, combat_only=True):
    parts = []
    labels = [label for label in COMBAT_ORDER if label in totals]
    if not combat_only:
        labels += sorted(label for label in totals
                         if label not in COMBAT_ORDER)
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
        f"scale x{scale_percent_value(item.get('item_level') or 0):.3f}",
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
# x mult/scale_flat_value(ilvl); verified to reproduce across items within ~1%).
# Tiers nobody owns are log-linearly interpolated between observed
# neighbours and marked "~" — a measurement gap, not a mechanic claim.

# Planning weights for scalar ranking ONLY — a strategy heuristic encoding
# the current bottleneck model (late-streak attrition: sustain + tempo, see
# docs/current-state.md), NOT a game formula. Retune when the bottleneck
# changes. Keys are display labels (STAT_LABELS values).
# NO WEIGHT MAY SIT IN A KNOWN-WRONG STATE. If a measurement shows a weight is
# wrong, re-fit it in the SAME session -- see PENDING_REFITS below and the
# "never defer a known defect" rule in CLAUDE.md. Leaving a measured-wrong
# weight in place because "it deserves its own change" silently corrupts every
# ranking computed until someone remembers; that happened with Barrier (0.02
# vs a measured 0.10, wrong for a week) and Acc (asserted 1.0 vs a measured
# 0.14, wrong for two days after it was first challenged).
#   Acc 0.14 -- MEASURED 29 Jul 2026, was 1.0. Within a fixed-Accuracy era
#     (n=2,674 fights, 174K attempts), hit rate against enemy effective_evasion
#     has slope 7.44pp per 1.0 of acc/eva ratio; at the working ratio ~2.1 a
#     +10% Accuracy buy is +1.56pp hit rate = ~+2.0% output = 0.197% per pp,
#     i.e. 0.7 x 0.197 = 0.14 on the AtkDmg scale. Accuracy is NOT saturated:
#     the 27 Jul "no hit-rate loss" test predicted -0.68pp against a +-0.9pp
#     95% CI on 8,195 attempts -- it was UNDERPOWERED, not null.
#   AtkSpd 0.9 -- the reason was wrong, the number may be right. Attack speed
#     buys NO extra fights per hour (cadence is a fixed real-time tick,
#     era-local value in FIGHT_CADENCE_S, mechanics.md §14); it pays by
#     shortening fights in ROUNDS (-2% to -5%
#     measured), which cuts enemy attacks per fight -- and rounds now matter
#     directly, because corruption is charged per round (mechanics.md §16).
CRAFT_WEIGHTS_PCT = {   # value per +1 percentage point
    # RE-FITTED 29 Jul 2026 from Software Profiler sweeps (mechanics.md §19).
    # Scale anchor: AtkDmg. A "+1%" AFFIX adds 1 point to that stat's shared
    # additive pool, so the STAT moves by 1/pool -- 0.686% for AtkDmg, whose
    # applied 0.7 therefore means "weight ~= % output-equivalent per +1% affix".
    # EVERY earlier weight was set without that conversion, which is why the
    # pool-heavy stats (Def pool 2.30, Eva pool 2.10) were the most inflated.
    "Def": 0.45, "Eva": 0.22, "Acc": 0.21, "AtkSpd": 0.56,
    "AtkDmg": 0.7, "CritCh": 0.7, "MaxHP": 0.5, "CritDmg": 0.22,
}
CRAFT_WEIGHTS_FLAT = {  # value per +1 flat point
    # Corrupt MEASURED 29 Jul 2026 (was 0.6, "deliberately conservative", and
    # separately mis-flagged as "~2x too generous" -- both wrong). `pcd` is the
    # PLAYER's corruption output (data-dictionary.md): across four eras with the
    # stat at 16.2-22.9 it is a stable 4.88-5.82 damage/round per point, i.e.
    # ~1.04% of the ~530/round output per point -> 0.7 x 1.04 = 0.7. Linear in
    # the FITTED RANGE 16-23 only; above ~25 remains extrapolation.
    "Regen": 0.6, "Corrupt": 1.0, "ArmorPen": 0.068,
    # Barrier REFIT 0.043 -> 0.0088 on 8 Aug 2026 by the dedicated CI/CD pair
    # (open-questions par.22 design, pre-registered predictions). 0.043 was a
    # correct measurement of the WRONG QUANTITY: +1 Barrier really is +1.0
    # HP/fight of absorption, but absorption does not convert into death-streak
    # depth at Regen's rate. Measured depth yield beta = 0.041 +- 0.024 streaks
    # per score point against Regen's 0.200, i.e. 0.20x, so the score weight is
    # scaled to match -- 0.043 x 0.20 = 0.0088. This is how the per-family
    # score->depth conversion gets applied: fold it into the weight, so summed
    # score stays depth-commensurate and the conversion stays 1.0 everywhere.
    # CAVEAT, and it is why the register keeps the interval: the pair rejects
    # "Barrier converts like Regen" at 6.6 sigma but sits only 1.7 sigma off
    # ZERO -- the 95% CI is 0.06x-0.44x Regen. The point estimate is used
    # because setting it to 0 would over-commit to the null just as 0.043
    # over-committed to Regen-parity.
    "Thorns": 0.13, "Barrier": 0.0088,
}

# ---------------------------------------------------------------------------
# PENDING REFITS -- the anti-deferral register.
#
# A constant belongs here the MOMENT evidence shows the applied value is wrong
# and it has not yet been corrected. It exists because the failure mode it
# guards against is invisible from the output: `potential` and `contract` keep
# printing clean-looking numbers computed from a value already known to be
# false, and nothing in the workflow ever surfaces it again.
#
# DO NOT ADD A ROW HERE TO AVOID FIXING SOMETHING. Fixing is the default and is
# nearly always cheap. A row is legitimate ONLY when the fix is genuinely
# blocked on data that does not exist yet, and it MUST carry an `unblock`
# naming the specific observation that resolves it. Anything else -- "deserves
# its own change", "would move live verdicts", "do it next session" -- is
# exactly the reasoning that left the Barrier weight at one fifth of its
# measured value for a week while every ranking in the workspace was wrong.
#
# Consumers (audit / potential / contract) print a banner while this register
# is non-empty. That is deliberate and should be annoying.
# Emptied 30 Jul 2026: the UPGRADE_BAND / INFERIOR_BAND row (opened 28 Jul)
# hit its unblock condition -- a third craft graded under uncapped+floor2+
# archive whose projection described the executed plan (Vital Payload of
# Striking, realized +64.7 vs projected +80.6) -- and both bands were
# re-derived to +/-16 the same session. See the bands' own provenance rows.
PENDING_REFITS = [
    # The weights are per-stat SCORE. Turning score into DEATH-STREAK DEPTH
    # needs a per-family conversion, and the two families measured so far
    # differ by ~4.6x: Regen ~5.0 score/streak (CI/CD pair, 6 Aug 2026) vs
    # Barrier >=23 score/streak (open-questions.md par.15 — a +44.0-score,
    # Barrier-carried Driver craft read -0.58 +- 1.03 simulated streaks AND
    # ~+1.9 +- 2 live). Any ranking that sums score ACROSS families therefore
    # over-weights Barrier-carried options, and `hardware_plan` does exactly
    # that: at the 7 Aug 2026 161K-chip balance it put 154K (96%) into Packet
    # Shield, the Barrier track, over ECC Memory (Regen) — a ranking that
    # inverts once score is converted to depth.
    # BARRIER ROW CLOSED 8 Aug 2026 — the 12-run Daemon pair (par.22) measured
    # beta_Barrier = 0.041 +- 0.024 against Regen's 0.200 and the weight was
    # refit 0.043 -> 0.0088 in the same change. That is what closing a row
    # looks like: the conversion is folded INTO the weight, so summed score
    # stays depth-commensurate and the conversion stays 1.0 everywhere.
    #
    # The same programme left ArmorPen suspect, so the register does not go
    # empty — it narrows to the one family that now has evidence against it.
    {
        "name": "CRAFT_WEIGHTS_FLAT[ArmorPen] (score -> depth conversion)",
        "applied": "0.068, i.e. converting at Regen's rate (beta 0.200)",
        "opened": "2026-08-08",
        "blocked_on": "the only ArmorPen measurement is the 8 Aug Analyzer "
                      "craft pair, where ArmorPen carries 81% of the delta "
                      "rather than all of it — beta reads 0.116-0.132 against "
                      "Regen's 0.200 (~0.6x), enough to call 0.068 wrong but "
                      "not enough to fit a replacement off one mixed bundle",
        "unblock": "a dedicated CI/CD pair on an ArmorPen-only lever, the "
                   "par.22 design applied to ArmorPen: 6 runs/arm, fit beta "
                   "after subtracting the other families. Cheap now that the "
                   "method is established — it shares a control arm with any "
                   "other pair run the same day (open-questions par.21)",
    },
]


def cohort_summary(rows, label="cohort", ms_key="seen_ms", item=None):
    """Print a cohort's OWN boundaries before any statistic is computed from it.

    Mandatory before segmenting the ledger -- see the "declare the cohort"
    rule in CLAUDE.md. On 29 Jul 2026 a post-craft cohort was selected by
    `17000 < max_hp < 18000` with no date bound; the 28 Jul loadout sat at
    max_hp 17,345-17,374, so a whole day of pre-craft fights was pooled into
    it. Two constants were "refined" from the result, published, and withdrawn.
    Printing min/max of the discriminating field plus the date range would have
    caught it in one line.

    `rows` are dicts carrying `ms_key` and optionally the fight/death payload
    under `item` (a key name) or at top level.
    """
    if not rows:
        print(f"  [{label}] EMPTY COHORT")
        return {}
    def _get(r, k):
        src = (r.get(item) or {}) if item else r
        return src.get(k, r.get(k))
    ms = [r.get(ms_key) for r in rows if r.get(ms_key)]
    hp = [v for v in (_get(r, "max_hp") for r in rows) if v]
    span = ""
    if ms:
        def f(x):
            return datetime.fromtimestamp(
                x / 1000, timezone.utc).strftime("%m-%d %H:%M")
        span = f"{f(min(ms))} .. {f(max(ms))}"
    out = {"n": len(rows), "span": span,
           "max_hp": (min(hp), max(hp)) if hp else None}
    print(f"  [{label}] n={len(rows)}  {span}"
          + (f"  max_hp {min(hp)}-{max(hp)}" if hp else ""))
    if hp and max(hp) - min(hp) > 0.05 * max(hp):
        print(f"  [{label}] WARNING: max_hp spans {100*(max(hp)-min(hp))/max(hp):.1f}%"
              f" — this cohort probably straddles a gear change")
    return out


def pending_refits():
    """Constants known to be wrong and not yet corrected. Should be empty."""
    return list(PENDING_REFITS)


def pending_refit_banner():
    """Warning lines for any command that consumes the planning weights."""
    if not PENDING_REFITS:
        return []
    out = [f"!! {len(PENDING_REFITS)} CONSTANT(S) KNOWN-WRONG AND "
           f"UNCORRECTED -- numbers below are computed from them:"]
    for r in PENDING_REFITS:
        out.append(f"   {r['name']}  (applied {r['applied']}, "
                   f"open since {r['opened']})")
        out.append(f"      blocked on: {r['blocked_on']}")
        out.append(f"      unblock by: {r['unblock']}")
    return out


# Verdict bands for ceiling-vs-equipped score deltas, calibrated against the
# realized Vital Driver craft (projected +3.9, realized -2): treat small
# positive deltas as noise/contract-shortfall, not upgrades.
# Re-derived 30 Jul 2026 from the three crafts graded under
# uncapped+floor2+archive (errors vs projection: +21.3, +56.8, +14.7).
# REVERTED 16 -> 5 on 31 Jul 2026: the -15.9 Payload error that set the band
# to 16 was a SCALE BUG, not a shortfall. The 30 Jul contract was recorded at
# the --deepen block's numbers, and that block called simulate_contract
# without `baseline` -- it printed ABSOLUTE post-craft scores as if they were
# deltas (proven 31 Jul: a deepen variant with the contract's own phases
# printed +128.1 against the contract's +38.4, difference exactly the equipped
# baseline 89.9). Corrected, the Payload projected +50.0/p10 +42.5/p90 +56.9
# and realized +64.7 -- error +14.7, ABOVE projection and above p90 like the
# other two grades. No negative in-era error exists, so the worst-shortfall
# method yields no band at all; ±5 (the pre-bug value, from the 22 Jul Vital
# Driver) is restored as a switching-cost indifference band pending the first
# genuine negative grade. Interval coverage 0/3, ALL misses above p90:
# simulate_contract underestimates -- its p10 has never been breached.
UPGRADE_BAND = 5.0   # delta > +5 -> genuine upgrade candidate
INFERIOR_BAND = -5.0  # delta < -5 -> inferior; between -> sidegrade

# Fight tick, from the game's own death clock -- NOT from the stream's poll
# interval, which measures the poller. Attack speed does not move it (a +9.9%
# AtkSpd equip changed it 0% within-window), but the tick is NOT one constant
# forever: daily medians era-stepped 4.873 -> 4.750 -> 4.788 -> 4.605 ->
# 4.641 -> 4.666 over 27 Jul-1 Aug (within-era sd ~0.01), mover unidentified
# -- not rounds/fight (r=0.42, and the most-rounds day sat at mid cadence).
# 4.65 is the 30 Jul-1 Aug era. `_chk_cadence` re-validates on a trailing
# window every run; when it fires DRIFT, re-read the recent medians.
FIGHT_CADENCE_S = 4.65

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
        for lo, hi in zip(tiers, tiers[1:], strict=False):
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


def weighted_score(totals, weights=None):
    """Scalar bottleneck score of a {label: (pct, flat)} totals dict.

    `weights` is an optional (pct_weights, flat_weights) pair; it defaults to
    the live CRAFT_WEIGHTS. Pass `suspect_free_weights()` to score a plan as if
    every flagged family were worth nothing.
    """
    pct_w, flat_w = weights or (CRAFT_WEIGHTS_PCT, CRAFT_WEIGHTS_FLAT)
    score = 0.0
    for label, (pct, flat) in totals.items():
        score += pct * 100 * pct_w.get(label, 0.0)
        score += flat * flat_w.get(label, 0.0)
    return score


def version_upgrade_expected_attempts(tier):
    """Expected Version-Upgrade attempts Tn -> T(n-1); chance = tier x 10%.

    ATTEMPTS, not Stability — the two diverge once Snapshot Backups is above
    level 0. Use this for a contract's attempt caps (what the player counts at
    the panel) and `version_upgrade_expected_stability` for budget arithmetic.
    """
    return 10.0 / tier


def version_upgrade_expected_stability(tier, preserve=0.0):
    """Expected Stability spent promoting Tn -> T(n-1).

    The success always costs 1; each failure costs 1 only when Snapshot
    Backups does not trigger. **The "success costs 1" half was CONFIRMED by the
    player 29 Jul 2026** after being registered as a blocker -- it had been an
    untested assumption carrying the whole Stability budget. Model A stands;
    the failure-only alternative is rejected. Homelab `tier_promotion_stability_preserve` is
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
                    scale = (scale_flat_value(ilvl) if e.get("type") == "flat_add"
                             else scale_percent_value(ilvl))
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


# Bounded: keyed by path-set signature, so an unbounded dict grows one full
# ladder table per distinct capture-set — i.e. one per capture that lands
# mid-process. Four signatures cover every real access pattern (audit fix).
_LADDER_ARCHIVE_CACHE = {}
_LADDER_ARCHIVE_CACHE_MAX = 4

# Malformed captures skipped by the last archive fit — (path, error) pairs.
# A truncated capture silently thins the ladders every craft verdict rests
# on, so the skip count must be visible: `audit` flags any non-empty value.
LADDER_FIT_SKIPPED = []


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
    LADDER_FIT_SKIPPED.clear()
    for path in paths:
        try:
            _collect_ladder_obs(json.loads(path.read_text()), raw)
        except (OSError, ValueError, KeyError) as error:
            # a malformed capture must not blind the fit -- but the skip must
            # not be silent either: it thins the evidence under every verdict
            LADDER_FIT_SKIPPED.append((str(path), repr(error)))
    ladders = {key: {t: sum(v) / len(v) for t, v in tiers.items()}
               for key, tiers in raw.items()}
    while len(_LADDER_ARCHIVE_CACHE) >= _LADDER_ARCHIVE_CACHE_MAX:
        _LADDER_ARCHIVE_CACHE.pop(next(iter(_LADDER_ARCHIVE_CACHE)))
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


def affix_entries(item):
    """[(uid, side, affix)] — a STABLE per-affix identity for an item.

    Affix DISPLAY NAMES are not unique on an item. The 7 Aug 2026 Assault
    Shell of the Shadow carried two distinct affixes both shown as
    "of Mending": `suffix_regeneration` (Regen flat) and
    `suffix_watchdog_matrix` (MaxHP% + Regen flat). `score_tiers` and
    `simulate_contract` keyed their tier maps by display name, so ONE phase's
    Stability promoted BOTH to T1 — pricing that contract at mean +98.5
    against a plan_craft ceiling of +52.3. A contract mean can never exceed
    the optimal-plan ceiling; that impossibility is what exposed it.

    5 of 88 items in the 7 Aug capture carry a duplicated affix name (3 of
    them craftable), so this is not a one-off. Anything that maps affix ->
    tier MUST key on the uid, never on `affix["name"]`.
    """
    return [(f"{'prefix' if side == 'prefixes' else 'suffix'}#{i}", side, affix)
            for side in ("prefixes", "suffixes")
            for i, affix in enumerate(item.get(side) or [])]


def affix_label(item, uid):
    """Display name for `uid`, disambiguated only when the name repeats.

    Keeps output identical for the common (unique-name) case and appends the
    `affix_id` when it would otherwise be impossible to tell two phases apart.
    """
    entries = affix_entries(item)
    match = next((a for u, _s, a in entries if u == uid), None)
    if match is None:
        return uid
    name = match.get("name") or uid
    if sum(1 for _u, _s, a in entries if a.get("name") == name) > 1:
        return f"{name} [{match.get('affix_id')}]"
    return name


def resolve_affix_uid(item, query):
    """uid for a `--phase` affix reference; raises ValueError if ambiguous.

    Accepts a uid ("suffix#1"), an exact//case-insensitive display name, or an
    `affix_id`. A bare display name that matches two affixes is REJECTED
    rather than silently resolved to the first — picking one arbitrarily is
    how the name-collision defect would come back through the CLI door.
    """
    entries = affix_entries(item)
    q = query.strip()
    for uid, _side, _affix in entries:
        if uid == q:
            return uid
    hits = [uid for uid, _s, a in entries if (a.get("name") or "").lower() == q.lower()]
    if not hits:
        hits = [uid for uid, _s, a in entries if (a.get("affix_id") or "") == q]
    if not hits:
        raise ValueError(f"{item.get('name')} has no affix {query!r}")
    if len(hits) > 1:
        options = ", ".join(f"{u} ({affix_label(item, u)})" for u in hits)
        raise ValueError(
            f"{query!r} is ambiguous on {item.get('name')} — it names "
            f"{len(hits)} affixes. Use one of: {options}")
    return hits[0]


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
               deep_step=TIER_STEP_DEEP, deep_step_low=TIER_STEP_DEEP_LOW,
               weights=None):
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
    # Which weights the GREEDY SEARCH optimises, not just how the result is
    # scored -- the two are the same decision. A plan chosen to maximise raw
    # score routes Stability into whatever family scores highest, and if that
    # family is flagged, re-scoring THAT plan ex-suspect answers the wrong
    # question: it prices a plan nobody would run under those beliefs. See
    # `suspect_free_weights`.
    pct_w, flat_w = weights or (CRAFT_WEIGHTS_PCT, CRAFT_WEIGHTS_FLAT)
    stability = item.get("stability") or 0
    ilvl = item.get("item_level") or 0
    open_slot, forced_side = augment_state(item)
    reserve = 1 if (open_slot and stability > floor) else 0
    budget = stability - floor - reserve

    # mutable affix state: [uid, affix, current_tier, upgraded?]. Keyed by uid,
    # never by display name -- see `affix_entries`.
    state = [{"uid": uid, "affix": affix, "tier": affix.get("tier"), "up": False}
             for uid, _side, affix in affix_entries(item)]

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
                gain += (nxt - cur) * scale_flat_value(ilvl) * flat_w.get(label, 0.0)
            else:
                gain += (nxt - cur) * scale_percent_value(ilvl) * 100 * pct_w.get(label, 0.0)
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
                cost = version_upgrade_expected_stability(entry["tier"], preserve)
                if cost > budget - spend or gain <= 0:
                    continue
                if gain / cost > best_ratio:
                    best, best_ratio = (entry, gain, estimated, cost), gain / cost
            if best is None:
                break
            entry, gain, estimated, cost = best
            spend += cost
            attempts += version_upgrade_expected_attempts(entry["tier"])
            entry["tier"] -= 1
            entry["up"] = True
            steps.append((entry["uid"], entry["affix"].get("tier"),
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
                    scale = (scale_flat_value(ilvl) if e.get("type") == "flat_add"
                             else scale_percent_value(ilvl))
                    value = norm * scale
                    value_low = low * scale
                else:
                    value = e.get("value", 0)
            else:
                value = e.get("value", 0)
            add(label, e.get("type"), value * (1 + compile_pct),
                None if value_low is None else value_low * (1 + compile_pct))

    # merge upgraded steps per affix for compact display -- by uid, so two
    # same-named affixes stay two lines with two costs instead of collapsing
    # into one that under-reports the spend
    merged = {}
    for uid, t_from, t_to, cost, estimated in steps:
        cur = merged.setdefault(uid, [t_from, t_to, 0.0, False])
        cur[1] = min(cur[1], t_to)
        cur[2] += cost
        cur[3] = cur[3] or estimated
    plan_steps = [(uid, affix_label(item, uid), f, t, c, est)
                  for uid, (f, t, c, est) in merged.items()]

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
        "score": weighted_score(totals, weights),
        "score_low": weighted_score(totals_low, weights),
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

    `tiers` maps affix UID (see `affix_entries`) -> target tier; affixes absent
    from it keep their current tier and roll. It was keyed by DISPLAY NAME
    until 7 Aug 2026, which silently promoted every same-named affix together
    for one affix's Stability. Promoted affixes are valued at the target tier
    MIDPOINT (roll is lost on promotion, crafting.md §12.2). Compile adds
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
    for uid, _side, affix in affix_entries(item):
        target = tiers.get(uid)
        promoted = target is not None and target != affix.get("tier")
        for e in affix.get("effects") or []:
            label = stat_label(e.get("resource") or "?")
            if promoted:
                key = (affix.get("affix_id"), e.get("resource"), e.get("type"))
                ladder = ladders.get(key)
                if ladder:
                    norm, _ = ladder_value(ladder, target, deep_step)
                    scale = (scale_flat_value(ilvl) if e.get("type") == "flat_add"
                             else scale_percent_value(ilvl))
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

    `phases` is [(affix UID, target tier), ...] IN EXECUTION ORDER — uid per
    `affix_entries`, NOT the display name, which is not unique on an item.
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
    start = {uid: a.get("tier") for uid, _side, a in affix_entries(item)}
    stability = item.get("stability") or 0
    budget = stability - floor
    results, completed = [], 0
    for _ in range(trials):
        spent, tiers = 0.0, dict(start)
        finished = True
        for uid, target in phases:
            tier = start.get(uid)
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
                tiers[uid] = tier
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


def deepen_search(item, ladders, phases, floor=COMPILE_FLOOR, preserve=0.0,
                  trials=4000, max_deepen=3, **kw):
    """Test plans DEEPER than plan_craft's, which stops at the expected budget.

    plan_craft breaks when the next step's expected Stability exceeds what is
    left (`cost > budget - spend`), so it plans to roughly exhaust the budget
    in expectation. That is the wrong objective. Tier value compounds while
    attempt cost only grows linearly, and an over-committed plan that runs out
    of Stability simply stops -- leaving a shallower craft that is still an
    upgrade, and which you are free not to equip. So the downside of aiming too
    deep is bounded and the upside is not.

    Measured on the 29 Jul Daemon, same base, 20k trials each: the contracted
    plan (Quarantine T2) scored mean +15.6 / p10 +7.8; deepening the single
    highest-value affix to T1 scored mean +21.3 / p10 +7.1 -- **+37% expected
    value for 0.7 of p10 and an identical worst case**. The player had already
    beaten the contract this way twice before it was modelled.

    Returns [(phases, sim)] ranked by mean, best first.
    """
    base = [(name, tier) for name, tier in phases]
    seen, out = set(), []
    for i in range(len(base)):
        for deeper in range(0, max_deepen + 1):
            cand = list(base)
            cand[i] = (base[i][0], max(1, base[i][1] - deeper))
            key = tuple(cand)
            if key in seen:
                continue
            seen.add(key)
            out.append((cand, simulate_contract(item, ladders, cand, floor=floor,
                                                preserve=preserve, trials=trials,
                                                **kw)))
    out.sort(key=lambda r: -r[1]["mean"])
    return out


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


def format_cost(cost):
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


def homelab_build_speed(info):
    """Homelab build-speed multiplier `o` -- the WHOLE tick pool, not per slot.

    Mirrors the client's `homelabBuildSpeedBreakdown`:
        o = (1 + upgradeEffects + global_build_speed_bonus) * global_multiplier
    clamped to [1, 20]. Total progress is `o / tick_seconds` ticks per second
    SPLIT evenly across active jobs, so this is the only lever on the rate --
    slot count is not one. Verified against the capture 29 Jul 2026: n=2 jobs
    each advanced 0.1580 ticks/s, total 0.3161 == 1.58/5. See mechanics.md §15.
    """
    bonus = float(info.get("global_build_speed_bonus") or 0)
    mult = float(info.get("global_build_speed_multiplier") or 1)
    upgrades = float(info.get("build_speed_upgrade_bonus") or 0)
    return max(1.0, min(20.0, (1.0 + upgrades + bonus) * mult))


def hardware_track_depth_note(definition):
    """Warning for a hardware track whose score does not convert to depth.

    Reads `SUSPECT_WEIGHTS`, the single registry. Until 8 Aug 2026 this had its
    OWN dict (`DEPTH_SUSPECT_STATS`, keyed by game stat id) holding Barrier
    while `SUSPECT_WEIGHTS` (keyed by craft label) did not -- so `hardware`
    printed the Barrier caveat and `potential`/`locks`/`contract` did not, on
    the same underlying finding. Its own comment said "every panel that ranks
    by score must mark them" and two of the three did not. Found by the two
    panels disagreeing in one advisory, which is how every defect here is
    found; merged rather than synchronised, because two dicts that agree today
    are the defect, not the fix.
    """
    for effect in definition.get("effects") or []:
        label = stat_label(effect.get("combat_stat") or "")
        if label in SUSPECT_WEIGHTS:
            return f"{label}: {SUSPECT_WEIGHTS[label]}"
    return None


# How many band-clearing craft bases to hold PER SLOT. Measured 7 Aug 2026
# after the first lock sweep recommended holding 13 and the player challenged
# it as excessive. Three numbers decide it, none of which the first version
# looked up:
#
#   1. Band-clearing bases ARRIVE at 0.92/day (14 keepers over the 15.2-day
#      acquisition span of the current inventory), and the newest keeper in
#      almost every slot is 0.0-0.5 days old. Supply roughly equals the ~0.8-1
#      craft/day throughput, so a deep queue is never drawn down.
#   2. Bases are CRAFTED YOUNG: median age at craft 1.2 days, max ever 4.5,
#      5 of 8 within 2 days (all eight graded crafts of the current era). No
#      base has ever waited in inventory long enough for depth to pay.
#   3. Holding has a price, though a SOFTER one than first claimed: inventory
#      was 94/102 and a slot costs 10 HACKCOIN (~83B credit-equivalents, the
#      scarcest currency). CORRECTED 7 Aug 2026 by code review -- `max_slots`
#      is NOT a hard cap: seven captures on 5 Aug held 103 items against a
#      max of 102, so the field bounds nothing absolutely and "only 8 slots
#      free" overstated the squeeze. Treat it as pressure, not a wall.
#
# Legs 1 and 2 carry the conclusion on their own and are the load-bearing
# ones; leg 3 only adds a price. A marginal 4th-choice base worth ~+11 score,
# near-certain to be superseded within days, is not worth a slot at any of
# these prices.
#
# RAISED 1 -> 2 on 7 Aug 2026, because leg 1 was measuring the wrong thing.
# "0.92 band-clearing keepers/day" counts everything over UPGRADE_BAND and
# treats those bases as INTERCHANGEABLE. They are not: scoring every base in
# the archive by arrival date, the Analyzer slot takes in a band-clearing
# base every 0.9 days but a TOP-DECILE one (keep_worth >= 46.5) only every
# 6.8 days. Depth 1 therefore discarded rank-2 bases whose true replacement
# time was ~7 days while the justification claimed ~1.
#
# It cost real progress the same day it was written: `Resilient Analyzer of
# Aiming` (keep +46.5, exactly the top-decile line) and `Untouchable Analyzer
# of Aiming` (keep +42.5, raw +121.2 -- the highest raw base owned in any
# slot) were both rank > 1, produced NO output at all because the list is
# delta-only and they were already unlocked, and were decompiled.
#
# Leg 3's price has also collapsed: inventory is 23/102 after that sweep, so
# holding a second base per slot is currently free. Re-examine if inventory
# pressure returns -- but note the correct comparison is the replacement time
# of a base of EQUAL QUALITY, never the raw keeper arrival rate.
KEEP_DEPTH_PER_SLOT = 2


def inventory_pressure(capture):
    """(used, cap, free, hackcoin_per_extra_slot) — the cost of holding.

    Exists because the first lock sweep recommended 13 holds without ever
    checking whether inventory space was scarce. It was: 94/102, expandable
    only at 10 hackcoin per slot.
    """
    used = sum(1 for where, _s, _i in iter_items(capture) if where == "inventory")
    # Prefer the always-present inventory binding over the LAZY homelab panel,
    # which is only captured when that tab was opened and goes stale in place.
    inv = (capture["state"].get("inventoryData") or {})
    cap_slots = inv.get("max_slots")
    if cap_slots is None:
        cap_slots = (capture["state"].get("homelabInfo") or {}
                     ).get("inventory_max_slots")
    price = None
    hw = hardware_state(capture) or {}
    for d in hw.get("definitions") or []:
        if d.get("name") == "Hard Disk Drive":
            price = (d.get("next_cost") or {}).get("hackcoin")
    return used, cap_slots, (cap_slots - used if cap_slots else None), price


def homelab_job_eta_hours(info, jobs):
    """{job index: real hours until it finishes}, sharing declining throughput.

    Throughput `o` is split across ACTIVE jobs, so the split CHANGES as jobs
    complete: with 3 running each gets o/3 until the first finishes, then o/2,
    then o. Pricing every job at the initial job count (the 7 Aug first
    version) over-states every ETA except the longest one's.

    Simulated in phases between completions — exact, and cheap at <= 4 jobs.
    """
    speed = homelab_build_speed(info)
    tick_s = info.get("tick_seconds") or 5
    remaining = {i: max((j.get("duration_ticks") or 0)
                        - (j.get("progress_ticks") or 0), 0.0)
                 for i, j in enumerate(jobs)}
    eta, elapsed_s = {}, 0.0
    while remaining:
        n = len(remaining)
        rate = speed / tick_s / n              # ticks per second, per job
        first = min(remaining, key=lambda i: remaining[i])
        phase_s = remaining[first] / rate if rate else 0.0
        elapsed_s += phase_s
        eta[first] = elapsed_s / 3600.0
        done_work = phase_s * rate
        del remaining[first]
        for i in list(remaining):
            remaining[i] = max(remaining[i] - done_work, 0.0)
    return eta


def capture_age_minutes(capture, now_ms=None):
    """Minutes between the capture and now, or None if it cannot be told.

    Lock/decompile advice is a SNAPSHOT of an irreversible decision, and a
    half-worked list looks exactly like a wrong one — so the age is printed
    beside it rather than left for the reader to infer.
    """
    cap_ms = captured_ms(capture)
    if not cap_ms:
        return None
    if now_ms is None:
        now_ms = time.time() * 1000
    return max(0.0, (now_ms - cap_ms) / 60000.0)


def protected_revert_items():
    """Item names held for a HOT A/B gate, lowercased.

    A revert path is held for the GATE, not for its craft ceiling — it will
    always look worthless to `plan_craft` (it is the thing being replaced), so
    value-based lock advice must exempt it by name or it recommends deleting
    the only way back out of a live experiment.
    """
    active = ACTIVE_EXPERIMENT or {}  # noqa: F405 -- star-import, see below
    if not active or active.get("concluded"):
        return set()
    name = (active.get("revert_item") or "").strip()
    if not name:
        # A hot gate with no declared revert path is a DECLARATION defect, not
        # an empty result: silently returning an empty set is how the 7 Aug
        # first run of `lock_actions` told the player to decompile Shielded
        # Shell of Bastion while shell-ab-2026-08-07 was live. Fail loudly.
        raise ValueError(
            f"experiment {active.get('name')!r} is HOT but declares no "
            f"'revert_item' — lock/decompile advice cannot run safely until "
            f"it names the item it replaced (or is marked concluded)")
    return {name}


def _family_scores(totals):
    """Per-family score contribution of one item's stat totals."""
    out = {}
    for stat, (pct, flat) in totals.items():
        value = (pct * 100 * CRAFT_WEIGHTS_PCT.get(stat, 0.0)
                 + flat * CRAFT_WEIGHTS_FLAT.get(stat, 0.0))
        if value:
            out[stat] = value
    return out


PROBE_MIN_PURITY = 1.0
# Below 1.0 the swap moves the OTHER families more than the one being
# measured, so par.22's "subtract the other families at their own betas" step
# is no longer a correction to the estimate -- it IS the estimate, and the fit
# reports other families' betas wearing the target's name. Its purest usable
# Barrier lever sat at 4.1 (-49.0 against 11.9 signed). Admitting anything
# lower is worse than admitting nothing: the first version of `probe_levers`
# had no floor and duly reserved a MaxHP "arm" moving +18.2 MaxHP against
# -112.5 of signed other movement, which would have held inventory at 102/102
# to protect an instrument that could not have measured anything.


PROBE_MIN_MOVE = 8.0
# Minimum target-family score movement for a swap to count as a lever at all.
# It is a decision-bearing threshold, not a display cut-off: it decides which
# items can serve as instruments and therefore which measurements can run, so
# CLAUDE.md's "tooling thresholds and defaults are model constants too" rule
# applies and it is registered. Sized off par.22's power math rather than
# taste -- at 6 runs/arm the SE on the difference is 1.17 streaks, so
# separating the live hypotheses needs a few streaks of predicted movement,
# and at beta ~0.13-0.20 streaks per score point that is ~8 score at the very
# least. It is a floor on ADMISSION, not a target: today's ArmorPen arms move
# 61.1, comfortably clear of it.


def probe_levers(capture, family, top=3, min_move=PROBE_MIN_MOVE,
                 min_purity=PROBE_MIN_PURITY):
    """Owned swaps ranked by how PURELY they move one stat family.

    A CI/CD pair measures a family by swapping in an item that moves it and
    as little else as possible; par.22 established that perfect isolation is
    neither available nor needed, provided the other families are subtracted
    at their own betas -- so the quantity to maximise is the RATIO of the
    target family's movement to everything else's, not the target movement
    alone. Its purest recorded Barrier lever moved -49.0 score against 11.9
    of signed other movement, and that was decisive at 6 runs per arm.

    Purity is computed against SIGNED other movement, matching par.22. Signed
    is the honest denominator because opposing families partly cancel in the
    depth reading; `other_abs` is returned alongside so a caller can see how
    much cancellation the signed figure is relying on.

    Returns rows sorted by purity, each with the swap's per-family deltas so
    the subtraction step can be written straight from the output.
    """
    equipped = {SLOT_DISPLAY.get(slot, slot): item
                for slot, item in (capture["state"].get("equipmentData")
                                   or {}).items()}
    rows = []
    for where, slot, item in iter_items(capture):
        if where != "inventory" or slot not in equipped:
            continue
        cand = _family_scores(item_stat_totals(item))
        base = _family_scores(item_stat_totals(equipped[slot]))
        delta = {k: cand.get(k, 0.0) - base.get(k, 0.0)
                 for k in set(cand) | set(base)}
        move = delta.get(family, 0.0)
        if abs(move) < min_move:
            continue
        other = sum(v for k, v in delta.items() if k != family)
        other_abs = sum(abs(v) for k, v in delta.items() if k != family)
        if abs(move) < min_purity * abs(other):
            continue
        rows.append({
            "name": item.get("name") or "?",
            "slot": slot,
            "family": family,
            "move": move,
            "other": other,
            "other_abs": other_abs,
            # A perfectly isolated lever divides by zero; cap rather than
            # returning inf so the ranking stays sortable and printable.
            "purity": min(abs(move) / max(abs(other), 1e-9), 999.0),
            "deltas": delta,
            "locked": bool(item.get("decompile_locked")),
        })
    rows.sort(key=lambda r: -r["purity"])
    # `if top` would make top=0 return EVERYTHING, and `arms: 0` in a
    # reservation would then protect the whole inventory from decompile --
    # a deadlock at 102/102 dressed as a safety feature.
    return rows if top is None else rows[:top]


def reserved_probes():
    """Live probe reservations (concluded rows dropped)."""
    return [p for p in (RESERVED_PROBES or [])  # noqa: F405 -- star-import
            if not p.get("concluded")]


def reserved_probe_holds(capture):
    """{item name -> reservation} for gear held as a measuring INSTRUMENT.

    Resolved against the capture every call, never from a stored name list.
    The five arms lost before 9 Aug 2026 were lost because the reservation
    was a sentence naming items; when the inventory turned over the sentence
    kept naming items that no longer existed, and the arms that replaced them
    were never protected.

    A reservation with NO owned lever is not an error here -- it is a finding,
    and `_audit_reserved_probes` is what reports it. This function's contract
    is only "what must not be decompiled today".
    """
    holds = {}
    for probe in reserved_probes():
        for row in probe_levers(capture, probe["family"],
                                top=probe.get("arms", 1)):
            holds.setdefault(row["name"], {"probe": probe, "lever": row})
    return holds


def lock_actions(capture, floor=COMPILE_FLOOR, per_slot=KEEP_DEPTH_PER_SLOT):
    """Daily lock/unlock ACTION list: {"lock": [...], "unlock": [...]}.

    `per_slot` caps how many band-clearing bases are held in each slot. It is
    1 by default and that default is MEASURED, not taste — see
    KEEP_DEPTH_PER_SLOT. The first version of this function had no cap and
    recommended holding 13 bases; the player pushed back that it felt
    excessive and was right, for a reason nothing here had priced.

    Written 7 Aug 2026 at the player's request. The operating model is
    **everything not locked is regularly decompiled and lost**, so the lock
    flag is the only thing standing between a craft base and deletion — which
    makes drift in it a silent, irreversible progress loss. The first sweep
    found the lock set almost exactly INVERTED against value: 17 of 18 locked
    items were not worth holding, and 13 band-clearing bases sat unlocked.

    Deliberately returns only the DELTA — items whose flag disagrees with
    their value. Anything already correct is omitted, because a list that
    re-states the whole inventory every day is one nobody reads.

    Value is `min(raw Δ, ex-suspect Δ)`: a base has to clear UPGRADE_BAND
    whether or not the Corrupt/MaxHP weights are believed. That is
    deliberately conservative in the KEEP direction (it never recommends
    discarding something the suspect weights alone were propping up) and
    conservative in the DISCARD direction too (a base only survives on
    evidence that does not depend on a flagged weight).
    """
    ladders = tier_ladders_archive()
    preserve = stability_preserve_chance(capture)
    protected = protected_revert_items()
    protected_lc = {p.lower() for p in protected}
    # Instruments are held on the same footing as revert paths and for the
    # same reason: both are worthless to `plan_craft` BY CONSTRUCTION, so a
    # value ranking always sorts them into the discard pile.
    probe_holds = reserved_probe_holds(capture)
    probe_lc = {name.lower(): hold for name, hold in probe_holds.items()}
    equipped = (capture["state"].get("equipmentData") or {})
    base, eq_totals = {}, {}
    for slot, item in equipped.items():
        display = SLOT_DISPLAY.get(slot, slot)
        eq_totals[display] = item_stat_totals(item)
        base[display] = weighted_score(eq_totals[display])

    lock, unlock, candidates, contested_rows = [], [], [], []
    for where, slot, item in iter_items(capture):
        if where != "inventory":
            continue
        name = item.get("name") or "?"
        plan = plan_craft(item, ladders, floor=floor, preserve=preserve)
        raw = plan["score"] - base.get(slot, 0.0)
        suspect, labels = suspect_share(
            score_contributions(plan["totals"], eq_totals.get(slot, {})))
        # TWO different ex-suspect questions, and conflating them was a defect
        # (8 Aug 2026, caught in review before it shipped):
        #
        #   ex_suspect  = this plan RE-SCORED without the flagged families.
        #                 Answers "does the raw verdict LEAN on a flagged
        #                 weight?" -- the disagreement test. Pessimistic by
        #                 construction, and the only reading allowed anywhere
        #                 near an irreversible decompile.
        #   ex_replanned = value of the best plan built WITHOUT them. Answers
        #                 "what is the base worth under disbelief?" It is a
        #                 larger number, and using it in the disagreement test
        #                 cancelled the CONTESTED hold on five bases and put
        #                 them on the UNLOCK list -- deletions enabled by a
        #                 number derived from the very weight the printed
        #                 guarantee says never decides a decompile.
        #
        # So ex_replanned may only ever RAISE what we hold: it feeds
        # `keep_worth` and the slot ranking, never `discard_worth` and never
        # `contested`. max() rather than trusting ex_replanned >= ex_suspect:
        # plan_craft is ratio-greedy, not an exact maximum, so the ordering is
        # a near-certainty rather than a guarantee.
        sf = suspect_free_weights()
        plan_sf = plan_craft(item, ladders, floor=floor, preserve=preserve,
                             weights=sf)
        ex_suspect = raw - suspect
        ex_replanned = (weighted_score(plan_sf["totals"], sf)
                        - weighted_score(eq_totals.get(slot, {}), sf))
        # Two readings, and the two directions need OPPOSITE tests.
        #   KEEP  is asserted on the WEAKER reading: only hold what clears the
        #         band even if the suspect weights are disbelieved.
        #   DISCARD is irreversible, so it needs BOTH readings to agree: an
        #         item survives if EITHER reading clears the band.
        # Using min() for both (the 7 Aug first version) condemned Slippery
        # Payload of Breaching at raw -39.1 while its ex-suspect delta was
        # +21.0 -- a decompile verdict resting entirely on Corrupt/MaxHP,
        # exactly what the printed guarantee says never happens.
        keep_worth = min(raw, max(ex_suspect, ex_replanned))
        discard_worth = max(raw, ex_suspect)
        worth = keep_worth
        row = {"name": name, "slot": slot, "worth": worth,
               "keep_worth": keep_worth, "discard_worth": discard_worth,
               "raw": raw, "ex_replanned": ex_replanned,
               "ex_suspect": ex_suspect, "suspect_labels": labels,
               "stability": item.get("stability") or 0,
               "item_level": item.get("item_level") or 0}
        row["locked"] = bool(item.get("decompile_locked"))
        row["protected"] = name.lower() in protected_lc
        row["probe"] = probe_lc.get(name.lower())
        candidates.append(row)

    # THREE outcomes, not two. Rank on the CONSERVATIVE reading among items
    # that reading defends -- ranking on the generous one let Corrupt-inflated
    # items displace real keepers and marked them surplus (7 Aug, second
    # attempt). An item the two readings DISAGREE about is contested and gets
    # NO action at all: it stays as it is, because an irreversible decompile
    # must never turn on a weight PENDING_REFITS has flagged.
    keepers = [r for r in candidates if r["keep_worth"] > UPGRADE_BAND]
    keepers.sort(key=lambda r: -r["keep_worth"])
    rank = {}
    for row in keepers:
        rank[row["slot"]] = rank.get(row["slot"], 0) + 1
        row["slot_rank"] = rank[row["slot"]]
    for row in candidates:
        row.setdefault("slot_rank", None)

    for row in candidates:
        real_keeper = row["slot_rank"] is not None
        in_depth = real_keeper and row["slot_rank"] <= per_slot
        contested = is_contested(row["raw"], row["ex_suspect"])
        if row["protected"]:
            # Held for the GATE, never discarded -- but an UNLOCKED revert path
            # is one sweep from deletion, so it must surface as a LOCK action.
            # The first version skipped protected rows in BOTH directions and
            # printed a reassuring "HELD" line over an unlocked item.
            if not row["locked"]:
                row["reason"] = ("revert path for the live A/B gate and "
                                 "currently UNLOCKED — lock it now")
                lock.append(row)
            continue
        if row["probe"]:
            # Same rule as a revert path, different reason: this item is the
            # INSTRUMENT for a named measurement, and its craft score is
            # irrelevant to why it is held. Never unlocked; surfaced as a LOCK
            # action while unlocked, because a probe arm sitting unlocked is
            # exactly how the previous five were lost.
            probe = row["probe"]["probe"]
            lever = row["probe"]["lever"]
            if not row["locked"]:
                row["reason"] = (
                    f"RESERVED {probe['family']} probe arm (purity "
                    f"{lever['purity']:.1f}, moves {lever['move']:+.1f} "
                    f"{probe['family']} against {lever['other']:+.1f} signed "
                    f"other) and currently UNLOCKED — lock it now. Held as an "
                    f"instrument, not a craft base: {probe['unblock']}")
                lock.append(row)
            continue
        if in_depth and not row["locked"]:
            row["reason"] = (f"best {row['slot']} base owned"
                             if row["slot_rank"] == 1
                             else f"#{row['slot_rank']} in {row['slot']}")
            lock.append(row)
        elif row["locked"] and not in_depth and not contested:
            row["reason"] = _lock_reason(
                row["raw"], row["ex_suspect"], row["suspect_labels"],
                row["slot_rank"], row["slot"], per_slot,
                worth=row["keep_worth"])
            unlock.append(row)
        elif row["locked"] and contested:
            row["reason"] = (
                f"CONTESTED: raw {row['raw']:+.1f} vs ex-suspect "
                f"{row['ex_suspect']:+.1f} — the verdict flips on "
                f"{'/'.join(row['suspect_labels'])}, so it is left locked. "
                f"Resolved by the PENDING_REFITS unblock, not by guessing")
            contested_rows.append(row)
        elif contested and not row["locked"]:
            # "No action on disagreement" was STATUS-QUO BIASED, and for a
            # fresh drop the status quo is DELETION. An unlocked contested
            # item was therefore destroyed by exactly the flagged weight this
            # rule promises will never decide a decompile -- the guarantee
            # held only for items that happened to be locked already.
            # `Aligned Analyzer of Breaching` (keep +7.2 vs discard +103.1)
            # went that way on 7 Aug 2026 with no line of output.
            # Locking is cheap and reversible; decompiling is neither, so the
            # tie breaks toward holding until PENDING_REFITS resolves.
            row["reason"] = (
                f"CONTESTED and UNLOCKED: raw {row['raw']:+.1f} vs "
                f"ex-suspect {row['ex_suspect']:+.1f} — the verdict flips on "
                f"{'/'.join(row['suspect_labels'])}, so it must not be lost "
                f"to a flagged weight. Lock it until the refit resolves")
            lock.append(row)

    # Band-clearing bases that the depth cap declines to hold AND that are
    # already unlocked produce no lock/unlock delta -- correct as a delta, but
    # under the "unlocked is deleted" operating model it means the list stays
    # silent while real value is destroyed. On 7 Aug 2026 that silence cost
    # `Untouchable Analyzer of Aiming` (keep +42.5, raw +121.2). Surfacing
    # them is not a recommendation to hold; it is the cost of the cap, stated.
    # CONTESTED rows are excluded: they are already on the `lock` list, and
    # listing them here too printed one item under two opposite headings --
    # "LOCK it" and "the cap is about to delete it" (Intangible Analyzer of
    # Evasion and Leviathan's Firewall of Vitality did exactly that on 8 Aug
    # 2026). That is the one-verdict-two-recommendations shape the 7 Aug
    # review already caught once in this same function. The hold wins: it is
    # cheap and reversible, and the cap must not release something whose
    # verdict turns on a flagged weight.
    # Reserved probe arms are excluded for the same reason as CONTESTED rows:
    # an unlocked one is already a LOCK action above, and printing it here too
    # would put one item under both "lock it now" and "the cap is about to
    # delete it" -- the exact double-heading defect fixed on 8 Aug 2026.
    at_risk = [r for r in candidates
               if r["slot_rank"] is not None and r["slot_rank"] > per_slot
               and not r["locked"] and not r["protected"] and not r["probe"]
               and not is_contested(r["raw"], r["ex_suspect"])]
    at_risk.sort(key=lambda r: -r["keep_worth"])

    lock.sort(key=lambda r: -r["worth"])
    unlock.sort(key=lambda r: r["worth"])
    used, cap_slots, free, price = inventory_pressure(capture)
    contested_rows.sort(key=lambda r: -r["discard_worth"])
    return {"lock": lock, "unlock": unlock, "contested": contested_rows,
            "at_risk": at_risk,
            "protected": sorted(protected),
            "probe_holds": probe_holds,
            "per_slot": per_slot, "inventory_used": used,
            "inventory_cap": cap_slots, "inventory_free": free,
            "slot_price_hc": price}


def _lock_reason(raw, ex_suspect, labels, slot_rank=None, slot=None,
                 per_slot=1, worth=None):
    """Why an unlock is safe, in the terms that decide it.

    `worth` is the caller's `keep_worth`. Passed in rather than re-derived:
    once `keep_worth` picked up the re-planned reading, re-deriving
    `min(raw, ex_suspect)` here printed a DIFFERENT number in the reason line
    from the one in the row header (+18.8 under a headline +33.6, 8 Aug 2026)
    -- one value with two producers, in the sentence that justifies an
    irreversible delete.
    """
    worth = min(raw, ex_suspect) if worth is None else worth
    if worth > UPGRADE_BAND and slot_rank and slot_rank > per_slot:
        # NOT "0.92 keepers/day arrive", which this string used until 8 Aug
        # 2026. That rate counts every band-clearing base and treats them as
        # interchangeable -- incident #23, the measured constant justified by
        # the wrong quantity, restated here as the reason to DELETE something.
        # The quantity `per_slot` is actually sized on is how long a base of
        # EQUAL quality takes to replace: top-decile ~6.8 days.
        return (f"clears the band ({worth:+.1f}) but is only #{slot_rank} in "
                f"{slot}, outside the depth cap of {per_slot} — a base of "
                f"this quality is replaced about every 6.8 days, which is "
                f"what the cap is sized on")
    if labels and raw > UPGRADE_BAND >= ex_suspect:
        return (f"raw {raw:+.1f} rests on {'/'.join(labels)} — "
                f"only {ex_suspect:+.1f} without it")
    if labels and ex_suspect > UPGRADE_BAND >= raw:
        return (f"raw {raw:+.1f} but ex-suspect {ex_suspect:+.1f} — the "
                f"{'/'.join(labels)} term is what sinks it, so this is a "
                f"depth/rank call, not a value one")
    return f"{raw:+.1f} vs equipped"


def homelab_job_hours(info, ticks, active_jobs=1):
    """REAL hours for `ticks` of build work, at the current build speed.

    The client advances a job by `l*o*t/n` (`homelabJobEstimates`): `o` is the
    whole-lab build-speed multiplier and `n` the number of ACTIVE jobs sharing
    it. So raw `duration_ticks * tick_seconds` is work, NOT time, and over-
    states the wait by `o/n` — 3.125x at the 7 Aug 2026 build.

    Found 7 Aug 2026: `ih.py homelab` printed the CI/CD Pipeline -> L4 job at
    "~229min" when it had ~73 min left, while `ih.py audit` (which divided
    correctly) said 1.2h of work was buffered. The two panels disagreed by
    exactly `o`. Every duration this workspace prints goes through here.

    `active_jobs` defaults to 1 — the "run it alone" convention used when
    ranking candidate jobs, which is also the fastest-to-finish case.
    """
    speed = homelab_build_speed(info)
    tick_s = info.get("tick_seconds") or 5
    return max(ticks, 0) * tick_s * max(active_jobs, 1) / speed / 3600.0


def homelab_fill_suggestions(capture, limit=3, allow_hackcoin=False):
    """Concrete jobs to put in free build slots / queue places, best first.

    Ranked by **points per tick** -- i.e. points per slot-hour. CORRECTED
    29 Jul 2026, having been backwards since it was written.

    The old ranking was by total points, justified by "an idle slot costs more
    than a better hourly rate". That rested on slots adding throughput. They do
    not. The Build Scheduler upgrade says so in its own description ("splits
    progress, doesn't speed up building"), the client divides by the active-job
    count (`homelabJobEstimates`: `remaining -= l*o*t/n`), and the capture
    confirms it exactly: with n=2 active jobs each advanced 0.1580 ticks/s and
    the total was 0.3161 ticks/s == `build_speed_multiplier / tick_seconds`
    == 1.58/5. See `mechanics.md` §15.

    So **tick throughput is a fixed pool** and the only question is which jobs
    to spend it on -- which makes points-per-tick the whole ranking. Slot count
    changes nothing about the rate; it only buffers work so throughput never
    falls to zero while nobody is refilling. Excludes jobs already active or
    queued, gated jobs, and (by default) anything costing hackcoin, which is
    reserved for install gates.
    """
    homelab, definitions, info = homelab_state(capture)
    if not homelab:
        return []
    level = homelab.get("level", 0)
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
            "hours": homelab_job_hours(info, nxt.get("duration_ticks") or 0),
            "cost": cost, "description": d.get("description") or "",
        })
    for r in out:
        r["pts_per_hour"] = r["points"] / r["hours"] if r["hours"] else 0.0
    # points per tick is the scarce-resource ranking; total points only breaks
    # ties, since a longer job buffers more unattended work at the same rate.
    out.sort(key=lambda r: (-r["pts_per_hour"], -r["hours"]))
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
            pool = gear_flat_pool(b)
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
    cap_ms = captured_ms(capture)
    rows = []
    for section in ("homelabInfo", "hardwareInfo"):
        info = state.get(section) or {}
        if not info:
            continue
        server_ms = info.get("server_time_ms")
        age = ((cap_ms - server_ms) / 1000
               if server_ms and cap_ms else None)
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
                credit_tolerance * max(credits) and credit == min(credits):
            # attribute to the MIN: credits mostly accrue, so the low reading
            # is the likelier-stale snapshot (until 6 Aug 2026 this flagged
            # every NON-min section -- the wrong culprit, arbitrarily)
            worst.append((section, f"reports {credit:,.0f} credits vs "
                                   f"{max(credits):,.0f} elsewhere -- credits "
                                   f"accrue, so the low reading is stale"))
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


def latest_stream_ms(dir_=None):
    """Newest seen_ms across ALL ledger record kinds, or None.

    Exists because `stats` records append only when combat stats CHANGE: a
    player who idles streams fights/deaths for an hour without a single new
    stats record, and any staleness measure keyed to stats alone goes silent
    exactly then (31 Jul 2026: a capture 25+ min behind a flowing stream drew
    no OUTDATED flag because the newest stats record predated the capture).
    """
    best = None
    for record in stream_records(dir_):
        ms = record.get("seen_ms")
        if ms is not None and (best is None or ms > best):
            best = ms
    return best


def latest_stream_player(dir_=None):
    """(seen_ms, player) of the newest ledger `stats` record, or (None, None).

    (A `before_ms` filter parameter existed here from 31 Jul to 6 Aug 2026
    with zero callers -- removed in the public-release audit.)"""
    best_ms, best = None, None
    for record in stream_records(dir_):
        if record.get("kind") != "stats":
            continue
        ms, player = record.get("seen_ms"), record.get("player") or {}
        if ms is None or not player:
            continue
        if best_ms is None or ms > best_ms:
            best_ms, best = ms, player
    return best_ms, best


def capture_filename_ts(path):
    """Naive datetime parsed from a capture filename, or None.

    One shared parser: this regex was duplicated between the register's
    contract-drop check and `cmd_brief` until the 6 Aug 2026 audit.
    """
    m = re.search(r"(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})", path.name)
    return (datetime.fromisoformat(
        f"{m.group(1)}T{m.group(2)}:{m.group(3)}:{m.group(4)}")
        if m else None)


def captured_ms(capture):
    stamp = capture.get("capturedAt")
    if not stamp:
        return None
    return datetime.fromisoformat(
        stamp.replace("Z", "+00:00")).timestamp() * 1000


def measured_credits_per_hour(max_gap_s=300, trailing_h=None, dir_=None):
    """Credits/hr from the ledger's own fight rewards, or None.

    Gap-aware, and it has to be: the ledger spans six days of wall clock but
    only ~13 hours of play, so dividing total rewards by (last - first) reports
    ~0.8M/hr against a true ~10M/hr. Same trap `fight_cadence` documents -- a
    ledger timestamp range is not playing time. Elapsed accrues only across
    consecutive fights less than `max_gap_s` apart (the stream polls every
    150 s, so 300 s spans a normal poll without spanning a closed browser).

    `trailing_h` restricts to the last N hours of records. The rate grows
    with the build (6.6M/hr on 23 Jul -> 23.8M/hr on 6 Aug), so the pooled
    all-history figure permanently lags the current era -- same drift the
    cadence check hides without its trailing window.
    """
    rows, seen = [], set()
    for record in stream_records(dir_):
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
    if trailing_h and rows:
        cutoff = rows[-1][0] - trailing_h * 3600 * 1000
        rows = [r for r in rows if r[0] >= cutoff]
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


_AFFIX_OBS_CACHE = {}


def _affix_range_observations():
    """{(affix_id, resource, type, tier): {ilvl: midpoint}} over the archive.

    Keyed by ilvl rather than appended per capture, so an affix owned on ONE
    item contributes ONE observation however many captures it survived in.
    Appending per capture silently weighted the fit by item longevity.
    """
    paths = tuple(sorted(str(p) for p in capture_paths()))
    if paths in _AFFIX_OBS_CACHE:
        return _AFFIX_OBS_CACHE[paths]
    groups = {}
    for path in paths:
        try:
            cap = json.loads(Path(path).read_text())
        except (OSError, ValueError):
            continue
        for _, _, item in iter_items(cap):
            for side in ("prefixes", "suffixes"):
                for affix in item.get(side) or []:
                    ilvl = (affix.get("item_level")
                            or item.get("item_level") or 0)
                    tier = affix.get("tier")
                    if not ilvl or tier is None:
                        continue
                    for e in affix.get("effects") or []:
                        # value_min may legitimately be 0, so test presence.
                        if e.get("value_max") is None or e.get("value_min") is None:
                            continue
                        key = (affix.get("affix_id"), e.get("resource"),
                               e.get("type"), tier)
                        mid = (e["value_min"] + e["value_max"]) / 2
                        groups.setdefault(key, {})[ilvl] = mid
    while len(_AFFIX_OBS_CACHE) >= 4:
        _AFFIX_OBS_CACHE.pop(next(iter(_AFFIX_OBS_CACHE)))
    _AFFIX_OBS_CACHE[paths] = groups
    return groups


def _chk_affix_scaling(cap):
    """Predict each affix's game-stated midpoint from the OTHER item levels.

    A genuine second opinion, not a restatement of the fit: for every
    affix/tier group in this capture that also appears at a different ilvl
    somewhere in the archive, normalise the other observations, re-multiply
    by this item's scale, and compare against the value_min/value_max
    midpoint the GAME declares here.

    REPORTS PER EFFECT TYPE, AND ON THE TOP-ILVL QUARTILE. The first version
    pooled flat and percent into one median and gated on |median| < 5%, which
    **did not catch the defect it was written for**: percent observations
    outnumber flat ~5:1 and were already accurate, and the flat law's error
    was a TAIL -- accurate mid-range, 19% low at the top. Reinstating the
    broken law made that version print OK at -0.0% median. A drifting law
    shows up as error that GROWS WITH ILVL, so the tail is the whole signal
    and pooling two laws over it is how the signal was lost.
    """
    groups = _affix_range_observations()
    per_type = {"flat_add": [], "mult_add": []}
    for _, _, item in iter_items(cap):
        for side in ("prefixes", "suffixes"):
            for affix in item.get(side) or []:
                ilvl = affix.get("item_level") or item.get("item_level") or 0
                tier = affix.get("tier")
                if not ilvl or tier is None:
                    continue
                for e in affix.get("effects") or []:
                    if e.get("value_max") is None or e.get("value_min") is None:
                        continue
                    etype = e.get("type")
                    key = (affix.get("affix_id"), e.get("resource"),
                           etype, tier)
                    rows = [(i, m) for i, m in groups.get(key, {}).items()
                            if i != ilvl]
                    # distinct ITEM LEVELS, which is what "predict from other
                    # levels" needs -- a count of observations let one item
                    # seen in six captures pass as six pieces of evidence.
                    if len(rows) < 3:
                        continue
                    scale = (scale_flat_value if etype == "flat_add"
                             else scale_percent_value)
                    pred = (statistics.median([m / scale(i) for i, m in rows])
                            * scale(ilvl))
                    truth = (e["value_min"] + e["value_max"]) / 2
                    if truth and etype in per_type:
                        per_type[etype].append((ilvl, pred / truth - 1.0))
    parts, status = [], "SKIP"
    for etype, label in (("flat_add", "flat"), ("mult_add", "pct")):
        rows = sorted(per_type[etype])
        if len(rows) < 8:
            parts.append(f"{label} n={len(rows)} (too few)")
            continue
        errs = [e for _i, e in rows]
        med = statistics.median(errs)
        # Top-ilvl quartile: where an ilvl-dependent law fails first, and
        # where every craft base we care about now sits.
        tail = [e for _i, e in rows[max(1, len(rows) * 3 // 4):]]
        tail_med = statistics.median(tail) if tail else 0.0
        bad = abs(med) >= 0.05 or abs(tail_med) >= 0.08
        if bad:
            status = "DRIFT"
        elif status != "DRIFT":
            status = "OK"
        parts.append(f"{label} {med:+.1%} median / {tail_med:+.1%} top-ilvl "
                     f"quartile (n={len(rows)})")
    return (status, "predicts the game's own affix midpoints from OTHER "
                    "item levels: " + "; ".join(parts))


def _chk_hardware_curve(cap):
    hw = hardware_state(cap)
    if not hw:
        return ("SKIP", "no hardwareInfo in this capture")
    fit = hardware_cost_curve(hw)
    if fit is None:
        return ("SKIP", "too few eligible tracks to fit the curve")
    _a, _p, spread = fit
    return (("OK" if spread < 1.05 else "DRIFT"),
            f"single-family fit spread {spread:.3f} (want < 1.05); the whole-"
            f"build total self-checked to +1.0% vs the game's reset refund")


def _chk_cadence(cap):
    rows = fight_cadence()
    if not rows:
        return ("SKIP", "no death records in the ledger")
    # Trailing window only: the tick era-steps (4.87 -> 4.65 over 27 Jul-
    # 1 Aug), so an all-history median averages eras together and hides
    # exactly the drift this check exists to catch (it sat "OK" at 4.750
    # pooled while the current era ran 4.65).
    recent = sorted(s for _ms, s in sorted(rows)[-50:])
    mid = recent[len(recent) // 2]
    return (("OK" if abs(mid - FIGHT_CADENCE_S) < 0.10 else "DRIFT"),
            f"trailing n={len(recent)} median {mid:.3f} s/fight vs recorded "
            f"{FIGHT_CADENCE_S}")


def _chk_credits_hr(cap):
    # Trailing window only, for the same reason as the cadence check: the
    # rate grows with the build, so the pooled all-history figure lags the
    # current era and the check would sit "OK" (or DRIFT the wrong way)
    # while the constant rotted. It did exactly that until 6 Aug 2026:
    # pooled said 17.0M vs constant 12M while the trailing rate was 23.8M.
    rate = measured_credits_per_hour(trailing_h=72)
    if rate is None:
        return ("SKIP", "no fight rewards in the trailing 72h of the ledger")
    return (("OK" if abs(rate - CREDITS_PER_HOUR) / CREDITS_PER_HOUR < 0.35
             else "DRIFT"),
            f"trailing 72h says {rate / 1e6:.1f}M/hr vs constant "
            f"{CREDITS_PER_HOUR / 1e6:.0f}M/hr")


def _chk_contract_drop(cap):
    """Re-measure drops/win from the board's own accrual across captures."""
    paths = capture_paths()
    cur = contract_board(cap).get("active")
    if not cur or cur.get("type") != "drops":
        return ("SKIP", "no drops contract active in the latest capture")

    ts = capture_filename_ts

    t_now = ts(paths[-1])
    for p in reversed(paths[-7:-1]):
        old = contract_board(load_capture(p)[0]).get("active")
        if not old or old.get("name") != cur.get("name"):
            continue
        gained = (cur.get("progress") or 0) - (old.get("progress") or 0)
        t_old = ts(p)
        if not t_old or not t_now or gained <= 20:
            continue
        hours = (t_now - t_old).total_seconds() / 3600
        if hours < 0.5:
            continue
        # wins approximated from the fixed cadence; deaths/offline gaps are
        # inside the 40% tolerance
        rate = gained / (hours * 3600 / FIGHT_CADENCE_S)
        ok = abs(rate - CONTRACT_DROP_PER_WIN) / CONTRACT_DROP_PER_WIN < 0.4
        return ("OK" if ok else "DRIFT",
                f"board accrual {gained} drops / {hours:.1f}h -> "
                f"{rate:.3f}/win vs constant {CONTRACT_DROP_PER_WIN}")
    return ("SKIP", "no earlier capture shares the active drops contract")


def assumptions():
    """[(name, value, provenance, basis, validated_on, check)] — the register.

    Ordered most-suspect first: anything `inherited` or `asserted`, then
    `supplied`, then `measured`.
    """
    w, f = CRAFT_WEIGHTS_PCT, CRAFT_WEIGHTS_FLAT
    rows = [
        # --- planning weights: a bottleneck heuristic, not a game formula ---
        ("CRAFT_WEIGHTS_PCT[Acc]", w["Acc"], "measured",
         "SETTLED at 0.21 after TWO corrections in one session -- the value "
         "moved 0.14 -> 0.19 -> 0.115 -> 0.21 and only the last is sound. "
         "Error 1: multiplied a per-STAT elasticity onto the weight scale, "
         "forgetting that a +1% AFFIX moves the accuracy stat only 0.4283% "
         "(pool 2.3347). Error 2: the elasticity itself came from a BIASED "
         "denominator -- `pm` flags only that the FIRST attack of the round "
         "missed, so hits/(hits+missflags) read 0.757 where the true "
         "per-attack rate is 0.638. Refitting on 2-attack rounds only "
         "(n(2,0) vs n(1,1), 1,004 rounds) gives "
         "logit(hit) = -0.164 + 1.420*ln(Acc/Eva) -- a STEEPER curve, so "
         "Accuracy is worth ~2x the biased fit: +0.45-0.50% output per 1% of "
         "the stat at the evasion streak 120-159 faces, i.e. 0.198-0.218. "
         "True hit rate there is 65-68%, nowhere near saturated. Covers the "
         "OUTPUT channel only, so still a floor. Out-of-sample holds: "
         "profiler 30 Jul (63.6% obs vs ~64% pred at Acc -11.2%), and live "
         "31 Jul firewall window (+0.7pp predicted at the deep bands, +0.7pp "
         "observed at both 86-105 and 106-130)",
         "29 Jul 2026 (fitted)", None),
        ("CORRUPT_REGEN_SUPPRESSION", CORRUPT_REGEN_SUPPRESSION, "measured",
         "prg = clamp(Regeneration - 1.5*ecd, 0, max_hp - php), verified "
         "288/288 Software Profiler rounds (residual exactly 0.0 on the 190 "
         "non-capped ones) across 4 enemy classes and 2 enemy levels. Incoming "
         "corruption costs ~2.5x face value: 1.0 direct + 1.5 regeneration "
         "destroyed. Fitted at Regeneration=537.85 and ecd 0-236/round; the "
         "1.5 has NOT been shown to be independent of the player's own stats "
         "-- re-check it after any large Regeneration change, and after any "
         "Isolated Sandbox level (mechanics.md §17)", "29 Jul 2026", None),
        ("CRAFT_WEIGHTS_PCT[AtkSpd]", w["AtkSpd"], "asserted",
         "right number, wrong reason: buys NO extra fights/hour (cadence is a "
         "fixed real-time tick, era-local -- see the cadence row); pays -2% "
         "to -5% rounds per fight, i.e. it is a mitigation stat",
         "27 Jul 2026 (rationale corrected)", None),
        ("CRAFT_WEIGHTS_FLAT[Corrupt]", f["Corrupt"], "measured",
         "RE-FIT 0.7 -> 1.0, 29 Jul 2026 (late), and BOTH earlier problems "
         "were artefacts. (a) The 'NON-LINEAR, invalid above ~25 points' flag "
         "is WRONG: enemy corruption spans 3.94-50.47 across the profiler "
         "sample and max ecd/round tracks it at a constant ~6x (mean ratio "
         "5.84 for stat<10 vs 6.45 for stat>30, z~1.5 -- indistinguishable). "
         "Corruption damage is LINEAR in the stat; the apparent non-linearity "
         "was stack accumulation varying with FIGHT LENGTH. (b) The 0.7 was "
         "computed as 1.04% output x 0.7, repeating the anchor error that also "
         "hit Acc -- the scale is ~1.02 per 1% output, not 0.7. Measured from "
         "the sims: our Corruption 17.3 deals 0.90% of total output per point "
         "at enemy level 1800 and 1.18% at 2100-2537, i.e. weight 0.92-1.20. "
         "Mechanism REFINED 30 Jul from the paired profiler arms (17.36 vs "
         "71.61): per-STACK tick = ~0.95 x stat (135/270/341/412/547/611 at "
         "2/4/5/6/8/9 stacks, i.e. ~68.3 per stack at stat 71.61 -- the same "
         "~2-5% shortfall thorns shows), stacks build one per landing hit "
         "over a rolling window (Resident Shader adds +1 round/level). The "
         "'~6x at full stack' multiple is therefore SIDE-DEPENDENT, not a "
         "constant: it is stacks-sustained, set by attacks landing per round. "
         "Enemy side ~6x; OUR side reaches 8.5-9x (1.8 attacks/round x ~64% "
         "hit). LINEARITY EXTENDED 50 -> 72: avg pcd/round per stat point is "
         "5.19x at stat 17.36 vs 4.95x at 71.61 (within 5%). Output-only "
         "basis: the 1.5x regen rider is real but enemy regen is already "
         "floored at 0 in 95%+ of rounds, so there is no further gain", "30 Jul 2026 (mechanism refined)", None),
        ("CRAFT_WEIGHTS_FLAT[Regen]", f["Regen"], "measured",
         "MAGNITUDE MEASURED 6 Aug 2026 on the CI/CD Regen pair (Pinpoint vs "
         "Assault-of-Penetration kernels, 7/6 alternating runs): +31 item-flat "
         "Regen (+59 at loadout, composition x1.905) bought +3.69 +- 0.72 "
         "sim streaks at the ~176-arm faces -- ~0.119 streaks per item-flat "
         "point, a 5-sigma paired readout whose confounds net NEGATIVE "
         "(ArmorPen -46% rel, Corrupt -5.6, MaxHP -198 vs Acc +0.8pp hit), "
         "so it mildly understates Regen alone. Cross-checks live history: "
         "the Shell's +49 item Regen x 0.119 = +5.8, exactly its live close. "
         "DIRECTION was already measured twice (+20.5 streaks on +35.3% "
         "realized prg; +7.0 on the Shell). Depth-dependence stands "
         "(mechanics.md par.17): realization rises with depletion, ~100% of "
         "listed at streaks 150+, so this fit is REGIME-LOCAL to the current "
         "deep-attrition era -- re-fit if the era shallows. The 0.6 score "
         "scalar is retained as consistent (implied ~5.0 score/streak for "
         "Regen; contrast Barrier's >=23 -- the cross-family distortion is "
         "open question par.15, not a Regen problem)",
         "6 Aug 2026", None),
        ("CRAFT_WEIGHTS_PCT[Def]", w["Def"], "measured",
         "RE-FIT 1.0 -> 0.45, 29 Jul 2026, and the old 1.0 was inflated by "
         "THREE compounding errors. (1) The mitigation law is "
         "dmg = Atk*K/(K+Def-ArmorPen) with K~205 -- fitted independently on "
         "both directions, 190.2 outgoing / 219.3 incoming -- so Defense's own "
         "elasticity is -0.88, not -1.0. (2) A +1% AFFIX moves the Defense "
         "STAT only 0.435%, because its additive pool is 2.2983 (the earlier "
         "live elasticities of -0.93 to -0.96 were per-STAT and were read as "
         "if per-affix). (3) Defense touches ONLY the direct channel: against "
         "Trojan Wall, `ea` is 352.8 of an effective 859.7 gross once "
         "corruption counts at its measured 2.5x, i.e. 41%. Net of all three, "
         "and multiplied by the measured leverage gross/net = 2.5-3.1x against "
         "the three classes that cause ~72% of deaths, Defense is worth "
         "0.40-0.50 output-equivalents per +1% affix. LEVERAGE IS THE WEAK "
         "TERM: it rests on 54-309 rounds per class from 3-6 fights, sampled "
         "at enemy levels 2100-2537 while deaths happen at ~1800, where "
         "leverage is HIGHER -- so 0.45 is if anything conservative. Re-measure "
         "with a class-controlled sweep at level 1800. Live corroboration 31 "
         "Jul: Def stat +11.4% predicted -9% incoming direct per hit; "
         "per-round gross fell 10-11% at the deep streak bands (bundled with "
         "a 107K-chip package, so directional)", "29 Jul 2026 (fitted)", None),
        ("CRAFT_WEIGHTS_PCT[Eva]", w["Eva"], "measured",
         "RE-FIT 1.0 -> 0.22, 29 Jul 2026. Enemy hit rate on us fits the SAME "
         "law with the SAME slope as our outgoing fit -- logit = 0.200 + 1.208 "
         "* ln(enemyAcc/ourEva) over 2,310 enemy attacks -- giving -0.40% "
         "enemy hit rate per +1% of the Evasion STAT. Eva/Def = 0.497 is "
         "leverage-free and sample-free (both act on the direct channel only), "
         "so that RATIO is the solid part; the absolute value inherits the same "
         "leverage caveat as Def. Evasion does NOT dodge corruption -- ticks "
         "land on missed rounds (mechanics.md §16) -- which is most of why it "
         "is worth half of Defense", "29 Jul 2026 (fitted)", None),
        ("CRAFT_WEIGHTS_PCT[AtkDmg]", w["AtkDmg"], "measured",
         "ANCHOR of the whole scale, and it self-validates: a +1% AtkDmg AFFIX "
         "adds 1 point to a shared additive pool of 1.458, so the stat moves "
         "0.686% -- against an applied 0.7. The weight scale therefore means "
         "'% output-equivalent per +1% affix'. Every other weight is now "
         "expressed on that basis (mechanics.md §19)", "29 Jul 2026", None),
        ("CRAFT_WEIGHTS_PCT[CritCh]", w["CritCh"], "measured",
         "VALIDATED at 0.7, 29 Jul 2026. Crit rate measured on 954 single-hit "
         "rounds (the only unconfounded denominator -- `pc` is capped at 1 per "
         "round, so multi-hit rounds undercount) is 0.2631 against a "
         "statsBreakdown crit_chance of 0.2558. A +1pp affix is ADDITIVE (no "
         "pool division) and moves output +0.699%, i.e. weight 0.713",
         "29 Jul 2026", None),
        ("CRAFT_WEIGHTS_PCT[MaxHP]", w["MaxHP"], "asserted",
         "STILL UNMEASURED and the largest unpriced term. Max HP is pure "
         "attrition buffer, and the Software Profiler runs full-HP SINGLE "
         "fights, so it cannot see the quantity. Needs the CI/CD Pipeline "
         "(homelab 12). Note its pool is small (1.5435), so a +1% affix moves "
         "the stat 0.648% -- more than Def or Eva get from the same affix. "
         "FIRST LIVE BOUND 31 Jul (firewall-ab-2026-07-31, pre-registered as "
         "a MaxHP test): trading max_hp -7.8% for Def +11.4% / Regen +8% "
         "RAISED the death mean +12.5, and the A/B closed KEEP at n=34 "
         "(167.6 vs 155.1) -- in a mitigation-compensated trade the 0.5 "
         "weight did not under-price Max HP. SECOND BOUND 1 Aug: the "
         "shell-ab-2026-07-31 REVERSE probe (+7% max_hp inside a "
         "mitigation-weighted-positive bundle) also raised the mean, +5.8 "
         "at n=25 (173.5 vs 167.7) -- both signs moved with the "
         "mitigation-weighted totals, so 0.5 is bracketed from both "
         "directions. Bounds, not a fit; the magnitude still needs the "
         "CI/CD Pipeline", None, None),
        ("CRAFT_WEIGHTS_PCT[CritDmg]", w["CritDmg"], "measured",
         "RE-FIT 0.35 -> 0.22, 29 Jul 2026. Crit multiplier measured at 1.883 "
         "on 251 crit vs 703 non-crit single-hit rounds, against a "
         "statsBreakdown crit_damage of 1.846 -- confirmed as a multiplier on "
         "hit damage. A +1pp affix is additive on that multiplier and, at a "
         "crit rate of 0.256, moves output only +0.214%", "29 Jul 2026", None),
        ("CRAFT_WEIGHTS_FLAT[ArmorPen]", f["ArmorPen"], "measured",
         "VALIDATED 29 Jul 2026 -- the inherited guess was right. The damage "
         "law dmg = Atk*K/(K+Def-AP) with K~205 (fitted independently on both "
         "directions, K=190.2 outgoing / 219.3 incoming) prices +97 ArmorPen "
         "(10 -> 107) at +6.1% output vs enemy Defense 1,500 and +7.0% vs "
         "1,300, i.e. 0.044-0.051 per point on the AtkDmg=0.7 scale against an "
         "applied 0.05. Fitted range: enemy Defense 743-1,990, our ArmorPen 10. "
         "Extrapolating to very high ArmorPen is NOT covered -- the law is "
         "convex, so value per point RISES as ArmorPen approaches enemy "
         "Defense", "29 Jul 2026", None),
        ("CRAFT_WEIGHTS_FLAT[Thorns]", f["Thorns"], "measured",
         "RE-FIT 0.05 -> 0.13, 29 Jul 2026 -- the inherited guess was ~2.5x "
         "TOO LOW. Thorns is exact: `ptd` = 72.08 per enemy hit that lands, "
         "against a stat of 73.4 (112,951 reflected damage over 1,567 enemy "
         "hits, per-fight ratio 72.03-72.54 -- extremely tight). Value scales "
         "with fight LENGTH because it is charged per enemy hit: 0.120 at "
         "enemy level 1800, 0.157 at 2100, 0.141 at 2500. 0.13 is the value "
         "at the levels where runs actually end. CONFIRMED at a second stat "
         "level 1 Aug 2026 (shell-ab-2026-07-31 close): ptd/landed-hit "
         "75.08 -> 125.28 as the gear affix added +48 -- delta 1.046x the "
         "affix through the pool multiplier, per-hit law holds",
         "29 Jul 2026", None),
        ("CRAFT_WEIGHTS_FLAT[Barrier]", f["Barrier"], "measured",
         "0.02 -> 0.10 -> 0.043 in one day; the 0.10 is WITHDRAWN and was my "
         "error. Barrier absorbs ALL incoming channels (8,473 depletion rounds "
         "match ea+ecd+etd at 100%; 2,657 rounds where the enemy MISSED still "
         "absorbed the corruption tick), so it remains the only counter to "
         "corruption -- that part stands. But the SIZE was measured by summing "
         "`pbs` across rounds, and `pbs` is the pool REMAINING, a stock. "
         "Summing a stock over time is meaningless and over-counts more when "
         "the pool is larger (more rounds before it empties), which manufactured "
         "a fake super-linearity: apparent 1.68x -> 2.34x -> 5.26x as Barrier "
         "grew. Measured as actual pool DRAWDOWN, absorption is exactly 1.00x "
         "the stat per fight in BOTH cohorts (787.5 -> 787 absorbed; 2,529.5 -> "
         "2,529). Barrier is a once-per-fight shield equal to its value. So +1 "
         "Barrier = +1.0 HP/fight against Regen's ~13.8 marginal -> 0.6/13.8 = "
         "0.043, and the ORIGINAL 0.02 was nearer the truth than my correction. "
         "Confirmed live: +1,742 Barrier gave +29/round absorbed over ~60-round "
         "fights, exactly as 1.00x predicts",
         "29 Jul 2026", None),

        # --- verdict bands ---
        ("UPGRADE_BAND", UPGRADE_BAND, "measured",
         "path 5 -> 16 -> 5. The 30 Jul move to 16 rested on a -15.9 Payload "
         "error that was a SCALE BUG: the contract was recorded at the "
         "--deepen block's numbers, and deepen_search was called without "
         "`baseline`, so it printed ABSOLUTE post-craft scores as deltas. "
         "Corrected (subtract the equipped Bastioned's 30.6): projected "
         "+50.0 / p10 +42.5 / p90 +56.9, realized +64.7, error +14.7. "
         "In-era errors are now +21.3 / +56.8 / +14.7 -- ALL positive, all "
         "above p90, so the worst-shortfall method yields no band; ±5 (the "
         "pre-bug 22 Jul value) is restored as a switching-cost indifference "
         "band pending the first genuine negative grade. simulate_contract's "
         "p10 has never been breached -- its intervals underestimate, they do "
         "not overpromise. First IN-interval grade same day: the Firewall "
         "realized +36.8 in [+17.4, +50.9] (error -2.3, coverage 1/4) on the "
         "first projection recorded after the deepen-scale fix",
         "31 Jul 2026", None),
        ("INFERIOR_BAND", INFERIOR_BAND, "measured",
         "symmetric with UPGRADE_BAND, same 31 Jul reversion",
         "31 Jul 2026", None),
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
        ("DAMAGE_K", DAMAGE_K, "measured",
         "mitigation law dmg = Atk*K/(K+Def-ArmorPen). Fitted INDEPENDENTLY "
         "in both directions -- 190.2 outgoing / 219.3 incoming -- and the "
         "agreement is the validation. Everything Defense- or ArmorPen-"
         "carrying is priced through it, so it is one of the two most "
         "load-bearing numbers here; it was nevertheless unregistered until "
         "7 Aug 2026, found by a test that walks the module's own constants",
         "29 Jul 2026", None),
        ("HIT_LOGIT_A / HIT_LOGIT_B", (HIT_LOGIT_A, HIT_LOGIT_B), "measured",
         "hit law logit(hit) = A + B*ln(Acc/Eva), fitted 29 Jul 2026 on a "
         "fixed-Accuracy era (n=2,674 fights / 174K attempts) after the "
         "`pm`-biased saturation reading was falsified. Held OUT-OF-SAMPLE "
         "three times (Software Profiler 30 Jul; the Payload and Firewall "
         "live windows, the last matching a +0.7pp prediction exactly). "
         "Superseded the retired 0.532/1.208 pm-biased fit. Unregistered "
         "until 7 Aug 2026",
         "29 Jul 2026", None),
        ("KEEP_DEPTH_PER_SLOT", KEEP_DEPTH_PER_SLOT, "measured",
         "how many craft bases to hold per slot; decides IRREVERSIBLE "
         "decompiles. RAISED 1 -> 2 on 7 Aug 2026 because its original "
         "load-bearing leg measured the WRONG QUANTITY. That leg was "
         "'band-clearing bases arrive 0.92/day and are crafted young "
         "(median age 1.2d)', which treats every base over UPGRADE_BAND as "
         "INTERCHANGEABLE. Scoring every base in the archive by arrival "
         "date, the Analyzer slot takes in a band-clearing base every 0.9 "
         "days but a TOP-DECILE one (keep_worth >= 46.5) only every 6.8 -- "
         "so depth 1 discarded rank-2 bases whose real replacement time was "
         "~7x what the justification claimed. It cost four bases the day it "
         "shipped, including the highest-raw base owned (+121.2). The right "
         "comparison is the replacement time of a base of EQUAL QUALITY, "
         "never the raw keeper arrival rate. Inventory pressure (10 hc/slot) "
         "only prices it and has collapsed at 23/102; max_slots is soft "
         "anyway -- seven 5 Aug captures held 103 against a max of 102",
         "7 Aug 2026 (re-derived)", None),
        ("PROBE_MIN_MOVE", PROBE_MIN_MOVE, "asserted",
         "minimum target-family score movement for a swap to be admitted as "
         "a probe arm. Gates which measurements can run at all, so it is a "
         "model constant and not a display cut-off. Derived from par.22's "
         "power math rather than measured: SE on the difference is 1.17 "
         "streaks at 6 runs/arm, and at beta 0.13-0.20 streaks per score "
         "point a few streaks of separation needs ~8 score at minimum. Never "
         "exercised near its value -- every arm admitted so far moves 61.1, "
         "~7.6x the floor -- so the binding case is untested and a marginal "
         "lever has never been run",
         "9 Aug 2026 (asserted at introduction)", None),
        ("PROBE_MIN_PURITY", PROBE_MIN_PURITY, "asserted",
         "admission floor for a reserved CI/CD probe arm: |target family "
         "score move| / |signed other move|. Decides which items are held as "
         "INSTRUMENTS and therefore exempted from decompile, so it spends "
         "inventory (10 hc/slot at 102/102) and it gates whether a "
         "measurement can run at all. Set to 1.0 by ARGUMENT, not by "
         "measurement: below 1.0 par.22's 'subtract the other families at "
         "their own betas' step is larger than the signal it corrects, so "
         "the fit reports other families' betas under the target's name. The "
         "only calibration point is par.22's purest Barrier lever at 4.1 "
         "(-49.0 against 11.9 signed), which was decisive at 6 runs/arm -- "
         "one point, well above the floor, so the floor itself is untested "
         "and the region 1.0-4.0 is unvalidated. EXERCISE IT: the 9 Aug "
         "ArmorPen block runs a purity-6.6 arm; if its beta lands with the "
         "SE par.22 predicts, that is a second point and the floor can be "
         "fitted rather than argued. Note the signed denominator relies on "
         "cancellation -- `other_abs` is returned so a caller can see how "
         "much (the top 9 Aug ArmorPen arm cancels 61.8 abs down to 6.6 "
         "signed, the second only 27.8 down to 9.2)",
         "9 Aug 2026 (asserted at introduction)", None),
        ("plan_craft tier_cap default", 1, "measured",
         "was 3 and untested, which excluded the two best steps on the "
         "ladder; gain per expected Stability point peaks at T3->T2",
         "27 Jul 2026", None),
        ("HARVEST_PER_GATHER_HOUR", HARVEST_PER_GATHER_HOUR, "measured",
         "LOWER BOUND, path 305 -> 700 in one evening (31 Jul 2026). First "
         "bound: an Extended Harvest (1,331 actions) cleared inside a 4.37h "
         "window of unknown gathering coverage. Second: 3 -> 294 actions "
         "across a 24.3-min two-capture window with the contract active at "
         "both ends = ~718/h; 700 recorded. Both are lower bounds -- the "
         "true rate needs a window with known continuous gathering. Passive "
         "accrual ~zero: harvest pays per GATHER-hour only",
         "31 Jul 2026", None),
        ("BOARD_TYPICAL_BEST_HC_PER_H", BOARD_TYPICAL_BEST_HC_PER_H,
         "asserted",
         "eyeballed from the 31 Jul - 6 Aug boards (best pending contract "
         "2.2-4.3 hc/combat-h), never fitted. Only prices the opportunity "
         "cost of a carried contract occupying the slot past reset -- low "
         "stakes, but it is a number in an audit message and belongs here",
         "6 Aug 2026 (named)", None),
        ("CICD_RUNS_PER_LEVEL", CICD_RUNS_PER_LEVEL, "measured",
         "the install's own description states it and L3 = 15 was observed "
         "5-6 Aug 2026; in-game description text is primary evidence. "
         "Whether a mid-day level-up raises the same day's budget is "
         "unobserved (simulator-protocol.md par 9.2)", "6 Aug 2026", None),
        ("ENEMY_LEVEL_GROWTH_PER_STREAK", ENEMY_LEVEL_GROWTH_PER_STREAK,
         "asserted",
         "streak-simulator extrapolation slope past the deepest observed "
         "level-curve point; eyeballed from the curve's deep end, never "
         "fitted on its own. Inline and unregistered until 6 Aug 2026. "
         "Matters only when simulated streaks exceed live depth",
         "6 Aug 2026 (named)", None),
        ("CORRUPT_STACK_CAP", CORRUPT_STACK_CAP, "measured",
         "max observed ecd/round is ~6x the corruption stat across profiler "
         "logs (mechanics.md par 19: stacks-sustained, side-dependent -- "
         "enemy side ~6x, our side reaches 8.5-9x on higher attack rate). "
         "The simulator caps ENEMY stacks at 6; unregistered until 6 Aug "
         "2026", "30 Jul 2026 (registered 6 Aug)", None),
        ("CONTRACT_DROP_PER_WIN", CONTRACT_DROP_PER_WIN, "measured",
         "0.0534 -> 0.296, 31 Jul 2026, and the old value had NO register row "
         "(introduced 29 Jul in violation of the same-change rule). The 29 "
         "Jul fit pooled 9,395 ledger wins recorded mostly with NO collection "
         "contract active, so it measured a different quantity 5.5x low -- it "
         "advised abandoning Marathon Collection on 31 Jul while the board's "
         "own accrual (1 -> 466 in 2.32h, contract active throughout) showed "
         "0.296/win and the contract finishing with hours to spare. Whether "
         "the rate moves with Drop Rate Amplifier, zone or streak is "
         "untested; the live check re-measures it whenever two captures "
         "share the same active drops contract", "31 Jul 2026",
         _chk_contract_drop),
        ("CREDITS_PER_HOUR", CREDITS_PER_HOUR, "measured",
         "fight rewards only; homelab jobs outspend it ~10x, and contracts "
         "add lumpy income on top. Grows with the build (6.6M/hr 23 Jul -> "
         "23.8M/hr 6 Aug), so the live check uses a trailing 72h window -- "
         "the old pooled check lagged the era and let the constant sit at "
         "half the true rate for a week", "6 Aug 2026", _chk_credits_hr),
        ("TIER_STEP_SHALLOW / TIER_STEP_DEEP / TIER_STEP_DEEP_LOW", f"{TIER_STEP_SHALLOW}/{TIER_STEP_DEEP}",
         "measured", "fitted archive-wide and re-fitted on every run by "
         "fit_tier_steps, so it cannot rot as the inventory turns over",
         "27 Jul 2026", _chk_tier_steps),
        ("DEEP_TIER", DEEP_TIER, "measured",
         "the step is region-dependent; one constant 1.4 was fitted on "
         "shallow tiers only and over-projected a T6->T1 chase by 1.9x",
         "27 Jul 2026", None),
        ("FIGHT_CADENCE_S (fight cadence, s/fight)", FIGHT_CADENCE_S, "measured",
         "from the game's own death clock, never the stream's poll interval. "
         "RE-FIT 4.872 -> 4.65 on 1 Aug 2026: the tick ERA-STEPS (daily "
         "medians 4.873 -> 4.750 -> 4.788 -> 4.605 -> 4.641 -> 4.666 over "
         "27 Jul-1 Aug, within-era sd ~0.01), mover unidentified -- not "
         "rounds/fight (r=0.42) and not AtkSpd (the +9.9% equip moved it 0% "
         "within-window). The economic law stands (AtkSpd buys no fights/"
         "hour); the CONSTANT is era-local and the live check now reads a "
         "trailing window so the next step fires DRIFT",
         "1 Aug 2026", _chk_cadence),
        ("hardware cost curve", "A*L**p", "measured",
         "fitted live off next_cost and self-validates against the game's own "
         "reset refund", "27 Jul 2026", _chk_hardware_curve),
        ("SCALE_FLAT_OFFSET/SCALE_FLAT_REF/SCALE_FLAT_EXPONENT",
         SCALE_FLAT_EXPONENT, "measured",
         "LINEAR in (ilvl + 250). Refitted 7 Aug 2026 over 138 affix/tier "
         "groups spanning ilvl 314-4767, against the game's OWN value_min/"
         "value_max fields -- so this self-validates rather than being a "
         "fit to our own scores. Was ((ilvl+100)/1021)**0.7849, an inline "
         "literal that no registry check could see. That form decayed above "
         "its fitting range: predicting the ilvl-4240 Kernel's T1 "
         "regeneration midpoint from ilvl 445-2912 observations alone it "
         "read 175.0 against a game-stated 216.0 (-19.0%), where this law "
         "reads 217.4 (+0.6%). Flat affixes are the Regen family, the "
         "confirmed win condition, so this under-projected every craft that "
         "mattered and is the leading candidate for the +23.7 calibration "
         "bias. Only OFFSET and EXPONENT matter; SCALE_FLAT_REF cancels",
         "7 Aug 2026 (refitted)", _chk_affix_scaling),
        ("SCALE_PCT_OFFSET/SCALE_PCT_REF/SCALE_PCT_EXPONENT",
         SCALE_PCT_EXPONENT, "measured",
         "((ilvl + 250)/1125)**0.4333, refitted 7 Aug 2026 in the same pass "
         "over 645 affix/tier groups. The old (offset 125, k 0.391) was much "
         "closer than the flat law -- median within-group spread 1.014 vs "
         "1.0015 refitted, and -2.2% vs -0.1% on the same out-of-sample "
         "ilvl-4240 test -- so this moves percent-carried verdicts only "
         "slightly. Refitted anyway rather than left as a known-smaller "
         "error", "7 Aug 2026 (refitted)", None),
        ("composed_stat_total stat families", "SCALING/DIRECT/economy", "measured",
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
PREDICTIONS_PATH = DATA_ROOT / "predictions.jsonl"
# Bumped 7 Aug 2026 by the affix-scaling refit. The nine rows tagged
# `uncapped+floor2+archive` all had their PROJECTIONS computed with a flat
# scaling law that ran ~19% low at current craft item levels, so that era's
# +23.7 bias is partly an artefact of the law rather than of the planner, and
# pooling new grades into it would launder a fixed defect into the new
# numbers. Their REALIZED values are unaffected (realized scores read the
# item's actual affix values, never the law) and stay comparable.
# Bumped again 8 Aug 2026 by the Barrier depth-yield refit (0.043 -> 0.0088).
# It moves any Barrier-carrying projection by far more than UPGRADE_BAND -- the
# equipped Driver's own baseline fell ~45 points, which flipped two Driver
# candidates -- so the single `+scalefit` grade (Analyzer, projected +71.4 /
# realized +75.5) stays tagged to its own era and must not be pooled with what
# follows. Its VERDICT is unaffected: projection and realized both carry the
# same ~5.2 of Barrier, so the error stays +4.1 and in-interval under either
# weight. That is a property of this particular craft, not a general one.
CURRENT_MODEL = "uncapped+floor2+archive+scalefit+betaBarrier"


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
    """Append one prediction at contract time; fill `realized` after.

    A realized-only call (projected is None, realized given) UPDATES the
    newest un-realized row for the same item instead of appending. Until
    6 Aug 2026 it appended an orphan all-None row and left the real row
    ungraded -- the documented fill flow simply did not exist, and the 5 Aug
    driver grade had been filled by hand-editing the JSONL.
    """
    if realized is not None and projected is None:
        rows = [json.loads(line) for line in
                path.read_text().splitlines() if line.strip()]
        for row in reversed(rows):
            if row.get("item") == item and row.get("realized") is None:
                row["realized"] = realized
                if note:
                    row["note"] = (row.get("note") or "") + " || " + note
                path.write_text(
                    "".join(json.dumps(r) + "\n" for r in rows))
                return row
        raise ValueError(f"no un-realized prediction row for {item!r} -- "
                         "record the contract-time row first")
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
    "Corrupt": "LINEAR to ~72 (verified 30 Jul, paired profiler arms); "
               "above that stat level is extrapolation",
    # Acc REMOVED 29 Jul 2026: it was flagged "measured saturated 27 Jul",
    # which §18 falsified. Hit rate at the evasion streak 120-159 actually
    # faces is 76-79%, nowhere near a cap, and the weight is now fitted from
    # the corrected hit law (HIT_LOGIT_A/_B = -0.164/1.420; the 0.532/1.208
    # fit quoted here until 6 Aug 2026 was the retired pm-biased one). A
    # stale suspect flag is as misleading as a stale weight -- it discounts
    # a Δ that is now sound.
    "MaxHP": "still UNMEASURED — pure attrition buffer, and the profiler's "
             "full-HP single fights cannot see it (needs CI/CD Pipeline)",
    # Barrier ADDED 8 Aug 2026 morning, REMOVED the same evening once the
    # dedicated pair measured it (beta = 0.041 +- 0.024 vs Regen's 0.200) and
    # the weight was refit 0.043 -> 0.0088. A stale suspect flag is as
    # misleading as a stale weight -- the same reason Acc came out on 29 Jul
    # and Regen on 6 Aug. Barrier-carried deltas are now SMALL rather than
    # SUSPECT, which is a different statement and the honest one: the weight
    # is measured, and `potential`/`locks` should stop discounting a Δ that no
    # longer rests on a guess. The residual uncertainty (95% CI 0.06x-0.44x
    # Regen) lives in the assumptions register, where an interval belongs,
    # rather than as a binary zeroing here.
    # Regen REMOVED 6 Aug 2026: magnitude measured on the CI/CD pair at
    # +3.69 +- 0.72 streaks per +31 item-flat (5-sigma, confounds net
    # negative, matches the Shell live close at 0.119 streaks/point). A
    # stale suspect flag is as misleading as a stale weight -- it was
    # discounting every Regen-carried Δ that is now the best-measured
    # family in the table. Fit is regime-local (deep-attrition era).
}


def is_contested(raw, ex_suspect):
    """Do the two readings of one base straddle `UPGRADE_BAND`?

    Deliberately a function of the (raw, RE-SCORED ex-suspect) pair and
    nothing else -- split out of `lock_actions` on 8 Aug 2026 so it cannot
    quietly acquire another input. It did: `keep_worth` was folded in, and
    once `keep_worth` started carrying the more generous RE-PLANNED reading
    (`suspect_free_weights`) that inflation cancelled the hold on five
    contested bases and moved them onto the irreversible UNLOCK list --
    deletions decided by a weight `PENDING_REFITS` has flagged, which is the
    one thing the printed guarantee promises never happens. The re-planned
    reading may raise what is HELD; it must never reach this test.
    """
    return min(raw, ex_suspect) <= UPGRADE_BAND < max(raw, ex_suspect)


def suspect_free_weights():
    """(pct, flat) CRAFT_WEIGHTS with every `SUSPECT_WEIGHTS` family zeroed.

    For planning under disbelief, not just scoring under it. `plan_craft` is a
    greedy search that spends Stability where score-per-Stability is highest,
    so with Barrier flagged (8 Aug 2026) the raw-optimal plan for
    `Shielded Analyzer of Puncturing` sank 13.1 of its 26 Stability into
    of Quarantine (Barrier T6->T1) -- and the lock recommender then priced the
    base by re-scoring THAT plan ex-suspect, getting +43.4 and releasing the
    base to the AT RISK list. Planning ex-suspect instead spends the same
    Stability on of Puncturing (ArmorPen, measured) and of Swiftness, worth
    ~+72 on the same disbelieving reading. The base was never the problem; the
    plan was. Found when `potential` called it the best Analyzer base in the
    same advisory where `locks` released it for deletion.
    """
    pct = {k: v for k, v in CRAFT_WEIGHTS_PCT.items() if k not in SUSPECT_WEIGHTS}
    flat = {k: v for k, v in CRAFT_WEIGHTS_FLAT.items() if k not in SUSPECT_WEIGHTS}
    return pct, flat


def suspect_share(contributions):
    """(suspect_total, [labels]) for the part of a Δ resting on bad weights."""
    rows = [(v, label) for v, label in contributions
            if label in SUSPECT_WEIGHTS]
    return sum(v for v, _ in rows), [label for _, label in rows]


def contract_board(capture):
    """Daily contract board state: reset clock, live progress, unclaimed pay.

    Added 28 Jul 2026 after the sweep missed it. The board resets at a fixed
    UTC hour. CORRECTED 6 Aug 2026: the original "unfinished progress is
    destroyed at reset" was asserted and never tested -- the ACTIVE contract
    in fact CARRIES THROUGH the reset and runs to completion
    (player-observed at the 6 Aug reset; mechanics.md §20 -- a 9-pair
    archive straddle scan cannot distinguish the models, so the live
    observation governs). What the reset replaces: unstarted contracts and
    the clear-bonus opportunity. Contracts are the game's only observed
    repeatable hackcoin source (1-5 hc each plus a board-clear bonus), which
    is the scarcest currency in the model.

    Returns {reset_ms, hours_left, all, active, pending, unclaimed,
    clear_bonus, clear_bonus_claimed, board_hackcoin, queue_capacity}.

    `all` is EVERY contract on the board. Corrected 29 Jul 2026: this used to
    return only `active` + `unclaimed`, which silently dropped the five to six
    contracts sitting incomplete at 0 progress -- so an advisory priced the
    board at 11 hackcoin when it held 25, and misread "one contract has barely
    moved" as evidence about offline accrual when the real cause was that the
    other six had never been made active. **Only the ACTIVE contract accrues
    progress** (`contract_queue_capacity` is 0: no queue, one at a time), so
    clearing the board is a sequence of manual switches, and that -- not wall
    clock -- is what makes the clear bonus hard.
    """
    board = ((capture["state"].get("currentPlayer") or {}).get("contracts")
             or {})
    rows = board.get("contracts") or []
    reset_ms = board.get("next_reset_at_ms")
    now = captured_ms(capture)
    active_id = board.get("active_contract_id")
    active = next((c for c in rows if c.get("id") == active_id), None)
    unclaimed = [c for c in rows
                 if c.get("completed") and not c.get("claimed")]
    return {
        "reset_ms": reset_ms,
        "hours_left": ((reset_ms - now) / 3.6e6
                       if reset_ms and now else None),
        "all": rows,
        "active": active,
        # incomplete and NOT the active one: these earn nothing until selected
        "pending": [c for c in rows
                    if not c.get("completed") and c.get("id") != active_id],
        "unclaimed": unclaimed,
        "clear_bonus": board.get("clear_bonus_amount") or 0,
        "clear_bonus_claimed": bool(board.get("clear_bonus_claimed")),
        "board_hackcoin": sum((c.get("rewards") or {}).get("hackcoin") or 0
                              for c in rows if not c.get("claimed")),
        "queue_capacity": board.get("contract_queue_capacity") or 0,
    }


# Contract-item drop rate per won fight WHILE a drops contract is active --
# the only regime where the number is ever used. RE-MEASURED 31 Jul 2026 from
# the board's own accrual: Marathon Collection 1 -> 466 across the 09:40 ->
# 11:59 captures (2.32h, ~1,569 stream wins) = 0.296/win. The 29 Jul fit
# (0.0534 = 502 ledger drops / 9,395 wins) pooled the WHOLE ledger, mostly
# hours with no collection contract active, so it measured a different
# quantity and came out 5.5x low -- it priced Standard Collection at ~4.8
# combat-hours (real: ~0.9) and got Marathon Collection advised as
# unfinishable on 31 Jul while it was cruising to completion. Same failure
# family as pcd/ecd: a field's meaning is a hypothesis until it is shown to
# vary with the thing it supposedly measures.
CONTRACT_DROP_PER_WIN = 0.296

# Harvest-contract actions per hour of ACTIVE gathering -- a LOWER BOUND.
# RE-MEASURED 31 Jul 2026 evening on a tight two-capture window with the
# contract active at both ends: Extended Harvest 3 -> 294 across 19:52:52 ->
# 20:17:10 (24.3 min) = ~718/h if gathering ran throughout; 700 recorded as
# the bound. The earlier same-day bound of 305 came from a 4.37h window
# (1,331 actions) where gathering coverage was unknown -- both are lower
# bounds, the tighter window simply wastes less. Passive accrual is ~ZERO
# (that same Extended sat at 3/1,374 through hours of idle combat), so
# harvest contracts pay only while the player is actively gathering: quote
# hc per GATHER-hour, never per combat-hour.
HARVEST_PER_GATHER_HOUR = 700

# Typical best hc/combat-hour among a fresh board's contracts -- used only to
# price the opportunity cost of a carried contract occupying the active slot
# past reset. Eyeballed from the 31 Jul - 6 Aug boards (best pending contract
# ran 2.2-4.3 hc/combat-h); never fitted. Was an inline "~3" in the audit
# message until the 6 Aug public-release audit named it.
BOARD_TYPICAL_BEST_HC_PER_H = 3.0

# CI/CD Pipeline daily run budget per upgrade level. The install's own
# description states it ("Each level allows 5 ..."), and L3 = 15 was observed
# directly on 5-6 Aug 2026. In-game description text is primary evidence
# (CLAUDE.md); whether a mid-day level-up raises the SAME day's budget is
# unobserved (simulator-protocol.md par 9.2).
CICD_RUNS_PER_LEVEL = 5

# Credit income, measured from the stream ledger rather than assumed.
# Trailing-72h fit 6 Aug 2026 (23.8M/hr over 9.6h of play, ~7,000 fights);
# grows with the build, so expect upward drift -- the live check is
# trailing-window and will flag it.
CREDITS_PER_HOUR = 24e6

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
    # definitions is None when the capture lacks homelabInfo (lazy panel) --
    # 3 of the first 144 archive captures do, and this crashed `audit` on them.
    for d in (definitions or {}).get("installs") or []:
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
    newest_ms = latest_stream_ms()
    if cap_ms is None or newest_ms is None or newest_ms <= cap_ms:
        return None, []
    # Lag is measured against the newest record of ANY kind -- stats records
    # only append when combat stats change, so keying the lag to them went
    # silent during pure idling (31 Jul 2026). The field diff below still
    # needs a stats record newer than the capture; without one the lag stands
    # alone with an empty change list.
    stream_ms, player = latest_stream_player()
    if stream_ms is None or stream_ms <= cap_ms:
        player = {}
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
    return (newest_ms - cap_ms) / 1000, changed


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
#          * (1 + homelab_mult)
# Confirmed formula-level 27 Jul 2026 against the game's own totals on the
# 21:07 capture -- all five economy stats reproduce to <1e-9 with this and to
# -11% .. -23% without it. Identifiable because the capture carries both a
# firewall_cache=0.15 case (the four gathering resources) and a
# firewall_cache=0 case (credits) against a constant participation_bonus=0.5;
# every additive reading of either term fails both. Regime: only these two
# values have been observed -- if a capture ever shows a different
# participation_bonus or firewall_cache, `validate_stat_totals` re-checks it.
# `homelab_mult` added 31 Jul 2026 when Container Runtime L1 ("x1.01,
# multiplicative" per its own description) populated the field for the first
# time: audit's MODEL check flagged all four gathering stats at +0.52%, and
# (base + homelab + equipment) * 1.01 reproduces every one to <1e-9 (cycles
# 2.0648121516 * 1.01 = 2.0854602731 exact; credits, with homelab_mult=0,
# unchanged). The multiplier takes the WHOLE bracket including base -- same
# footing as participation/cache, matching the in-game description.
ECONOMY_MULT_KEYS = ("participation_bonus", "firewall_cache", "homelab_mult")
# everything else in stats_breakdown is gear-flat (regeneration, corruption,
# thorns, damage_barrier, armor_penetration) -> pool multiplies equipment_flat.
#
# ...but the homelab term does NOT join that pool for a gear-flat stat: it is
# added ALONGSIDE equipment_flat, inside the bracket the pool multiplies.
#   gear-flat:  total = (equipment_flat + homelab) * (1 + equipment_pct + hardware)
#   scaling:    total = (base + level + equipment_flat) * (1 + equipment_pct
#                                                          + hardware + homelab)
# Found 8 Aug 2026 by audit's MODEL self-check, the same detector that caught
# `homelab_mult` on the economy family on 31 Jul: Malware Sandbox L1
# ("Increases Corruption by 0.5% per level" -> homelab 0.005) populated the
# field for the first time on a gear-flat stat and the pool reading missed the
# game's total by +0.35%. (65 + 0.005) * 1.39 = 90.35695 reproduces it exactly,
# where 65 * 1.395 = 90.675 does not. The pool reading is ruled out for
# gear-flat and confirmed for scaling: on `accuracy` the same swap misses by
# -5.6%, so the two families genuinely differ.
#
# The plain reading is that the game credits a gear-flat stat with the RAW
# FRACTION as a flat addend -- 0.5% delivers +0.005 corruption, not +0.5% of
# 90.4 (+0.45). That is ~90x smaller than the description implies and is very
# likely a game-side bug; the model reproduces what the game does, not what it
# says. REGIME: ONE observation, one stat, one level -- corruption is the only
# gear-flat stat that has ever carried a non-zero homelab across all 159
# archived captures, and equipment_pct is 0 there, so this cannot yet
# distinguish `homelab * (1 + pct + hardware)` from `homelab * (1 + hardware)`
# (they differ by <0.01 corruption today). Malware Sandbox L2 is the forward
# test: it predicts total = (65 + 0.01) * 1.39 = 90.3639, against 91.00 under
# the pool reading. `validate_stat_totals` re-checks every capture, so a wrong
# form here cannot stay quiet.


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


def gear_flat_pool(breakdown):
    """Multiplier a gear-flat stat's `equipment_flat` actually receives.

    NOT `stat_pool`: the homelab term sits inside the bracket rather than in
    the pool for this family (see the note above ECONOMY_MULT_KEYS). Both
    `composed_stat_total` and `hardware_track_value` must read the multiplicand
    from here -- `hardware_track_value` re-derived the pool inline until 8 Aug
    2026, which is exactly the shape of duplication that hides a defect in one
    caller while the other is fixed.
    """
    b = breakdown or {}
    return stat_pool(b) - (b.get("homelab") or 0)


def economy_multiplier(breakdown):
    """Product of the multiplicative economy terms; 1.0 for combat stats."""
    b = breakdown or {}
    if not is_economy_breakdown(b):
        return 1.0
    mult = 1.0
    for key in ECONOMY_MULT_KEYS:
        mult *= 1 + (b.get(key) or 0)
    return mult


def composed_stat_total(breakdown, stat, d_equipment_pct=0.0, d_hardware=0.0,
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
    # gear-flat: homelab lands in the bracket, not the pool, so a homelab delta
    # moves the addend and must be taken back out of `pool`.
    homelab = (b.get("homelab") or 0) + d_homelab
    return (flat + homelab) * (pool - homelab)


def validate_stat_totals(capture, tolerance=1e-6):
    """[(stat, reported, modelled)] where `composed_stat_total` misses the game's total.

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
        reported, modelled = b["total"], composed_stat_total(b, stat)
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
# The experiment DECLARATIONS live in experiments.py -- the campaign record,
# quarantined from the library logic (public-release restructure, 6 Aug 2026).
# The reading logic (experiment_status / experiment_mechanism) stays here.
# Star-import is deliberate: experiments.py defines __all__, and cmd_ab's
# concluded-experiment scan walks vars(ihlib) expecting the dicts present.
from experiments import *  # noqa: E402,F401,F403 -- deliberate mid-file: section ordering



STREAM_DIR = DATA_ROOT / "combat-stream"


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
        # = dmg - rg - soak is directional). soak is pool DRAWDOWN per round
        # (pbs = start, pbf = final): once-per-fight shield, 0 refills across
        # 81K logged barrier rounds (1 Aug 2026). Until 1 Aug this summed the
        # pbs STOCK -- the exact error the 29 Jul Barrier weight refit
        # removed -- overstating absorption ~8-10x in every mechanism table.
        "dmg": f.get("damage_taken") or 0,
        "rg": sum(r.get("prg") or 0 for r in rounds),
        "soak": sum((r.get("pbs") or 0) - (r.get("pbf") or 0)
                    for r in rounds),
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


_STREAM_CACHE = {"key": None, "rows": None}


def stream_records(dir_=None):
    """Yield deduped ledger records from data/combat-stream/*.jsonl.

    Parsed once per process per ledger state (keyed on directory plus every
    file's mtime and size), because `ab`, `audit`, the register's live checks
    and `brief` all consume the same multi-MB ledger. The cached container is
    a TUPLE so a consumer cannot append/reorder, but the record dicts inside
    are still shared — treat them as read-only; a mutation corrupts every
    later consumer in the process (public-release audit finding; the full fix
    is a Ledger object owning copies, deferred).

    `dir_` overrides the ledger directory — the injection point tests use
    (matches `sim_records`' pattern).
    """
    base = Path(dir_) if dir_ else STREAM_DIR
    paths = sorted(base.glob("*.jsonl"))
    key = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size)
                for p in paths)
    if _STREAM_CACHE["key"] != key:
        rows = []
        for path in paths:
            for line in path.read_text().splitlines():
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        _STREAM_CACHE["key"], _STREAM_CACHE["rows"] = key, tuple(rows)
    yield from _STREAM_CACHE["rows"]


# ---- Hacking Simulator ------------------------------------------------------
# The Software Profiler (homelab 10) runs 100 fights against a CHOSEN enemy
# level in a chosen zone, with either the equipped loadout or a saved gear set,
# and returns wins/losses plus one fully-logged victory and one fully-logged
# loss. That is a controlled dose-response instrument: the live ledger can only
# observe the enemy levels the streak happens to visit, with gear changing
# underneath it.
#
# REGIME WARNING, and it decides what the profiler may be used for: each sim
# fight is an INDEPENDENT fight, not a continuing streak. `sim_regime_check`
# tests whether fights start at full HP; until that returns "full-hp", nothing
# here may be used to weight attrition stats (Regen, Barrier, Max HP), because
# a full-HP-start sample cannot see attrition at all. Mitigation and hit
# reliability are measurable either way.

SIM_DIR = DATA_ROOT / "sim-runs"

# Columnar compact combat log, ported from the client's
# inflateCombatLogCompact (vendor/game-js/hacking.js). `bm` is a per-round
# bitmask: bit 0 = player barrier fields present, bit 1 = enemy barrier.
COMPACT_SCALARS = ("pa", "ph", "pc", "ea", "eh", "ec", "php", "ehp", "pls",
                   "prg", "erg", "ptd", "pcd", "etd", "ecd", "srh", "ecs",
                   "ecx")
COMPACT_FLAGS = ("pm", "em", "el", "sr")


def inflate_compact_combat_log(compact):
    """Expand a `combat_log_compact` block into the per-round dicts the rest
    of the toolkit (and data-dictionary.md) already speak."""
    if not compact or not isinstance(compact, dict):
        return []
    n = int(compact.get("n") or 0)
    if n <= 0:
        return []

    def col(name):
        value = compact.get(name)
        return value if isinstance(value, list) else []

    rounds = []
    for i in range(n):
        row = {"r": i + 1}
        for name in COMPACT_SCALARS:
            values = col(name)
            row[name] = values[i] if i < len(values) else 0
        for name in COMPACT_FLAGS:
            values = col(name)
            row[name] = bool(values[i]) if i < len(values) else False
        mask = 0
        bm = col("bm")
        if i < len(bm):
            mask = int(bm[i] or 0)
        if mask & 1:
            for name in ("pbs", "pbf"):
                values = col(name)
                row[name] = values[i] if i < len(values) else 0
        if mask & 2:
            for name in ("ebs", "ebf"):
                values = col(name)
                row[name] = values[i] if i < len(values) else 0
        rounds.append(row)
    return rounds


# ---------------------------------------------------------------------------
# COMBAT LAWS -- measured 29 Jul 2026 from Software Profiler sweeps.
# These are mechanisms, not weights: they take the enemy's own stat line
# (which every profiler fight carries) and return the game's behaviour.

# Hit chance. Fitted on the UNBIASED 2-attack-round sample (1,004 rounds, 32
# fights, enemy evasion 3,002-7,699, player Accuracy 9,226.9). The ratio-power
# form p = acc^k/(acc^k+eva^k) is REJECTED.
#
# THE DENOMINATOR MATTERS AND IT BIT ONCE. `pm` is a per-round flag meaning
# "the FIRST attack missed" (client: "First hit misses, but N hits land"), not
# a miss count -- so hits/(hits+missflags) SILENTLY OVERSTATES hit rate,
# because a round whose first attack hits and second misses is indistinguish-
# able from a 1-attack round. That estimator gave 0.757 where the truth is
# 0.638, and a first fit of 0.532 + 1.208*ln(Acc/Eva) was shipped from it.
# The clean sample is 2-attack rounds only, identified WITHOUT knowing the
# attack count: ph=2,pm=0 (both hit) vs ph=1,pm=1 (first missed, second hit),
# so p = n(2,0)/(n(2,0)+n(1,1)). The model self-validates three ways --
# predicted n(0,1) 335 vs 354 observed, total rounds 1,930 vs 1,949, and
# implied attacks/round 1.815 vs the AttackSpeed stat of 1.8458.
HIT_LOGIT_A = -0.164
HIT_LOGIT_B = 1.420


def hit_chance(accuracy, evasion):
    """logit(p) = -0.164 + 1.420 * ln(Accuracy / Evasion)  (HIT_LOGIT_A/_B).

    Resolves open question §7. Fitted range: Acc/Eva ratio 1.20-3.07. At the
    ratios this build actually fights at (streak 120-159 faces evasion
    4,857-5,386) true per-attack hit rate is 65-68% -- nowhere near saturated,
    which retires the 'Accuracy is saturated' reading of 27 Jul and makes
    Accuracy worth roughly DOUBLE what the biased first fit (0.532 + 1.208
    ln(r), from the pm-denominator artefact -- see the block comment above)
    implied. Until 6 Aug 2026 this docstring quoted that retired fit while
    the constants three lines up held the corrected one."""
    z = HIT_LOGIT_A + HIT_LOGIT_B * math.log(accuracy / evasion)
    return 1.0 / (1.0 + math.exp(-z))


# Damage mitigation. Same functional form fits BOTH directions independently:
# outgoing K = 190.2 (32 fights vs enemy Defense 743-1,990), incoming
# K = 219.3 (28 fights, our Defense 1,487, enemy ArmorPen 26-406).
DAMAGE_K = 205.0


def damage_multiplier(defense, armor_pen=0.0, k=DAMAGE_K):
    """dmg_dealt = AttackDamage * K / (K + Defense - ArmorPen).

    Resolves open question §8. Consequences: Defense elasticity is
    -Defense/(K+Defense) = -0.88 at our 1,487, and ArmorPen is worth far more
    than its face value looks -- +97 points (10 -> 107) is +6.1% output
    against enemy Defense 1,500, which validates the inherited weight of 0.05
    at 0.044-0.051 in the operating range."""
    return k / (k + max(defense - armor_pen, 0.0))


# Corruption's healing-reduction rider. MEASURED 29 Jul 2026 on 288/288
# Software Profiler rounds (residual exactly 0.0 over the 190 non-capped ones),
# across 4 enemy classes and 2 enemy levels. See mechanics.md §17.
CORRUPT_REGEN_SUPPRESSION = 1.5


def realized_regen(regeneration, ecd, missing_hp):
    """The game's own `prg`, from first principles.

    prg = clamp(Regeneration - 1.5*ecd, 0, max_hp - php)

    Incoming corruption destroys 1.5 HP/round of regeneration per point ON TOP
    of the damage it deals, so incoming corruption costs ~2.5x face value; and
    regeneration is truncated to missing HP, so a listed-regen buy realizes
    NOTHING near full HP and 1:1 once depleted."""
    return max(0.0, min(regeneration - CORRUPT_REGEN_SUPPRESSION * ecd,
                        missing_hp))


def gross_regen(prg, ecd):
    """Undo the corruption suppression to recover gross regeneration.

    `prg` is NET. Any cross-cohort comparison of realized regeneration must
    either use this or segment by enemy corruption -- comparing raw Sum(prg)
    between a high-corruption and a low-corruption cohort measures the
    opponents, not the build (data-dictionary.md)."""
    return prg + CORRUPT_REGEN_SUPPRESSION * ecd


def sim_key(run):
    """Content identity for a simulator run. Results carry no server id, and
    the userscript re-sends the same live binding until the player runs
    again, so dedupe hashes the whole result body."""
    body = json.dumps(run.get("result"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(body.encode()).hexdigest()[:16]


def sim_records(path=None):
    """Yield deduped simulator records from data/sim-runs/*.jsonl.

    Dedupe is by the record's content `key`, keeping the earliest
    occurrence. The hub's own dedup was day-scoped until 5 Aug 2026, so the
    ledger holds cross-day re-ingests of the profiler panel's last-10
    results (all of 2026-08-01 and 2026-08-03 duplicate 30 Jul runs); the
    files are immutable, so the accessor is where they are filtered."""
    paths = [path] if path else sorted(SIM_DIR.glob("*.jsonl"))
    seen = set()
    for p in paths:
        if not Path(p).exists():
            continue
        for line in Path(p).read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            key = record.get("key")
            if key is not None:
                if key in seen:
                    continue
                seen.add(key)
            yield record


def sim_ledger_duplicates(after=None):
    """Count sim-ledger rows whose key already appeared in an earlier file.

    Hub-regression sentinel (audit): the hub's write-side dedup was
    day-scoped until 5 Aug 2026 and re-ingested the profiler panel's
    last-10 results once per day. `after` (YYYY-MM-DD) scopes the count to
    files dated later, so the 20 grandfathered pre-fix rows (filtered at
    read time by sim_records) do not flag forever."""
    seen = set()
    dupes = 0
    for p in sorted(SIM_DIR.glob("*.jsonl")):
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            key = json.loads(line).get("key")
            if key in seen and (after is None or p.stem > after):
                dupes += 1
            seen.add(key)
    return dupes


def unbiased_hit_rate(rounds, hit_key="ph", miss_key="pm"):
    """True per-attack hit rate from a round log.

    `pm`/`em` flag only that the FIRST attack of the round missed, so the
    obvious hits/(hits+missflags) overstates accuracy. Restrict to rounds that
    are provably 2-attack -- (2 hits, no flag) or (1 hit, flag) -- where the
    flag alone decides the first attack's outcome. Returns (hits, trials)."""
    both = sum(1 for x in rounds
               if (x.get(hit_key) or 0) == 2 and not x.get(miss_key))
    split = sum(1 for x in rounds
                if (x.get(hit_key) or 0) == 1 and x.get(miss_key))
    return both, both + split


def _sim_fight_row(fight):
    """Per-fight measurements from a profiler's logged victory/loss."""
    if not isinstance(fight, dict):
        return None
    rounds = inflate_compact_combat_log(fight.get("combat_log_compact")) or \
        fight.get("combat_log") or []
    hits = sum(r.get("ph") or 0 for r in rounds)
    misses = sum(1 for r in rounds if r.get("pm"))
    enemy = fight.get("enemy_stats") or {}
    shp, mhp = fight.get("starting_hp"), fight.get("max_hp")
    return {
        "victory": bool(fight.get("victory")),
        "enemy_class": fight.get("enemy_class"),
        "enemy_level": fight.get("enemy_level"),
        "rounds": len(rounds),
        "hits": hits,
        "misses": misses,
        "attacks": hits + misses,
        # NOTE: naive_hit_rate is BIASED HIGH (see unbiased_hit_rate). Kept
        # only for continuity with pre-29-Jul figures; never fit on it.
        "naive_hit_rate": hits / (hits + misses) if hits + misses else None,
        "hit_hits": unbiased_hit_rate(rounds)[0],
        "hit_trials": unbiased_hit_rate(rounds)[1],
        "hit_rate": (lambda h, t: h / t if t else None)(*unbiased_hit_rate(rounds)),
        "enemy_hit_hits": unbiased_hit_rate(rounds, "eh", "em")[0],
        "enemy_hit_trials": unbiased_hit_rate(rounds, "eh", "em")[1],
        "enemy_evasion": enemy.get("effective_evasion"),
        "enemy_accuracy": enemy.get("effective_accuracy"),
        "enemy_defense": enemy.get("effective_defense"),
        "enemy_attack": enemy.get("effective_attack_damage"),
        "enemy_stats": enemy,
        # gross intake and its recovery offsets (data-dictionary.md: prefixes
        # are the OWNER of the effect -- ecd is the ENEMY'S corruption, i.e.
        # damage dealt TO the player)
        "dmg_out": sum(r.get("pa") or 0 for r in rounds),
        "dmg_in": sum(r.get("ea") or 0 for r in rounds),
        "corrupt_in": sum(r.get("ecd") or 0 for r in rounds),
        "corrupt_out": sum(r.get("pcd") or 0 for r in rounds),
        "regen": sum(r.get("prg") or 0 for r in rounds),
        "starting_hp": shp,
        "max_hp": mhp,
        "final_hp": fight.get("final_hp"),
        "start_frac": (shp / mhp) if shp is not None and mhp else None,
        "rounds_detail": rounds,
    }


def sim_rows(mode="software_profiler", path=None):
    """One row per simulator run, with the logged fights parsed out."""
    rows = []
    for record in sim_records(path):
        if record.get("kind") != "sim":
            continue
        if mode and record.get("mode") != mode:
            continue
        result = record.get("result") or {}
        form = record.get("form") or {}
        context = record.get("context") or {}
        fights = [f for f in (_sim_fight_row(result.get("first_victory")),
                              _sim_fight_row(result.get("first_loss")))
                  if f]
        wins = result.get("wins") or 0
        losses = result.get("losses") or 0
        rows.append({
            "key": record.get("key"),
            "seen_ms": record.get("seen_ms"),
            "mode": record.get("mode"),
            "zone": result.get("zone_name") or result.get("zone_id"),
            "enemy_level": result.get("requested_enemy_level"),
            "n": result.get("simulation_count") or (wins + losses),
            "wins": wins,
            "losses": losses,
            "win_rate": result.get("win_rate"),
            "loss_archetype": result.get("most_common_loss_enemy_archetype"),
            # which loadout produced it -- "current" or a saved gear set
            "gear": form.get("profilerGearID") or "current",
            "hack_level": context.get("hack_level"),
            "combat_stats": context.get("combat_stats") or {},
            "fights": fights,
        })
    rows.sort(key=lambda r: (r.get("seen_ms") or 0))
    return rows


def cicd_rows(path=None):
    """One row per CI/CD Pipeline run. Each run is `sims` full-streak
    simulations; the game returns only their aggregate (avg/min/max of
    final_streak etc.) plus best/worst run detail, so the run-average is
    the unit of analysis. `gear_set` is the player-chosen label — identify
    arms from `player_combat_stats`, never from the label (the 5 Aug first
    use had A=post-craft, B=pre-craft, the reverse of the instruction)."""
    rows = []
    for record in sim_records(path):
        if record.get("kind") != "sim" or record.get("mode") != "cicd_pipeline":
            continue
        res = record.get("result") or {}
        agg = res.get("aggregate") or {}
        fs = agg.get("final_streak") or {}
        arch = agg.get("most_common_final_enemy_archetype") or {}
        rows.append({
            "key": record.get("key"),
            "seen_ms": record.get("seen_ms"),
            "zone": res.get("zone_name") or res.get("zone_id"),
            "gear_set": res.get("gear_set_name") or res.get("gear_mode") or "current",
            "gear_set_id": res.get("gear_set_id"),
            "sims": res.get("simulation_count"),
            "starting_streak": res.get("starting_streak"),
            "streak_avg": fs.get("average"),
            "streak_min": fs.get("min"),
            "streak_max": fs.get("max"),
            "loss_archetype": arch.get("class"),
            "player_combat_stats": res.get("player_combat_stats") or {},
            "credits_per_hour": (agg.get("credits_per_hour_without_buffs") or {}).get("average"),
            "xp_per_hour": (agg.get("xp_per_hour_without_buffs") or {}).get("average"),
            "chips_per_hour": (agg.get("chips_per_hour_expected_without_buffs") or {}).get("average"),
            "daily_used": res.get("daily_used"),
            "daily_limit": res.get("daily_limit"),
        })
    rows.sort(key=lambda r: (r.get("seen_ms") or 0))
    return rows


def sim_regime_check(rows=None):
    """Does the profiler start every fight at full HP?

    This is the FIRST thing to establish and it gates every later use: if
    fights start full, the profiler measures single-fight win probability and
    is blind to attrition, so it cannot price Regen/Barrier/Max HP. Returns
    (verdict, detail)."""
    rows = sim_rows() if rows is None else rows
    fracs = [f["start_frac"] for r in rows for f in r["fights"]
             if f.get("start_frac") is not None]
    if not fracs:
        return "unknown", "no logged fights captured yet"
    full = sum(1 for f in fracs if f > 0.999)
    lo, hi = min(fracs), max(fracs)
    if full == len(fracs):
        return "full-hp", (
            f"all {len(fracs)} logged fights start at 100% HP — the profiler "
            "measures SINGLE-FIGHT win probability and cannot see attrition; "
            "do not fit Regen/Barrier/MaxHP weights from it")
    if full == 0:
        return "carried-hp", (
            f"{len(fracs)} logged fights start at {lo:.1%}-{hi:.1%} HP — HP "
            "carries between sim fights, so the profiler DOES model attrition")
    return "mixed", (
        f"{full}/{len(fracs)} logged fights start full; range "
        f"{lo:.1%}-{hi:.1%} — inspect before fitting anything")


# ---- Streak simulator ------------------------------------------------------
# Forward model of a whole streak, built ONLY from laws measured in this
# workspace, so perturbing a player stat gives that stat's value in STREAKS --
# the actual objective. Exists because the Software Profiler runs full-HP
# SINGLE fights and is structurally blind to attrition, which is ~100% of how
# runs end (decision-log.md, 29 Jul: the player dies at median enemy level
# 1,798 where the profiler wins 300/300).
#
# Laws used, all measured:
#   hit chance         logit = -0.164 + 1.420*ln(acc/eva)      mechanics.md §18
#   damage            Atk * K/(K + Def - ArmorPen), K~205      mechanics.md §18
#   regeneration      clamp(Regen - 1.5*ecd, 0, missing_hp)    mechanics.md §17
#   barrier           absorbs exactly its value once per fight mechanics.md §16
#   corruption        ~6 x stat per round at full stack        mechanics.md §19
#   thorns            = stat per enemy hit landed              mechanics.md §19
#   post-combat heal  5 * hack_level * 0.99^(streak-10)        mechanics.md §3
#
# Enemy stats come from per-class power-law fits of the ledger's own
# `enemy_stats` (17,751 fights), and enemy level from the recent ledger's
# streak->level curve, which is near-deterministic (+-1.6-2.6% spread).

CORRUPT_STACK_CAP = 6           # measured max ecd/round ~= 6x the stat

# Enemy-level growth per streak past the deepest OBSERVED level-curve point,
# used only when the streak simulator extrapolates beyond live data. Was an
# inline 0.011 with no register row from first light to 6 Aug 2026 (the
# public-release audit named it); the value eyeballs the observed curve's
# deep-end slope and has never been fitted on its own.
ENEMY_LEVEL_GROWTH_PER_STREAK = 1.011


def _fight_ledger_rows():
    rows = [r for r in stream_records() if r.get("kind") == "fight"]
    rows.sort(key=lambda r: r.get("seen_ms") or 0)
    return rows


def enemy_level_curve(recent=4000, rows=None):
    """{streak: median enemy level} from the RECENT ledger only.

    Must be recent: enemy level tracks player level too, which rose
    1,031 -> 1,283 over the archive, so a pooled fit understates the curve."""
    rows = rows or _fight_ledger_rows()
    buckets = {}
    for r in rows[-recent:]:
        f = r["fight"]
        st, lv = f.get("current_win_streak"), f.get("enemy_level")
        if st is not None and lv and f.get("victory"):
            buckets.setdefault(int(st), []).append(lv)
    return {s: statistics.median(v) for s, v in buckets.items() if len(v) >= 3}


def enemy_stat_fits(rows=None, min_obs=20):
    """{(class, field): (A, B)} for enemy_stat = A * enemy_level**B."""
    fields = ("attack_damage", "effective_accuracy", "effective_defense",
              "effective_evasion", "corruption", "thorns", "max_hp",
              "attack_speed", "effective_armor_penetration",
              "effective_crit_chance", "effective_crit_damage",
              "damage_barrier")
    rows = rows or _fight_ledger_rows()
    obs = {}
    for r in rows:
        f = r["fight"]
        es, c, lv = f.get("enemy_stats") or {}, f.get("enemy_class"), f.get("enemy_level")
        if not (c and lv and es):
            continue
        for k in fields:
            v = es.get(k)
            if v and v > 0:
                obs.setdefault((c, k), []).append((lv, v))
    fits = {}
    for key, pts in obs.items():
        if len(pts) < min_obs:
            continue
        xs = [math.log(x) for x, _ in pts]
        ys = [math.log(y) for _, y in pts]
        n = len(xs)
        sx, sy = sum(xs), sum(ys)
        sxx = sum(x * x for x in xs)
        sxy = sum(x * y for x, y in zip(xs, ys, strict=True))
        denom = n * sxx - sx * sx
        if abs(denom) < 1e-12:
            continue
        b = (n * sxy - sx * sy) / denom
        fits[key] = (math.exp((sy - b * sx) / n), b)
    return fits


def _enemy_at(fits, cls, level):
    def g(field, default=0.0):
        f = fits.get((cls, field))
        return f[0] * level ** f[1] if f else default
    return {
        "atk": g("attack_damage"), "acc": g("effective_accuracy"),
        "dfn": g("effective_defense"), "eva": g("effective_evasion"),
        "corrupt": g("corruption"), "thorns": g("thorns"),
        "hp": g("max_hp"), "spd": g("attack_speed", 1.0),
        "apen": g("effective_armor_penetration"),
        "crit_ch": g("effective_crit_chance"), "crit_dm": g("effective_crit_damage", 1.5),
        "barrier": g("damage_barrier"),
    }


def player_combat_stats(capture=None):
    """Our combat stats in the simulator's own vocabulary."""
    cap = capture or load_capture()[0]
    cs = (cap["state"].get("currentPlayer") or {}).get("combat_stats") or {}
    sb = cap["state"].get("statsBreakdown") or {}
    def sbt(name, fallback):
        d = sb.get(name)
        return d.get("total") if isinstance(d, dict) and d.get("total") else fallback
    return {
        "max_hp": sbt("max_hp", cs.get("MaxHP", 0)),
        "atk": sbt("attack_damage", cs.get("AttackDamage", 0)),
        "dfn": sbt("defense", cs.get("Defense", 0)),
        "eva": sbt("evasion", cs.get("Evasion", 0)),
        "acc": sbt("accuracy", cs.get("Accuracy", 0)),
        "spd": sbt("attack_speed", cs.get("AttackSpeed", 1.0)),
        "crit_ch": sbt("crit_chance", cs.get("CritChance", 0)),
        "crit_dm": sbt("crit_damage", cs.get("CritDamage", 1.5)),
        "regen": cs.get("Regeneration", 0),
        "barrier": cs.get("DamageBarrier", 0),
        "apen": cs.get("ArmorPenetration", 0),
        "thorns": cs.get("Thorns", 0),
        "corrupt": cs.get("Corruption", 0),
    }


def _attacks_this_round(speed, rng):
    """Fractional attack speed = that many attacks, remainder as a coin."""
    whole = int(speed)
    return whole + (1 if rng.random() < speed - whole else 0)


def simulate_fight(p, e, hp, rng, max_rounds=400):
    """One fight from `hp`. Returns (won, hp_after, rounds)."""
    ehp = e["hp"]
    p_shield, e_shield = p["barrier"], e["barrier"]
    p_stacks = e_stacks = 0
    p_hit = hit_chance(p["acc"], e["eva"])
    e_hit = hit_chance(e["acc"], p["eva"])
    p_dmg = p["atk"] * damage_multiplier(e["dfn"], p["apen"])
    e_dmg = e["atk"] * damage_multiplier(p["dfn"], e["apen"])
    for rnd in range(1, max_rounds + 1):
        # --- incoming ---
        incoming = 0.0
        landed = 0
        for _ in range(_attacks_this_round(e["spd"], rng)):
            if rng.random() < e_hit:
                landed += 1
                d = e_dmg
                if rng.random() < e["crit_ch"]:
                    d *= e["crit_dm"]
                incoming += d
        if landed:
            e_stacks = min(e_stacks + landed, CORRUPT_STACK_CAP)
        ecd = e["corrupt"] * e_stacks
        incoming += ecd
        # our thorns reflect on each enemy hit that landed
        ehp -= p["thorns"] * landed
        # barrier absorbs every channel, once, up to its value
        if p_shield > 0:
            used = min(p_shield, incoming)
            p_shield -= used
            incoming -= used
        hp -= incoming
        if hp <= 0:
            return False, 0.0, rnd
        # regeneration: NET of the corruption rider, capped at missing HP
        hp += realized_regen(p["regen"], ecd, p["max_hp"] - hp)
        # --- outgoing ---
        outgoing = 0.0
        our_landed = 0
        for _ in range(_attacks_this_round(p["spd"], rng)):
            if rng.random() < p_hit:
                our_landed += 1
                d = p_dmg
                if rng.random() < p["crit_ch"]:
                    d *= p["crit_dm"]
                outgoing += d
        if our_landed:
            p_stacks = min(p_stacks + our_landed, CORRUPT_STACK_CAP)
        outgoing += p["corrupt"] * p_stacks
        hp -= e["thorns"] * our_landed          # enemy thorns reflect on us
        if hp <= 0:
            return False, 0.0, rnd
        if e_shield > 0:
            used = min(e_shield, outgoing)
            e_shield -= used
            outgoing -= used
        ehp -= outgoing
        if ehp <= 0:
            return True, hp, rnd
    return True, hp, max_rounds


def simulate_streak(p, hack_level, level_curve, fits, rng, max_streak=400):
    """Run one streak to death. Returns (streak_reached, fights)."""
    classes = sorted({c for c, _ in fits})
    hp = p["max_hp"]
    streak = 0
    levels = sorted(level_curve)
    lo, hi = levels[0], levels[-1]
    while streak < max_streak:
        key = min(max(streak, lo), hi)
        level = level_curve.get(key) or level_curve[min(levels, key=lambda s: abs(s - key))]
        if streak > hi:                       # extrapolate past observed depth
            level *= ENEMY_LEVEL_GROWTH_PER_STREAK ** (streak - hi)
        # uniform class draw is measured, not assumed: the ledger shows
        # 10.7-11.5% per class across all 9 enemy classes
        e = _enemy_at(fits, rng.choice(classes), level)
        won, hp, _rounds = simulate_fight(p, e, hp, rng)
        if not won:
            return streak
        streak += 1
        # post-combat heal: 5 * hack_level, decaying 0.99^(streak-10)
        heal = 5.0 * hack_level * (0.99 ** max(0, streak - 10))
        hp = min(p["max_hp"], hp + heal)
    return max_streak


def streak_distribution(p, hack_level, trials=300, seed=12345,
                        level_curve=None, fits=None):
    """Death-streak distribution for a stat vector. Returns sorted list."""
    rng = random.Random(seed)
    level_curve = level_curve if level_curve is not None else enemy_level_curve()
    fits = fits if fits is not None else enemy_stat_fits()
    return sorted(simulate_streak(p, hack_level, level_curve, fits, rng)
                  for _ in range(trials))


def fight_cadence(since_ms=None, zone="corporate_network", max_gap_s=900,
                  dir_=None):
    """[(ended_at_ms, seconds_per_fight)] measured from the game's own clock.

    Elapsed between consecutive deaths divided by the fights between them
    (`streak_ended` + 1). Deaths carry a server `ended_at_ms`, so this is the
    only wall-clock measure in the toolkit that does not go through the
    auto-stream's 150 s polling interval -- pooling `seen_ms` gaps instead
    just re-measures the poll rate, which is how this was nearly got wrong.

    Measured 27 Jul 2026 at 4.872 s/fight (sd 0.053, n=29), invariant across
    every loadout change that day including a +9.9% Attack Speed equip that
    moved it 0%. RE-READ 1 Aug 2026: the tick ERA-STEPS -- daily medians
    4.873 -> 4.750 -> 4.788 -> 4.605 -> 4.641 -> 4.666 over 27 Jul-1 Aug,
    within-era sd ~0.01, mover unidentified (not rounds/fight, r=0.42; not
    AtkSpd). Current era ~4.65 -> ~774 fights/hour. See mechanics.md §14:
    within an era the tick is fixed, so **attack speed is still not income**
    -- it pays in rounds per fight, i.e. fewer enemy attacks per fight, i.e.
    mitigation. Anything claiming a stat buys "fights per hour" is wrong
    until this function says otherwise; quote FIGHT_CADENCE_S, not 4.872.
    """
    deaths = {}
    for record in stream_records(dir_):
        if record.get("kind") != "death":
            continue
        entry = record.get("death") or {}
        if entry.get("ended_at_ms"):
            deaths[entry["ended_at_ms"]] = entry
    out = []
    ordered = sorted(deaths.items())
    for (ms0, _prev), (ms1, entry) in zip(ordered, ordered[1:],
                                          strict=False):
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
    exp = experiment or ACTIVE_EXPERIMENT  # noqa: F405
    # A concluded experiment left as ACTIVE_EXPERIMENT must read as "no active
    # experiment" -- but only on the implicit path: passing one explicitly is
    # the documented retrospective-analysis route and must keep working.
    if exp is None or (experiment is None and exp.get("concluded")):
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
        cap_ms = captured_ms(cap)  # local was named captured_ms until 6 Aug
                                   # 2026, shadowing this very function
        for entry in state.get("recentLossStreaks") or []:
            ms = entry.get("ended_at_ms")
            if ms:
                deaths[ms] = entry
        log = state.get("combatLog") or []
        ids = [f.get("id") for f in log if f.get("id") is not None]
        capture_pre = cap_ms is not None and cap_ms < exp["equip_ms"]
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
            _absorb_fight(fights, f, post, cap_ms)
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
    # None -> no mid-window segment declared, so NOTHING is after it. This
    # used to fall back to `post_deaths`, which made "no boundary declared"
    # print identically to "every death is past the boundary" (7 Aug 2026):
    # shell-ab-2026-08-07 declares segment_ms None and the readout still
    # announced all 29 deaths as post-segment, over a hardcoded VLAN label
    # belonging to a July experiment. A false contamination warning on a
    # clean window is as costly as a missed real one -- it argues for
    # discounting a result that needs no discount.
    segment_ms = exp.get("segment_ms")
    segmented = ([e for e in post_deaths if e["ended_at_ms"] >= segment_ms]
                 if segment_ms else [])
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
            seg_ms = exp.get("segment_ms")  # None -> no mid-window segment
            era = "post-seg" if seg_ms and ms and ms >= seg_ms else "post"
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
