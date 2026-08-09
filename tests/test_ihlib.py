"""Seed test suite — the eight highest-confidence-per-line tests from the
public-release audit (6 Aug 2026). unittest-style on purpose: the project is
zero-dependency, so the suite must run on a bare interpreter with
`python3 -m unittest discover tests`. pytest runs it unchanged in CI.

Each test names the incident it guards against where one exists; regression
tests without a story are just tests, but most of these have one.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

# Point at an EMPTY data tree BEFORE importing ihlib, which resolves its data
# paths at import time. This is deliberately here and not only in
# tests/__init__.py: `python -m unittest discover tests` (what CI runs) makes
# `tests/` the top-level directory, so the package __init__ is never imported
# and isolation set up there silently does not apply. `setdefault` keeps the
# two in agreement. Without it the suite reads whatever captures happen to be
# on disk — green locally, red in CI (7 Aug 2026).
os.environ.setdefault("IH_DATA_DIR", tempfile.mkdtemp(prefix="ih-tests-data-"))

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import ihlib  # noqa: E402

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "capture-fixture.json").read_text())


class StatModelTest(unittest.TestCase):
    """Locks the whole stat-composition family model to game ground truth."""

    def test_every_fixture_stat_reproduces(self):
        self.assertEqual(ihlib.validate_stat_totals(FIXTURE), [])

    def test_composed_stat_total_moves_with_deltas(self):
        breakdowns = FIXTURE["state"]["statsBreakdown"]
        stat, b = next((s, b) for s, b in sorted(breakdowns.items())
                       if isinstance(b, dict) and "total" in b
                       and b["total"])
        base = ihlib.composed_stat_total(b, stat)
        moved = ihlib.composed_stat_total(b, stat, d_equipment_pct=0.10)
        self.assertGreater(moved, base)

    def test_gear_flat_homelab_is_an_addend_not_a_pool_term(self):
        """Ground truth from the 8 Aug 2026 07:40 capture, where Malware
        Sandbox L1 put a non-zero homelab on a gear-flat stat for the first
        time in 159 captures. The suite was green with `flat * pool` (which
        gives 90.675) because no fixture exercised the case -- audit's MODEL
        self-check caught it, not the tests. Numbers below are the game's own,
        not re-derived from the model."""
        b = {"base": 0, "level": 0, "equipment_flat": 65, "equipment_pct": 0,
             "hardware": 0.39, "homelab": 0.005, "homelab_flat": 0,
             "syndicate": 0, "total": 90.35695}
        self.assertAlmostEqual(
            ihlib.composed_stat_total(b, "corruption"), 90.35695, places=9)
        # the pool reading, explicitly ruled out
        self.assertNotAlmostEqual(
            ihlib.composed_stat_total(b, "corruption"), 90.675, places=3)
        # a homelab delta moves the addend, not the multiplier: Malware
        # Sandbox L2 predicts (65 + 0.01) * 1.39, NOT 65 * 1.40
        self.assertAlmostEqual(
            ihlib.composed_stat_total(b, "corruption", d_homelab=0.005),
            90.3639, places=9)

    def test_scaling_homelab_stays_in_the_pool(self):
        """The other half of the same finding: the families genuinely differ,
        so fixing gear-flat must not be generalised to scaling stats."""
        b = {"base": 100, "level": 7356, "equipment_flat": 0,
             "equipment_pct": 0.678920309838818, "hardware": 0.5,
             "homelab": 0.13, "homelab_flat": 0, "syndicate": 0,
             "total": 17215.309830158225}
        self.assertAlmostEqual(
            ihlib.composed_stat_total(b, "accuracy"), 17215.309830158225,
            places=6)

    def test_suspect_free_plan_never_loses_to_the_rescored_raw_plan(self):
        """The invariant `locks` violated on 8 Aug 2026.

        It priced every base by re-scoring the RAW-optimal plan ex-suspect.
        That plan spends Stability where raw score is highest, so when a
        flagged family wins the greedy search the ex-suspect reading measures a
        contract nobody would run -- and the recommender released
        `Shielded Analyzer of Puncturing` (best Analyzer base, ex-suspect +70.9
        once re-planned) to the AT RISK deletion list at +43.4. Re-planning
        under the disbelieving weights is a MAXIMUM over plans, so it can never
        be worse than any single plan scored the same way.
        """
        sf = ihlib.suspect_free_weights()
        ladders = ihlib.tier_ladders(FIXTURE)
        checked = 0
        for where, _slot, item in ihlib.iter_items(FIXTURE):
            if where != "inventory" or not (item.get("stability") or 0):
                continue
            raw_plan = ihlib.plan_craft(item, ladders)
            sf_plan = ihlib.plan_craft(item, ladders, weights=sf)
            self.assertGreaterEqual(
                ihlib.weighted_score(sf_plan["totals"], sf),
                ihlib.weighted_score(raw_plan["totals"], sf) - 1e-9,
                f"{item.get('name')}: re-planning ex-suspect lost to the "
                f"raw plan re-scored, which is impossible for a maximum")
            checked += 1
        self.assertGreater(checked, 0, "fixture exercised no craftable item")

    def test_suspect_free_weights_drop_every_flagged_family(self):
        pct, flat = ihlib.suspect_free_weights()
        self.assertTrue(ihlib.SUSPECT_WEIGHTS, "registry emptied by accident")
        for label in ihlib.SUSPECT_WEIGHTS:
            self.assertNotIn(label, pct)
            self.assertNotIn(label, flat)
        # and it is a copy, not a view onto the live weights
        self.assertIn("ArmorPen", flat)

    def test_one_suspect_registry_feeds_hardware_and_crafts(self):
        """`hardware` kept its own dict and printed the Barrier caveat while
        `potential`/`locks` ranked Barrier at face value (8 Aug 2026).

        Asserts the STRUCTURAL property — the hardware panel and the craft
        panels read one registry — rather than any particular membership.
        The first version of this test pinned "Barrier" by name and went red
        the same evening when the dedicated pair measured Barrier and it
        graduated out of the registry, which is a test pinning today's answer
        instead of the invariant.
        """
        suspect_ids = [sid for sid, label in ihlib.STAT_LABELS.items()
                       if label in ihlib.SUSPECT_WEIGHTS]
        self.assertTrue(suspect_ids, "no suspect family maps to a game stat")
        for sid in suspect_ids:
            note = ihlib.hardware_track_depth_note(
                {"effects": [{"combat_stat": sid, "additive_per_level": 0.01}]})
            self.assertIsNotNone(
                note, f"hardware does not warn on suspect family {sid}")
            self.assertIn(ihlib.stat_label(sid), note)
        # ...and a family NOT in the registry must not be warned about, or the
        # marker means nothing
        clean = next((sid for sid, label in ihlib.STAT_LABELS.items()
                      if label not in ihlib.SUSPECT_WEIGHTS), None)
        self.assertIsNotNone(clean)
        self.assertIsNone(ihlib.hardware_track_depth_note(
            {"effects": [{"combat_stat": clean, "additive_per_level": 0.01}]}))

    def test_gear_flat_pool_is_the_single_multiplicand_source(self):
        """`hardware_track_value` re-derived this pool inline until 8 Aug 2026.
        Two producers of one number is how a fix lands in one caller only."""
        b = {"equipment_pct": 0.0, "hardware": 0.39, "homelab": 0.005}
        self.assertAlmostEqual(ihlib.gear_flat_pool(b), 1.39, places=9)
        self.assertAlmostEqual(ihlib.stat_pool(b), 1.395, places=9)


class ContractSimulationTest(unittest.TestCase):
    """Guards the deepen-scale bug (30-31 Jul 2026): `simulate_contract`
    called without `baseline` returned ABSOLUTE post-craft scores that were
    read as deltas, corrupting three grades and re-fitting UPGRADE_BAND to a
    phantom ±16."""

    def setUp(self):
        self.item = FIXTURE["state"]["inventoryData"]["items"][0]
        self.ladders = ihlib.tier_ladders(FIXTURE)
        plan = ihlib.plan_craft(self.item, self.ladders)
        self.phases = [(uid, to) for uid, _label, _from, to, _att, _meas
                       in plan["steps"]]

    def test_baseline_shifts_not_rescales(self):
        phases = self.phases
        if not phases:
            self.skipTest("fixture item has no plannable phases")
        absolute = ihlib.simulate_contract(
            self.item, self.ladders, phases, trials=2000, seed=7)
        shifted = ihlib.simulate_contract(
            self.item, self.ladders, phases, trials=2000, seed=7,
            baseline=50.0)
        self.assertAlmostEqual(
            absolute["mean"] - 50.0, shifted["mean"], places=6)

    def test_seed_reproducibility(self):
        phases = self.phases
        if not phases:
            self.skipTest("fixture item has no plannable phases")
        a = ihlib.simulate_contract(self.item, self.ladders, phases,
                                    trials=1000, seed=3)
        b = ihlib.simulate_contract(self.item, self.ladders, phases,
                                    trials=1000, seed=3)
        self.assertEqual(a["mean"], b["mean"])


class DuplicateAffixNameTest(unittest.TestCase):
    """Guards the affix-name collision (7 Aug 2026): affix DISPLAY NAMES are
    not unique on an item, and `score_tiers`/`simulate_contract` keyed their
    tier maps by name. On the Assault Shell of the Shadow — two distinct
    affixes both shown "of Mending" — one phase's Stability promoted BOTH to
    T1, pricing the contract at mean +98.5 against a plan ceiling of +52.3.
    A contract mean can never exceed the optimal-plan ceiling."""

    LADDER_KEY_A = ("suffix_regen_a", "regeneration", "flat_add")
    LADDER_KEY_B = ("suffix_regen_b", "regeneration", "flat_add")

    def _item(self):
        return {
            "name": "Twin Shell of Mending", "slot": "shell",
            "item_level": 3667, "stability": 27,
            "max_normal_affixes": 6, "max_prefixes": 3, "max_suffixes": 3,
            "prefixes": [],
            "suffixes": [
                {"name": "of Mending", "tier": 9, "affix_id": "suffix_regen_a",
                 "effects": [{"resource": "regeneration", "type": "flat_add",
                              "value": 8}]},
                {"name": "of Mending", "tier": 9, "affix_id": "suffix_regen_b",
                 "effects": [{"resource": "regeneration", "type": "flat_add",
                              "value": 5}]},
            ],
        }

    LADDERS = {LADDER_KEY_A: {9: 1.0, 1: 8.0}, LADDER_KEY_B: {9: 1.0, 1: 8.0}}

    def test_uids_are_distinct(self):
        uids = [uid for uid, _side, _a in ihlib.affix_entries(self._item())]
        self.assertEqual(len(uids), len(set(uids)))

    def test_label_disambiguates_only_on_collision(self):
        item = self._item()
        self.assertEqual(ihlib.affix_label(item, "suffix#0"),
                         "of Mending [suffix_regen_a]")
        item["suffixes"][1]["name"] = "of Warding"
        self.assertEqual(ihlib.affix_label(item, "suffix#0"), "of Mending")

    def test_ambiguous_phase_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            ihlib.resolve_affix_uid(self._item(), "of Mending")
        # ...but the uid and the affix_id both resolve cleanly
        self.assertEqual(
            ihlib.resolve_affix_uid(self._item(), "suffix#1"), "suffix#1")
        self.assertEqual(
            ihlib.resolve_affix_uid(self._item(), "suffix_regen_b"), "suffix#1")

    def test_one_phase_promotes_exactly_one_affix(self):
        item = self._item()
        both = ihlib.score_tiers(item, self.LADDERS,
                                 {"suffix#0": 1, "suffix#1": 1}, 10.0)
        one = ihlib.score_tiers(item, self.LADDERS, {"suffix#0": 1}, 10.0)
        neither = ihlib.score_tiers(item, self.LADDERS, {}, 10.0)
        self.assertGreater(both, one)
        self.assertGreater(one, neither)

    def test_contract_mean_never_exceeds_plan_ceiling(self):
        item = self._item()
        plan = ihlib.plan_craft(item, self.LADDERS, floor=2)
        phases = [(uid, to) for uid, _l, _f, to, _c, _e in plan["steps"]]
        if not phases:
            self.skipTest("no plannable phases")
        sim = ihlib.simulate_contract(item, self.LADDERS, phases, floor=2,
                                      trials=2000, seed=5)
        self.assertLessEqual(sim["mean"], plan["score"] + 1e-6)


class HomelabJobHoursTest(unittest.TestCase):
    """Guards the two-panel ETA disagreement (7 Aug 2026): `ih.py homelab`
    printed raw tick-hours ("~229min") while `ih.py audit` divided by the
    build-speed multiplier ("1.2h") for the same job. Ticks are WORK; real
    time is `ticks * tick_s * n / o` (client `homelabJobEstimates`)."""

    INFO = {"tick_seconds": 5, "global_build_speed_bonus": 0,
            "global_build_speed_multiplier": 3.125}

    def test_divides_by_build_speed(self):
        # 3600 ticks * 5s = 5h of work; at o=3.125 running alone that is 1.6h
        self.assertAlmostEqual(
            ihlib.homelab_job_hours(self.INFO, 3600), 1.6, places=6)

    def test_scales_with_concurrent_jobs(self):
        alone = ihlib.homelab_job_hours(self.INFO, 3600, 1)
        shared = ihlib.homelab_job_hours(self.INFO, 3600, 4)
        self.assertAlmostEqual(shared, alone * 4, places=6)

    def test_never_negative_and_floors_job_count(self):
        self.assertEqual(ihlib.homelab_job_hours(self.INFO, -100), 0.0)
        self.assertEqual(ihlib.homelab_job_hours(self.INFO, 3600, 0),
                         ihlib.homelab_job_hours(self.INFO, 3600, 1))


class AssumptionsRegistryTest(unittest.TestCase):
    """Every tunable constant must appear in `ihlib.assumptions()`.

    CLAUDE.md has required this since the register was built, as prose only.
    It was violated twice: `KEEP_DEPTH_PER_SLOT` shipped deciding irreversible
    decompiles without a row (7 Aug 2026, caught by code review), and this
    test's first run found `DAMAGE_K` and the fitted hit law — the mitigation
    and hit-rate formulas everything else is priced through — unregistered
    since they were fitted on 29 Jul.

    A TOTAL check: it walks the module's own namespace rather than searching
    for known-bad names, which is what lets it carry the rule. A bare
    module-level number IS a tunable by definition; structural constants
    (paths, slot maps, field-name tuples) are excluded by type, and private
    implementation limits by the underscore convention.
    """

    def _bare_numeric_constants(self):
        return {name: value for name, value in vars(ihlib).items()
                if name.isupper() and not name.startswith("_")
                and isinstance(value, (int, float))
                and not isinstance(value, bool)}

    def test_every_numeric_constant_is_registered(self):
        registered = {row[0] for row in ihlib.assumptions()}
        missing = sorted(
            name for name in self._bare_numeric_constants()
            if not any(name in row_name for row_name in registered))
        self.assertEqual(
            missing, [],
            "tunable constants missing from ihlib.assumptions(): "
            f"{missing}. CLAUDE.md requires registration in the same change "
            "that introduces the constant.")

    def test_registry_rows_have_the_documented_arity(self):
        """Exactly six fields, and `check` is callable-or-None.

        Both other tests in this class read fields by index (`row[2]`,
        `row[4]`), so a row with a stray extra element passes them while every
        *unpacking* consumer dies. Two did: INFERIOR_BAND and
        HARVEST_PER_GATHER_HOUR each carried a duplicated date, which shifted
        `check` into a seventh slot. `ih.py assumptions` -- the command
        CLAUDE.md requires before any weight-bearing verdict -- printed the
        register up to the first bad row and then aborted, and
        `_audit_homelab` was blind for as long as it lasted (7 Aug 2026,
        found by the audit's own broken-check flag).
        """
        for row in ihlib.assumptions():
            with self.subTest(constant=row[0]):
                self.assertEqual(
                    len(row), 6,
                    f"{row[0]} has {len(row)} fields, not the 6 that "
                    "assumptions() documents and every consumer unpacks")
                self.assertTrue(row[5] is None or callable(row[5]),
                                f"{row[0]} field 6 must be a live check or "
                                f"None, not {row[5]!r}")

    def test_registry_rows_carry_provenance(self):
        """Status and rationale always; a DATE only where one can exist.

        `asserted` and `inherited` rows legitimately have no validation date
        -- that absence is the whole point, and MaxHP's empty date is how the
        register says NEVER VALIDATED. But a `measured` row with no date is a
        gap: it claims a measurement and does not say when. This test found
        two on its first run (ArmorPen and Thorns, both measured 29 Jul 2026
        with the date recorded only in the prose)."""
        for row in ihlib.assumptions():
            name, status, rationale, validated = row[0], row[2], row[3], row[4]
            with self.subTest(constant=name):
                self.assertIn(status, {"measured", "asserted", "inherited",
                                       "supplied"})
                self.assertTrue(rationale and rationale.strip())
                if status in {"measured", "supplied"}:
                    self.assertTrue(
                        validated and validated.strip(),
                        f"{name} claims to be {status} but records no date")


class CliHelpTest(unittest.TestCase):
    """`ih.py --help` must document every subcommand.

    A TOTAL check (it walks the real subparser registry), which is what lets
    CLAUDE.md drop its hand-maintained command list and point at --help
    instead. That list had already drifted once — `locks` needed adding by
    hand — and a list in prose cannot be kept honest by anything.
    """

    def _subparsers(self):
        import ih
        parser = ih.build_parser()
        return next(a for a in parser._actions
                    if hasattr(a, "choices") and a.choices)

    def test_every_subcommand_has_help_text(self):
        sub = self._subparsers()
        documented = {a.dest for a in sub._choices_actions if a.help}
        missing = sorted(set(sub.choices) - documented)
        self.assertEqual(missing, [], f"subcommands with no help=: {missing}")

    def test_help_text_is_a_description_not_a_restated_name(self):
        sub = self._subparsers()
        for action in sub._choices_actions:
            with self.subTest(command=action.dest):
                self.assertGreater(len(action.help or ""), len(action.dest) + 8)


class DataIsolationTest(unittest.TestCase):
    """The suite must not be able to read the working tree's real data.

    Enforced structurally rather than by discipline: `tests/__init__.py` sets
    IH_DATA_DIR to an empty temp dir. Before that existed, a test calling
    `load_capture()` passed locally against 146 live captures and failed in
    CI, where `data/` is git-ignored (7 Aug 2026)."""

    def test_data_root_is_not_the_repo_data_dir(self):
        self.assertNotEqual(ihlib.DATA_ROOT.resolve(),
                            (ihlib.ROOT / "data").resolve())

    def test_no_captures_are_visible(self):
        with self.assertRaises(FileNotFoundError):
            ihlib.load_capture(None)


class AuditSmokeTest(unittest.TestCase):
    """Every registered audit check must RUN on a real capture.

    Added 7 Aug 2026: `_audit_inventory_capacity` shipped calling
    `hackcoin_equivalent(int)` when it takes a cost dict, and `ih.py audit`
    died with an AttributeError — the whole sweep, not just the new check.
    The unit suite was green because nothing executed the registry. A check
    that crashes is worse than a missing one: it takes the sweep with it."""

    def test_every_audit_check_runs(self):
        import ih
        for check in ih.AUDIT_CHECKS:
            with self.subTest(check=check.__name__):
                flags = check(FIXTURE, {})
                self.assertIsInstance(flags, list)
                for kind, message in flags:
                    self.assertIsInstance(kind, str)
                    self.assertIsInstance(message, str)

    def test_run_audit_returns_flags(self):
        import ih
        self.assertIsInstance(ih.run_audit(FIXTURE), list)


class CicdBudgetMessageTest(unittest.TestCase):
    """The free-runs line the advisory acts on. Every case here is a review
    finding from 7 Aug 2026: the check reported a budget from a model where
    the game reports its own, then over-advertised it three further ways."""

    def _run(self, rows, cicd_level):
        import ih
        with mock.patch.object(ihlib, "cicd_rows", return_value=rows):
            return ih._audit_cicd_budget_note(cicd_level)

    @staticmethod
    def _row(used, limit):
        now = datetime.now(timezone.utc)
        return {"seen_ms": now.timestamp() * 1000,
                "daily_used": used, "daily_limit": limit}

    def test_uses_game_reported_used_not_the_row_count(self):
        """Both halves of the fraction must come from one producer. Counting
        ledger rows under-counts any run made while the hub wasn't
        streaming, which overstates the free budget."""
        note = self._run([self._row(9, 15)], cicd_level=3)
        self.assertIn("6/15", note)

    def test_level_up_narrative_only_when_a_level_up_explains_the_gap(self):
        # observed 15 == 5 * L3 while the pipeline reads L4: supported.
        self.assertIn("L3->L4", self._run([self._row(8, 15)], cicd_level=4))
        # observed 13 matches no level: must NOT assert a level-up.
        other = self._run([self._row(8, 13)], cicd_level=4)
        self.assertNotIn("level-up raised", other)
        self.assertIn("no level-up explains", other)

    def test_counts_never_go_negative(self):
        """`observed - used` and `modelled - used` were printed unclamped, so
        a game cap above the model (or a missing newest limit) could print
        '-2 free runs'."""
        for used, limit, level in [(12, 15, 2), (16, 15, 4), (14, 15, 3)]:
            with self.subTest(used=used, limit=limit, level=level):
                note = self._run([self._row(used, limit)], cicd_level=level)
                for token in note.replace("/", " ").replace("(", " ").split():
                    self.assertFalse(
                        token.lstrip("-").isdigit() and token.startswith("-"),
                        f"negative count in: {note}")


class AffixScalingCheckTest(unittest.TestCase):
    """The live check must catch the defect it was written for.

    Its first version pooled flat and percent affixes into one median and
    gated on |median| < 5%. Percent observations outnumber flat ~5:1 and were
    already accurate, and the flat law's error was a TAIL — accurate
    mid-range, 19% low at the top — so reinstating the known-broken law made
    the check print OK at -0.0% median (7 Aug 2026 review finding). A check
    that cannot fail on the bug it guards is worse than none: it launders the
    bug as validated.
    """

    def _archive(self):
        """One flat affix observed across a wide ilvl span, truth = linear."""
        obs = {}
        for tier in (1, 5, 9):
            key = ("suffix_regeneration", "regeneration", "flat_add", tier)
            obs[key] = {ilvl: (ilvl + 250) / 1021 * (100.0 / tier)
                        for ilvl in (400, 900, 1600, 2400, 3200, 4200)}
        return obs

    def _capture_at(self, ilvl, tier=1):
        mid = (ilvl + 250) / 1021 * (100.0 / tier)
        return {"state": {"equipmentData": {}, "inventoryData": {"items": [{
            "name": "Probe", "slot": "acc1", "item_level": ilvl,
            "prefixes": [], "suffixes": [{
                "name": "of Mending", "tier": tier,
                "affix_id": "suffix_regeneration",
                "effects": [{"resource": "regeneration", "type": "flat_add",
                             "value": mid, "value_min": mid * 0.9,
                             "value_max": mid * 1.1}]}]}]}}}

    def _run(self, law):
        caps = [self._capture_at(i, t) for i in (900, 2400, 4200)
                for t in (1, 5, 9)]
        merged = {"state": {"equipmentData": {}, "inventoryData": {"items": [
            it for c in caps
            for it in c["state"]["inventoryData"]["items"]]}}}
        with mock.patch.object(ihlib, "_affix_range_observations",
                               return_value=self._archive()), \
             mock.patch.object(ihlib, "scale_flat_value", law):
            return ihlib._chk_affix_scaling(merged)

    def test_correct_law_passes(self):
        status, detail = self._run(lambda i: (i + 250) / 1021)
        self.assertEqual(status, "OK", detail)

    def test_the_old_broken_flat_law_is_flagged(self):
        status, detail = self._run(lambda i: ((i + 100) / 1021) ** 0.7849)
        self.assertEqual(status, "DRIFT", detail)
        self.assertIn("flat", detail)

    def test_flat_and_percent_are_reported_separately(self):
        _s, detail = self._run(lambda i: (i + 250) / 1021)
        self.assertIn("flat", detail)
        self.assertIn("pct", detail)


class LockActionsTest(unittest.TestCase):
    """Guards the 7 Aug decompile-lock rules. Decompiling is IRREVERSIBLE, so
    every one of these encodes a way the first versions got it wrong."""

    def _capture(self, items):
        return {"state": {"equipmentData": {}, "inventoryData": {"items": items,
                                                                "max_slots": 100},
                          "homelabInfo": {}}}

    def test_contested_item_is_never_discarded(self):
        # raw below band, ex-suspect above: the readings disagree, so the only
        # safe action is NONE. The first version decompiled it on raw alone.
        rows = [{"keep_worth": -39.1, "discard_worth": 21.0, "locked": True,
                 "protected": False, "slot": "Payload", "name": "x",
                 "raw": -39.1, "ex_suspect": 21.0,
                 "suspect_labels": ["Corrupt"]}]
        keep = [r for r in rows if r["keep_worth"] > ihlib.UPGRADE_BAND]
        contested = [r for r in rows
                     if r["keep_worth"] <= ihlib.UPGRADE_BAND < r["discard_worth"]]
        self.assertEqual(keep, [])
        self.assertEqual(len(contested), 1)

    def test_replanned_value_can_never_cancel_a_contested_hold(self):
        """Caught in review before shipping, 8 Aug 2026.

        `contested` used to be `keep_worth <= BAND < discard_worth`. When
        `keep_worth` began carrying the ex-suspect-OPTIMAL re-plan (a strictly
        larger number than the re-scored reading), that inflation pushed
        `keep_worth` over the band and cancelled the hold on five bases --
        `Aligned Analyzer of Thunder`, `Resilient Analyzer of Puncturing` and
        `Resilient Analyzer of Decay` among them -- which then fell to the
        depth cap and were printed as UNLOCK+decompile. Irreversible deletions
        decided by a flagged weight, under a header promising the opposite.

        `is_contested` takes the (raw, re-scored) pair and nothing else, so no
        re-planned number can reach the test however large it gets.
        """
        # the real 8 Aug numbers for Aligned Analyzer of Thunder
        raw, ex_rescored, ex_replanned = 69.1, -6.6, 19.8
        self.assertTrue(ihlib.is_contested(raw, ex_rescored))
        # the re-planned reading clears the band on its own and must not be
        # able to change that verdict -- the signature makes it unpassable
        self.assertGreater(ex_replanned, ihlib.UPGRADE_BAND)
        keep_worth = min(raw, max(ex_rescored, ex_replanned))
        self.assertGreater(keep_worth, ihlib.UPGRADE_BAND)
        self.assertTrue(ihlib.is_contested(raw, ex_rescored),
                        "a raised keep_worth must not cancel the hold")

    def test_agreeing_readings_are_not_contested(self):
        self.assertFalse(ihlib.is_contested(84.5, 43.4))   # both clear
        self.assertFalse(ihlib.is_contested(-158.2, -94.1))  # both fail

    def test_min_and_max_readings_differ_for_the_two_directions(self):
        raw, suspect = -39.1, -60.1        # suspect term is NEGATIVE
        keep_worth = min(raw, raw - suspect)
        discard_worth = max(raw, raw - suspect)
        self.assertLess(keep_worth, discard_worth)
        self.assertLessEqual(keep_worth, ihlib.UPGRADE_BAND)
        self.assertGreater(discard_worth, ihlib.UPGRADE_BAND)

    def test_lock_reason_ex_suspect_branch_is_not_inverted(self):
        text = ihlib._lock_reason(-39.1, 21.0, ["Corrupt"], 1, "Payload", 1)
        self.assertIn("what sinks it", text)
        self.assertNotIn("needs the suspect weight to look good", text)

    def test_lock_actions_outcomes_are_disjoint(self):
        """No item may appear in two outcome buckets, and nothing protected
        may ever be proposed for unlock.

        Built on a SYNTHETIC capture, not `load_capture`: the suite is
        zero-dependency and CI runs with an empty `data/` tree, so a test
        that reads a live capture passes locally and fails in CI (it did —
        hidden behind a lint failure on the same run, 7 Aug 2026).
        """
        def item(name, slot, locked):
            return {"name": name, "slot": slot, "decompile_locked": locked,
                    "item_level": 1000, "stability": 25,
                    "prefixes": [], "suffixes": [], "max_normal_affixes": 6,
                    "max_prefixes": 3, "max_suffixes": 3}
        cap = {"state": {
            "equipmentData": {},
            "inventoryData": {"max_slots": 100, "items": [
                item("Old Shell", "shell", True),
                item("Junk Driver", "gloves", True),
                item("Spare Router", "boots", False)]},
            "homelabInfo": {}}}
        with mock.patch.object(ihlib, "ACTIVE_EXPERIMENT",
                               {"name": "t-ab", "revert_item": "Old Shell"}):
            a = ihlib.lock_actions(cap)

        def names(key):
            return {r["name"] for r in (a.get(key) or [])}

        self.assertFalse(names("lock") & names("unlock"))
        self.assertFalse(names("unlock") & names("contested"))
        self.assertFalse(names("lock") & names("contested"))
        self.assertNotIn("Old Shell", names("unlock"))
        self.assertEqual(a["protected"], ["Old Shell"])

    @staticmethod
    def _scored_item(name, slot, locked, corrupt=0, regen=0):
        suffixes = []
        if corrupt:
            suffixes.append({"name": "of Infection", "tier": 9,
                             "affix_id": "suffix_corruption",
                             "effects": [{"resource": "corruption",
                                          "type": "flat_add",
                                          "value": corrupt}]})
        if regen:
            suffixes.append({"name": "of Mending", "tier": 9,
                             "affix_id": "suffix_regeneration",
                             "effects": [{"resource": "regeneration",
                                          "type": "flat_add", "value": regen}]})
        return {"name": name, "slot": slot, "decompile_locked": locked,
                "item_level": 1000, "stability": 25, "prefixes": [],
                "suffixes": suffixes, "max_normal_affixes": 6,
                "max_prefixes": 3, "max_suffixes": 3}

    def _run(self, items):
        cap = {"state": {"equipmentData": {},
                         "inventoryData": {"max_slots": 100, "items": items},
                         "homelabInfo": {}}}
        with mock.patch.object(ihlib, "ACTIVE_EXPERIMENT", None):
            return ihlib.lock_actions(cap)

    def test_unlocked_contested_item_is_locked_not_ignored(self):
        """The contested guarantee was STATUS-QUO BIASED and so did not hold.

        "An item the two readings disagree about gets NO action, it stays as
        it is" protects a LOCKED item. For a fresh drop the status quo is
        UNLOCKED, and under the operating model unlocked means deleted — so
        an unlocked contested item was destroyed by precisely the flagged
        weight the rule promises will never decide a decompile. Real loss:
        `Aligned Analyzer of Breaching`, keep +7.2 vs discard +103.1,
        decompiled 7 Aug 2026 with no line of output.
        """
        a = self._run([self._scored_item("Corrupt Base", "acc1", False,
                                         corrupt=200)])
        locked_names = {r["name"] for r in a["lock"]}
        self.assertIn("Corrupt Base", locked_names,
                      "an unlocked contested base must be proposed for LOCK, "
                      "not silently left to the next decompile sweep")
        self.assertNotIn("Corrupt Base", {r["name"] for r in a["unlock"]})

    def test_no_item_appears_under_two_opposite_headings(self):
        """One item told to LOCK and simultaneously listed as about to be
        deleted by the cap. The 7 Aug review caught this shape once already in
        this function; it came back on 8 Aug through the CONTESTED path,
        because `at_risk` filtered on rank and lock flag but not on contested.
        Live symptom: `Intangible Analyzer of Evasion` and `Leviathan's
        Firewall of Vitality` printed under both headings in one advisory."""
        # several unlocked contested bases in ONE slot, so ranks run past the
        # depth cap and the at-risk branch is reachable
        items = [self._scored_item(f"Corrupt Base {i}", "acc1", False,
                                   corrupt=200 - 10 * i) for i in range(5)]
        a = self._run(items)
        buckets = {k: {r["name"] for r in (a.get(k) or [])}
                   for k in ("lock", "unlock", "contested", "at_risk")}
        self.assertEqual(buckets["lock"] & buckets["at_risk"], set())
        self.assertEqual(buckets["lock"] & buckets["unlock"], set())
        self.assertEqual(buckets["unlock"] & buckets["at_risk"], set())

    def test_band_clearing_base_outside_the_cap_is_surfaced_not_silent(self):
        """Delta-only output must never hide an impending irreversible loss.

        A band-clearing base that is already unlocked and ranks outside the
        depth cap generates no lock/unlock delta, so the list said nothing
        while it was deleted. That silence cost `Untouchable Analyzer of
        Aiming` (keep +42.5, raw +121.2 — the highest raw base owned).
        """
        items = [self._scored_item(f"Regen {i}", "acc1", False, regen=r)
                 for i, r in enumerate((400, 300, 200, 100), start=1)]
        a = self._run(items)
        at_risk = {r["name"] for r in a["at_risk"]}
        self.assertTrue(at_risk, "band-clearing unlocked surplus must appear "
                                 "in at_risk so the cap's cost is visible")
        for row in a["at_risk"]:
            self.assertGreater(row["slot_rank"], a["per_slot"])
            self.assertFalse(row["locked"])

    def test_keep_depth_holds_more_than_the_single_best_base(self):
        """Depth 1 discarded rank-2 bases whose true replacement time was
        ~7 days while its justification claimed ~1 (the 0.92/day figure
        counts ALL band-clearing bases as interchangeable; top-decile ones
        arrive every 6.8 days in the measured slot)."""
        self.assertGreaterEqual(ihlib.KEEP_DEPTH_PER_SLOT, 2)
        items = [self._scored_item(f"Regen {i}", "acc1", False, regen=r)
                 for i, r in enumerate((400, 300), start=1)]
        a = self._run(items)
        self.assertEqual({r["name"] for r in a["lock"]},
                         {"Regen 1", "Regen 2"})


class HomelabEtaScheduleTest(unittest.TestCase):
    """The throughput split DECLINES as jobs finish; a fixed divisor
    over-states every ETA except the longest job's (7 Aug review finding)."""

    INFO = {"tick_seconds": 5, "global_build_speed_bonus": 0,
            "global_build_speed_multiplier": 1.0}

    def test_single_job_matches_the_simple_helper(self):
        jobs = [{"duration_ticks": 720, "progress_ticks": 0}]
        eta = ihlib.homelab_job_eta_hours(self.INFO, jobs)
        self.assertAlmostEqual(eta[0],
                               ihlib.homelab_job_hours(self.INFO, 720, 1),
                               places=6)

    def test_shorter_job_finishes_first_and_speeds_up_the_rest(self):
        jobs = [{"duration_ticks": 720, "progress_ticks": 0},
                {"duration_ticks": 360, "progress_ticks": 0}]
        eta = ihlib.homelab_job_eta_hours(self.INFO, jobs)
        self.assertLess(eta[1], eta[0])
        # job 1: 360 ticks at rate/2 -> 3600s. job 0 then has 360 left at full
        # rate -> another 1800s. Total 5400s = 1.5h, NOT the 2h a fixed
        # divisor would predict.
        self.assertAlmostEqual(eta[1], 1.0, places=6)
        self.assertAlmostEqual(eta[0], 1.5, places=6)

    def test_empty_job_list(self):
        self.assertEqual(ihlib.homelab_job_eta_hours(self.INFO, []), {})


class RevertPathProtectionTest(unittest.TestCase):
    """Guards the hot-gate revert path (7 Aug 2026): the first run of
    `lock_actions` recommended decompiling Shielded Shell of Bastion while
    shell-ab-2026-08-07 was live, because the experiment declared no
    `revert_item` and the lookup returned an empty set instead of failing."""

    def test_hot_experiment_without_revert_item_raises(self):
        with mock.patch.object(ihlib, "ACTIVE_EXPERIMENT",
                               {"name": "x-ab", "slot": "Shell"}):
            with self.assertRaises(ValueError):
                ihlib.protected_revert_items()

    def test_concluded_experiment_protects_nothing(self):
        with mock.patch.object(ihlib, "ACTIVE_EXPERIMENT",
                               {"name": "x-ab", "concluded": "KEEP"}):
            self.assertEqual(ihlib.protected_revert_items(), set())

    def test_hot_experiment_protects_its_revert_item(self):
        with mock.patch.object(ihlib, "ACTIVE_EXPERIMENT",
                               {"name": "x-ab", "revert_item": "Old Shell"}):
            self.assertEqual(ihlib.protected_revert_items(), {"Old Shell"})

    def test_live_declaration_names_a_revert_item(self):
        # the real ACTIVE_EXPERIMENT must stay safe to run lock advice against
        ihlib.protected_revert_items()


class ReservedProbeArmTest(unittest.TestCase):
    """Guards gear held as an INSTRUMENT rather than as a craft base.

    A probe arm is chosen for what it ISOLATES, so `plan_craft` scores it as
    junk by construction and value-based lock advice sorts it into the
    discard pile. Before 9 Aug 2026 the reservation was a sentence in
    docs/candidate-status.md naming five items; nothing in the code read it,
    the inventory turned over, and all five were gone — the MaxHP pair among
    them, with MaxHP still the largest ASSERTED term in the model.
    """

    SLOT = "acc1"          # SLOT_DISPLAY maps the equipment keys, not slugs

    @classmethod
    def _item(cls, name, locked=False, armor_pen=0.0, defense=0.0,
              slot=None):
        effects = []
        if armor_pen:
            effects.append({"resource": "armor_penetration",
                            "type": "flat_add", "value": armor_pen})
        if defense:
            effects.append({"resource": "defense",
                            "type": "percent_add", "value": defense})
        return {"name": name, "slot": slot or cls.SLOT,
                "decompile_locked": locked, "item_level": 1000,
                "stability": 25, "max_normal_affixes": 6, "max_prefixes": 3,
                "max_suffixes": 3, "prefixes": [],
                "suffixes": [{"name": "of Puncturing", "tier": 9,
                              "affix_id": "suffix_armor_pen",
                              "effects": effects}]}

    def _capture(self, inventory, equipped_armor_pen=900.0):
        return {"state": {
            "equipmentData": {
                self.SLOT: self._item("Equipped", True,
                                      armor_pen=equipped_armor_pen)},
            "inventoryData": {"max_slots": 100, "items": inventory},
            "homelabInfo": {}}}

    PROBE = [{"family": "ArmorPen", "arms": 1, "reason": "r",
              "unblock": "u", "concluded": None}]

    def test_pure_lever_outranks_a_bigger_but_dirtier_one(self):
        # `Dirty` moves ArmorPen further, but drags Defense with it. par.22
        # ranks on the RATIO, because the other families have to be
        # subtracted at their own betas and that subtraction is the error.
        cap = self._capture([
            self._item("Clean", True, armor_pen=300.0),
            self._item("Dirty", True, armor_pen=0.0, defense=0.60)])
        levers = ihlib.probe_levers(cap, "ArmorPen", top=2)
        self.assertEqual(levers[0]["name"], "Clean")
        self.assertGreater(levers[0]["purity"], levers[1]["purity"])

    def test_lever_below_the_purity_floor_is_not_an_arm(self):
        """The floor is the whole point: a dirty lever is worse than none.

        Without it the first version reserved a MaxHP 'arm' moving +18.2
        against -112.5 of signed other movement — inventory spent at 102/102
        to protect something that could not have measured anything.
        """
        # ArmorPen moves -40.8 score (600 * 0.068); Defense moves -67.5
        # (1.5 * 100 * 0.45). Purity 0.60 — the correction outweighs the
        # signal, so this must not be admitted at any arm count.
        cap = self._capture([
            self._item("Filthy", True, armor_pen=300.0, defense=-1.5)])
        self.assertEqual(ihlib.probe_levers(cap, "ArmorPen"), [])

    def test_reserved_arm_is_never_offered_for_decompile(self):
        cap = self._capture([self._item("Instrument", True, armor_pen=300.0)])
        with mock.patch.object(ihlib, "RESERVED_PROBES", self.PROBE), \
             mock.patch.object(ihlib, "ACTIVE_EXPERIMENT", None):
            actions = ihlib.lock_actions(cap)
        self.assertNotIn("Instrument",
                         {r["name"] for r in actions["unlock"]})
        self.assertIn("Instrument", actions["probe_holds"])

    def test_unlocked_reserved_arm_surfaces_as_a_lock_action(self):
        """An unlocked instrument is one sweep from deletion, which is
        exactly the state the five lost arms passed through unremarked."""
        cap = self._capture([self._item("Instrument", False, armor_pen=300.0)])
        with mock.patch.object(ihlib, "RESERVED_PROBES", self.PROBE), \
             mock.patch.object(ihlib, "ACTIVE_EXPERIMENT", None):
            actions = ihlib.lock_actions(cap)
        row = next(r for r in actions["lock"] if r["name"] == "Instrument")
        self.assertIn("RESERVED ArmorPen probe arm", row["reason"])
        # and it must NOT also appear under the opposite heading
        self.assertNotIn("Instrument",
                         {r["name"] for r in actions["at_risk"]})

    def test_concluded_reservation_holds_nothing(self):
        cap = self._capture([self._item("Instrument", True, armor_pen=300.0)])
        done = [dict(self.PROBE[0], concluded="fitted 9 Aug")]
        with mock.patch.object(ihlib, "RESERVED_PROBES", done):
            self.assertEqual(ihlib.reserved_probe_holds(cap), {})

    def test_audit_reports_a_reservation_with_no_owned_lever(self):
        """The finding that went unreported for the five lost arms.

        A reservation whose instrument no longer exists must READ as a loss,
        not as silence — and must not be papered over by protecting whatever
        junk ranks highest.
        """
        import ih
        cap = self._capture([self._item("Filthy", True, armor_pen=300.0,
                                        defense=-1.5)])
        with mock.patch.object(ihlib, "RESERVED_PROBES", self.PROBE):
            kinds = [k for k, _ in ih._audit_reserved_probes(cap, {})]
        self.assertEqual(kinds, ["PROBE-GONE"])

    def test_audit_reports_an_unlocked_lever(self):
        import ih
        cap = self._capture([self._item("Instrument", False, armor_pen=300.0)])
        with mock.patch.object(ihlib, "RESERVED_PROBES", self.PROBE):
            flags = ih._audit_reserved_probes(cap, {})
        self.assertEqual([k for k, _ in flags], ["PROBE-LOOSE"])
        self.assertIn("Instrument", flags[0][1])

    def test_audit_is_silent_when_the_arm_is_owned_and_locked(self):
        import ih
        cap = self._capture([self._item("Instrument", True, armor_pen=300.0)])
        with mock.patch.object(ihlib, "RESERVED_PROBES", self.PROBE):
            self.assertEqual(ih._audit_reserved_probes(cap, {}), [])

    def test_zero_arms_holds_nothing_rather_than_everything(self):
        """`rows[:top] if top else rows` made arms=0 return the whole
        inventory, so a mis-declared reservation would protect every item
        from decompile — an inventory deadlock dressed as a safety feature."""
        cap = self._capture([self._item("Instrument", True, armor_pen=300.0)])
        self.assertEqual(ihlib.probe_levers(cap, "ArmorPen", top=0), [])
        none_probe = [dict(self.PROBE[0], arms=0)]
        with mock.patch.object(ihlib, "RESERVED_PROBES", none_probe):
            self.assertEqual(ihlib.reserved_probe_holds(cap), {})

    def test_live_reservations_name_a_family_never_an_item(self):
        """The root cause was a NAME list: it rots when the inventory turns
        over, and rotted silently because nothing recomputed it."""
        for probe in ihlib.RESERVED_PROBES:
            self.assertIn("family", probe)
            self.assertNotIn("item", probe)
            self.assertNotIn("items", probe)
            self.assertTrue(probe.get("unblock"))


class PlanCraftTest(unittest.TestCase):
    def test_budget_and_cap_respected(self):
        item = FIXTURE["state"]["inventoryData"]["items"][0]
        ladders = ihlib.tier_ladders(FIXTURE)
        plan = ihlib.plan_craft(item, ladders)
        stability = item.get("stability") or 0
        # greedy planning may overshoot the budget by less than one step's
        # expectation, never by more (plan_craft stops when the NEXT step
        # does not fit) — so total spend stays under the full Stability pool
        self.assertLessEqual(plan["expected_spend"], stability)
        for _uid, _label, _from, target, _attempts, _measured in plan["steps"]:
            self.assertGreaterEqual(target, 1)
        capped = ihlib.plan_craft(item, ladders, tier_cap=3)
        for _uid, _label, _from, target, _attempts, _measured in capped["steps"]:
            self.assertGreaterEqual(target, 3)


class LadderValueTest(unittest.TestCase):
    """Region-aware ladder walking: interpolation is bounded by data, but
    extrapolation past the observed range once over-projected a T6→T1 chase
    by 1.9× (the one-constant-1.4 era)."""

    LADDER = {8: 10.0, 6: 20.0, 2: 100.0}

    def test_measured_point(self):
        value, measured = ihlib.ladder_value(self.LADDER, 6)
        self.assertEqual(value, 20.0)
        self.assertTrue(measured)

    def test_interpolated_point(self):
        value, measured = ihlib.ladder_value(self.LADDER, 4)
        self.assertFalse(measured)
        self.assertGreater(value, 20.0)
        self.assertLess(value, 100.0)

    def test_extrapolated_point(self):
        value, measured = ihlib.ladder_value(self.LADDER, 1)
        self.assertFalse(measured)
        self.assertGreater(value, 100.0)


class CompactLogTest(unittest.TestCase):
    """Round-trip of the game's compact combat-log encoding, including the
    `bm` barrier bitmask, feeding the unbiased hit-rate estimator (the
    biased `pm` denominator produced the false 'Accuracy is saturated'
    reading of 27 Jul 2026)."""

    COMPACT = {
        "n": 4,
        "ph": [2, 1, 2, 0],
        "pm": [0, 1, 0, 1],
        "pa": [100, 40, 90, 0],
        "bm": [1, 0, 3, 0],
        "pbs": [500, 0, 300, 0],
        "pbf": [400, 0, 0, 0],
        "ebs": [0, 0, 90, 0],
        "ebf": [0, 0, 10, 0],
    }

    def test_inflate_and_hit_rate(self):
        rounds = ihlib.inflate_compact_combat_log(self.COMPACT)
        self.assertEqual(len(rounds), 4)
        self.assertEqual(rounds[0]["pbs"], 500)     # bm bit 1 -> player pool
        self.assertNotIn("pbs", rounds[1])          # no bit -> no pool keys
        self.assertEqual(rounds[2]["ebf"], 10)      # bm bit 2 -> enemy pool
        hits, trials = ihlib.unbiased_hit_rate(rounds)
        # provably-2-attack rounds only: (2 hits, no flag) x2 and (1 hit, flag)
        self.assertEqual((hits, trials), (2, 3))


class PredictionLedgerTest(unittest.TestCase):
    """Guards the orphan-row bug (6 Aug 2026): a realized-only record call
    appended an all-None row and left the contract-time row ungraded."""

    def test_realized_updates_in_place(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "predictions.jsonl"
            ledger.write_text("")
            ihlib.record_prediction("Test Item", "Router", 10.0, p10=5.0,
                                    p90=15.0, path=ledger)
            row = ihlib.record_prediction("Test Item", "Router", None,
                                          realized=12.5, path=ledger)
            self.assertEqual(row["realized"], 12.5)
            self.assertEqual(row["projected"], 10.0)
            rows = [json.loads(line) for line in
                    ledger.read_text().splitlines()]
            self.assertEqual(len(rows), 1)          # updated, not appended

    def test_realized_without_contract_row_raises(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "predictions.jsonl"
            ledger.write_text("")
            with self.assertRaises(ValueError):
                ihlib.record_prediction("Ghost Item", "Router", None,
                                        realized=1.0, path=ledger)


class ExperimentStatusTest(unittest.TestCase):
    """Pre/post classification around the equip boundary — the subtlest code
    in the repo (the driver A/B's first provisional boundary silently leaked
    a pre-craft death into the post window)."""

    EXPERIMENT = {
        "name": "test-ab", "item": "Test Item", "slot": "Router",
        "equip_ms": 1_000_000, "boundary_fight_id": None,
        "baseline_deaths": [100], "baseline_hits": (10, 3),
        "target_deaths": 4, "baseline_recent_ms": 0, "segment_ms": None,
        "keep_rule": "test",
    }

    def _run(self, records):
        with tempfile.TemporaryDirectory() as streams, \
                tempfile.TemporaryDirectory() as caps:
            ledger = Path(streams) / "day.jsonl"
            ledger.write_text("\n".join(json.dumps(r) for r in records) + "\n")
            with mock.patch.object(ihlib, "STREAM_DIR", Path(streams)), \
                    mock.patch.object(ihlib, "CAPTURES_DIR", Path(caps)):
                ihlib._STREAM_CACHE["key"] = None
                return ihlib.experiment_status(self.EXPERIMENT)

    @staticmethod
    def _death(ms, streak):
        return {"kind": "death", "seen_ms": ms, "key": [ms],
                "death": {"ended_at_ms": ms, "streak_ended": streak}}

    def test_boundary_split(self):
        status = self._run([self._death(500_000, 90),
                            self._death(2_000_000, 110)])
        self.assertEqual(status["pre_death_streaks"], [90])
        self.assertEqual(status["post_death_streaks"], [110])

    def test_undeclared_segment_counts_no_deaths_after_it(self):
        """`segment_ms: None` means no boundary, so nothing is past one.

        This fell back to ALL post deaths, making "no boundary declared"
        print identically to "every death is past the boundary" — and the
        printer captioned it with a hardcoded July VLAN label. On 7 Aug 2026
        shell-ab-2026-08-07 (segment_ms None) reported all 29 post deaths as
        post-segment and told the reader to analyse them separately. A false
        contamination warning argues for discounting a clean result, which
        is as costly as missing a real one.
        """
        status = self._run([self._death(500_000, 90),
                            self._death(2_000_000, 110),
                            self._death(3_000_000, 115)])
        self.assertEqual(status["post_death_streaks"], [110, 115])
        self.assertEqual(status["deaths_after_segment"], 0)

    def test_declared_segment_counts_only_deaths_after_it(self):
        segmented = dict(self.EXPERIMENT, segment_ms=2_500_000)
        with tempfile.TemporaryDirectory() as streams, \
                tempfile.TemporaryDirectory() as caps:
            ledger = Path(streams) / "day.jsonl"
            ledger.write_text("\n".join(
                json.dumps(r) for r in [self._death(2_000_000, 110),
                                        self._death(3_000_000, 115)]) + "\n")
            with mock.patch.object(ihlib, "STREAM_DIR", Path(streams)), \
                    mock.patch.object(ihlib, "CAPTURES_DIR", Path(caps)):
                ihlib._STREAM_CACHE["key"] = None
                status = ihlib.experiment_status(segmented)
        self.assertEqual(status["deaths_after_segment"], 1)

    def test_every_declared_segment_carries_a_label(self):
        """A boundary the readout can name. The label was hardcoded to one
        July experiment's VLAN build, so every later segmented window would
        have been captioned with someone else's confound."""
        import experiments
        for name, exp in vars(experiments).items():
            if not (name.isupper() and isinstance(exp, dict)
                    and "segment_ms" in exp):
                continue
            if exp.get("segment_ms"):
                with self.subTest(experiment=name):
                    self.assertTrue(
                        (exp.get("segment_label") or "").strip(),
                        f"{name} declares segment_ms but no segment_label, "
                        "so its readout cannot name the confound")

    def test_sentinel_keeps_post_empty(self):
        sentinel = dict(self.EXPERIMENT, equip_ms=4_102_444_800_000)
        with tempfile.TemporaryDirectory() as streams, \
                tempfile.TemporaryDirectory() as caps:
            ledger = Path(streams) / "day.jsonl"
            ledger.write_text(json.dumps(self._death(2_000_000, 110)) + "\n")
            with mock.patch.object(ihlib, "STREAM_DIR", Path(streams)), \
                    mock.patch.object(ihlib, "CAPTURES_DIR", Path(caps)):
                ihlib._STREAM_CACHE["key"] = None
                status = ihlib.experiment_status(sentinel)
        self.assertEqual(status["post_death_streaks"], [])


class FreshWorkspaceTest(unittest.TestCase):
    """A fresh clone with an empty data/ must degrade gracefully, and a
    capture missing a lazy panel must not crash the audit (the July-22
    captures crashed `credit_runway` until 6 Aug 2026)."""

    def test_missing_homelab_panel_does_not_crash(self):
        capture = {"state": {"statsBreakdown":
                             FIXTURE["state"]["statsBreakdown"],
                             "currentPlayer": {"credits": 0, "hackcoin": 0}}}
        balance, hours, pending = ihlib.credit_runway(capture)
        self.assertEqual(pending, [])

    def test_empty_captures_raises_filenotfound(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(ihlib, "CAPTURES_DIR", Path(d)):
                with self.assertRaises(FileNotFoundError):
                    ihlib.load_capture()

    def test_empty_ledger_accessors_degrade(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(ihlib.fight_cadence(dir_=d), [])
            self.assertIsNone(ihlib.measured_credits_per_hour(dir_=d))
            self.assertIsNone(ihlib.latest_stream_ms(dir_=d))


if __name__ == "__main__":
    unittest.main()
