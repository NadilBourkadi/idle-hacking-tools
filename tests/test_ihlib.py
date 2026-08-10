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

    def test_surplus_is_never_lost_silently_at_any_depth(self):
        """The 7 Aug incident was depth-1 *plus silence*, not depth 1.

        Four bases were lost because a cap-surplus base generates no
        lock/unlock delta, so the list said nothing while they were deleted.
        The fix that mattered was the AT RISK block; the depth bump to 2 was
        the other half and it priced only ONE side — how long a base of equal
        quality takes to replace (~6.8 days top-decile).

        The player overrode it to 1 on 9 Aug 2026 on the side the derivation
        never had: holding costs manual lock management, and it costs slots at
        102/102 which suppresses the fresh drops that obsolete the held bases
        in the first place, against a craft rate of about one a day.

        So this test no longer pins the NUMBER — pinning today's answer is
        what made the Barrier membership test go red on success. It pins the
        invariant that survives any depth: whatever the cap is, everything it
        releases is visible.
        """
        items = [self._scored_item(f"Regen {i}", "acc1", False, regen=r)
                 for i, r in enumerate((400, 300, 200), start=1)]
        a = self._run(items)
        held = {r["name"] for r in a["lock"]}
        self.assertEqual(len(held), ihlib.KEEP_DEPTH_PER_SLOT)
        surplus = {r["name"] for r in a["at_risk"]}
        self.assertEqual(
            held | surplus, {"Regen 1", "Regen 2", "Regen 3"},
            "every band-clearing base must be either held or shown AT RISK — "
            "a base in neither list is deleted with no line of output")

    def test_contested_hold_respects_the_depth_cap(self):
        """A contested base outside the cap protects nothing and costs a slot.

        Until 9 Aug 2026 contested items ignored slot rank entirely, so the
        hold was unbounded — it lasted until the flagged weight resolved, and
        for MaxHP no instrument to resolve it is even owned. The disagreement
        only matters if WINNING it would make the item a keeper, so the cap is
        applied at the item's best case (`discard_worth`), never the disputed
        one.
        """
        # Corrupt-carried bases: raw and ex-suspect straddle the band, so all
        # three are contested. Only the best may be held.
        items = [self._scored_item(f"Corrupt {i}", "acc1", True, corrupt=c)
                 for i, c in enumerate((900, 600, 300), start=1)]
        a = self._run(items)
        self.assertLessEqual(len(a["contested"]), ihlib.KEEP_DEPTH_PER_SLOT)
        for row in a["contested"]:
            self.assertLessEqual(row["optimistic_rank"],
                                 ihlib.KEEP_DEPTH_PER_SLOT)


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


class DeepenSearchTest(unittest.TestCase):
    """`deepen_search` could only ever push ONE phase (9 Aug 2026).

    It rebuilt every candidate from `plan_craft`'s plan and changed a single
    index, so a plan with two phases pushed was unreachable -- and the player
    beat it that way twice before the shape was noticed.
    """

    def _fixture(self):
        item = FIXTURE["state"]["inventoryData"]["items"][0]
        return item, ihlib.tier_ladders(FIXTURE)

    def test_multi_phase_deepenings_are_reachable(self):
        item, ladders = self._fixture()
        plan = ihlib.plan_craft(item, ladders)
        phases = [(label, target)
                  for _uid, label, _from, target, _att, _m in plan["steps"]]
        if len(phases) < 2:
            self.skipTest("fixture base plans fewer than two phases")
        out = ihlib.deepen_search(item, ladders, phases, trials=200)
        deepened = [sum(1 for (n, t), (bn, bt) in zip(cand, phases, strict=True) if t < bt)
                    for cand, _sim in out]
        self.assertTrue(
            any(d >= 2 for d in deepened),
            "no candidate pushes two phases at once — the search is still "
            "single-index and the plans that beat it stay unreachable")

    def test_the_unmodified_plan_is_always_offered(self):
        """Deepening must never REMOVE the shallow option: over-committing is
        bounded-downside, not free, and the caller compares against it."""
        item, ladders = self._fixture()
        plan = ihlib.plan_craft(item, ladders)
        phases = [(label, target)
                  for _uid, label, _from, target, _att, _m in plan["steps"]]
        out = ihlib.deepen_search(item, ladders, phases, trials=200)
        self.assertIn(tuple(phases), {tuple(c) for c, _ in out})


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


class EquipBoundaryStraddleTest(unittest.TestCase):
    """A death is classified post-equip on when it ENDED, but it ends a
    streak that may have been fought entirely on the old item.

    Found 9 Aug 2026 mid-flight: router-ab-2026-08-09's first post-equip
    death (streak 240, ended 10:20Z) began ~10:00Z against a 10:06Z equip.
    True of every experiment here -- `boundary_fight_id` split FIGHTS and
    nothing split DEATHS.
    """

    EQUIP = 1_000_000_000_000

    def _status(self, deaths):
        exp = {"name": "t-ab", "item": "X", "slot": "Shell",
               "equip_ms": self.EQUIP, "baseline_deaths": [100],
               "target_deaths": 4, "keep_rule": "k", "segment_ms": None,
               "baseline_hits": (10, 1), "baseline_recent_ms": 0}
        records = [{"kind": "death", "death": d} for d in deaths]
        with mock.patch.object(ihlib, "stream_records", return_value=records), \
             mock.patch.object(ihlib, "capture_paths", return_value=[]):
            return ihlib.experiment_status(exp)

    def test_streak_begun_before_the_equip_is_flagged(self):
        cadence_ms = ihlib.FIGHT_CADENCE_S * 1000
        st = self._status([
            # ends 1 min after equip having fought 200 fights -> began well before
            {"ended_at_ms": self.EQUIP + 60_000, "streak_ended": 200},
            # begins comfortably after the equip
            {"ended_at_ms": self.EQUIP + int(500 * cadence_ms),
             "streak_ended": 100},
        ])
        self.assertEqual(st["straddler_streaks"], [200])
        self.assertEqual(st["post_death_streaks_clean"], [100])

    def test_the_declared_metric_is_untouched(self):
        """The disclosure must never silently become the measurement."""
        st = self._status([
            {"ended_at_ms": self.EQUIP + 60_000, "streak_ended": 200},
            {"ended_at_ms": self.EQUIP + 9_000_000, "streak_ended": 100},
        ])
        self.assertEqual(st["post_death_streaks"], [200, 100])

    def test_no_straddlers_when_every_streak_starts_after_equip(self):
        cadence_ms = ihlib.FIGHT_CADENCE_S * 1000
        st = self._status([
            {"ended_at_ms": self.EQUIP + int(400 * cadence_ms),
             "streak_ended": 50},
        ])
        self.assertEqual(st["straddler_streaks"], [])


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

    def test_every_reservation_declares_a_family_and_an_unblock(self):
        """Was `..._name_a_family_never_an_item` until 10 Aug 2026, when it
        went red on a reservation that has to name its arms.

        It pinned "no `items` key", but the root cause of the five lost arms
        was not naming — it was SILENCE. The reservation lived as prose in a
        doc, nothing recomputed it, and when the inventory turned over it kept
        naming ghosts with no flag. A name list resolved against the capture
        every call, which reports a missing arm as PROBE-GONE, does not have
        that failure mode.

        And one reservation genuinely cannot be expressed any other way: a
        REPLICATION re-tests a beta fitted on specific arms, so re-ranking
        substitutes a different experiment. The invariant is therefore
        "resolved against the capture, and loud when an arm is gone" — pinned
        by the two tests below — not "never name anything".

        `item` singular stays forbidden: that was the doc-prose shape, and
        nothing reads it.
        """
        for probe in ihlib.RESERVED_PROBES:
            self.assertIn("family", probe)
            self.assertNotIn("item", probe)
            self.assertTrue(probe.get("unblock"))
            if probe.get("items"):
                self.assertIsInstance(probe["items"], list)

    def test_named_arms_are_held_instead_of_the_purity_ranked_ones(self):
        """A replication must not be silently re-armed. `Better` outranks
        `Named` on purity, so a family reservation would hold it — and the
        block that already ran did not use it."""
        cap = self._capture([self._item("Named", True, armor_pen=300.0,
                                        defense=-0.2),
                             self._item("Better", True, armor_pen=300.0)])
        named = [dict(self.PROBE[0], items=["Named"], arms=2)]
        self.assertEqual(
            ihlib.probe_levers(cap, "ArmorPen", top=1)[0]["name"], "Better")
        with mock.patch.object(ihlib, "RESERVED_PROBES", named):
            self.assertEqual(list(ihlib.reserved_probe_holds(cap)), ["Named"])

    def test_a_missing_named_arm_reads_as_a_loss_not_as_silence(self):
        """The half of the original incident that actually cost the arms."""
        import ih
        cap = self._capture([self._item("Better", True, armor_pen=300.0)])
        named = [dict(self.PROBE[0], items=["Named"], arms=2)]
        with mock.patch.object(ihlib, "RESERVED_PROBES", named):
            flags = ih._audit_reserved_probes(cap, {})
        self.assertEqual([k for k, _ in flags], ["PROBE-GONE"])
        self.assertIn("Named", flags[0][1])
        self.assertIn("replicated", flags[0][1])

    def test_an_unlocked_named_arm_surfaces_as_a_lock_action(self):
        import ih
        cap = self._capture([self._item("Named", False, armor_pen=300.0)])
        named = [dict(self.PROBE[0], items=["Named"], arms=2)]
        with mock.patch.object(ihlib, "RESERVED_PROBES", named), \
             mock.patch.object(ihlib, "ACTIVE_EXPERIMENT", None):
            flags = ih._audit_reserved_probes(cap, {})
            actions = ihlib.lock_actions(cap)
        self.assertEqual([k for k, _ in flags], ["PROBE-LOOSE"])
        row = next(r for r in actions["lock"] if r["name"] == "Named")
        self.assertIn("named arm", row["reason"])
        self.assertNotIn("Named", {r["name"] for r in actions["unlock"]})


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


def _hardware_fixture(levels=None):
    """A synthetic hardware panel: one flagged-family track, three clean ones.

    Built here rather than taken from a capture because the suite is
    data-isolated by construction (`DataIsolationTest`). Track types are the
    real ones so `stat_label` resolves them into CRAFT_WEIGHTS families.
    """
    levels = levels or {"ecc": 200, "corruption": 80, "defense": 100,
                        "armor_pen": 60}
    stats = {"regeneration": {"equipment_flat": 1000, "equipment_pct": 0,
                              "hardware": 1.0, "homelab": 0},
             "corruption": {"equipment_flat": 140, "equipment_pct": 0,
                            "hardware": 0.4, "homelab": 0},
             "armor_penetration": {"equipment_flat": 1500, "equipment_pct": 0,
                                   "hardware": 0.3, "homelab": 0},
             "defense": {"equipment_flat": 0, "equipment_pct": 0.7,
                         "hardware": 0.5, "homelab": 0}}
    effects = {"ecc": "regeneration", "corruption": "corruption",
               "defense": "defense", "armor_pen": "armor_penetration"}
    defs = []
    for typ, level in levels.items():
        defs.append({
            "name": typ.upper(), "type": typ, "current_level": level,
            "effects": [{"combat_stat": effects[typ],
                         "additive_per_level": 0.005}],
            # cost(L) = 30 * L**1.17, the shape fitted off live captures
            "next_cost": {"chips": round(30 * level ** 1.17),
                          "credits": 1000},
        })
    held = sum(levels.values())
    hw = {
        "definitions": defs, "stats_breakdown": stats,
        "can_reset": True, "highest_hardware_levels_held": held,
        "hardware_purchased": held * 2,
    }
    # The refund must be FULL VALUE under the same curve the planner fits, or
    # the fixture is not modelling this game: a short-changing refund makes
    # resetting a genuine loss, and asserting otherwise would only be testing
    # that the fixture agreed with itself.
    curve = ihlib.hardware_cost_curve(hw, family="combat")
    refund = round(sum(ihlib.hardware_cumulative(curve, lv)
                       for lv in levels.values()))
    hw["reset_section_options"] = [
        {"section": "all", "held_levels": held,
         "refund": {"chips": refund, "hackcoin": 8}},
        {"section": "combat", "held_levels": held // 2,
         "refund": {"chips": refund // 3, "hackcoin": 0}},
    ]
    return hw


class HardwarePlanTest(unittest.TestCase):
    """The chip allocator gained a disbelieving reading on 10 Aug 2026.

    Until then `hardware_track_value` read the module weights only, so the
    least reversible spend in the game — hardware cannot be sold back outside
    the monthly reset — was the one decision with no ex-suspect check, while
    `locks` and `potential` both decided on the weaker of the two readings.
    On the capture that surfaced it the raw-optimal plan sent 12% of the
    budget into a Corruption track whose stat sits 2.8x past its verified
    linear range.
    """

    def test_flagged_only_track_scores_zero_not_none_under_disbelief(self):
        """None means 'not modelled' and sorts a track into the unscored
        economy list, where no reader would ever see the two plans disagree
        about it. Disbelief must say 'worth nothing', not 'unknown'."""
        hw = _hardware_fixture()
        defn = next(d for d in hw["definitions"] if d["type"] == "corruption")
        sf = ihlib.suspect_free_weights()
        self.assertGreater(
            ihlib.hardware_track_value(defn, hw["stats_breakdown"]), 0)
        self.assertEqual(
            ihlib.hardware_track_value(defn, hw["stats_breakdown"], sf), 0.0)

    def test_disbelieving_plan_funds_no_flagged_family_track(self):
        hw = _hardware_fixture()
        sf = ihlib.suspect_free_weights()
        raw = ihlib.hardware_plan(hw, hw["stats_breakdown"], 400000)
        dis = ihlib.hardware_plan(hw, hw["stats_breakdown"], 400000,
                                  weights=sf)
        bought = {n: t for n, _ty, lv, t, _v, _c in raw if t > lv}
        self.assertIn("CORRUPTION", bought,
                      "fixture no longer exercises the disagreement")
        self.assertEqual(
            [t for n, _ty, lv, t, _v, _c in dis
             if n == "CORRUPTION" and t > lv], [],
            "the disbelieving plan still spends chips on a flagged family")

    def test_reset_gain_is_never_negative(self):
        """The dominance property the RESET block rests on: the refund is
        full value, so re-cutting can at worst reproduce what you held. A
        negative gain means the planner or the cost curve has broken, not
        that resetting is a bad idea — which is exactly the failure a
        priced-but-unguarded recommendation would hide."""
        sf = ihlib.suspect_free_weights()
        for held in ({"ecc": 200, "corruption": 80, "defense": 100,
                      "armor_pen": 60},
                     {"ecc": 20, "corruption": 300, "defense": 300,
                      "armor_pen": 20}):
            hw = _hardware_fixture(held)
            for weights in (None, sf):
                gain = ihlib.hardware_reset_gain(
                    hw, hw["stats_breakdown"], 100000, weights=weights)
                self.assertIsNotNone(gain)
                self.assertGreaterEqual(
                    gain["gain"], -1e-6,
                    f"reset priced as a LOSS for {held} — impossible under a "
                    f"full-value refund")

    def test_reset_gain_prices_the_all_section_refund(self):
        hw = _hardware_fixture()
        all_refund = next(o["refund"]["chips"]
                          for o in hw["reset_section_options"]
                          if o["section"] == "all")
        gain = ihlib.hardware_reset_gain(hw, hw["stats_breakdown"], 100000)
        self.assertEqual(gain["refund_chips"], all_refund)
        self.assertEqual(gain["budget"], 100000 + all_refund)

    def test_refund_shortfall_is_measured_against_the_curve(self):
        """The dominance argument is only as good as refund-vs-curve
        agreement, so that agreement is returned rather than assumed. A
        refund the game short-changes must show up as a shortfall AND as a
        priced loss — the number exists so a caller can tell the two apart."""
        hw = _hardware_fixture()
        gain = ihlib.hardware_reset_gain(hw, hw["stats_breakdown"], 100000)
        self.assertAlmostEqual(gain["refund_shortfall"], 0.0, places=4)
        for opt in hw["reset_section_options"]:
            if opt["section"] == "all":
                opt["refund"]["chips"] = int(opt["refund"]["chips"] * 0.5)
        halved = ihlib.hardware_reset_gain(hw, hw["stats_breakdown"], 100000)
        self.assertLess(halved["refund_shortfall"], -0.4)
        self.assertLess(halved["gain"], 0)

    def test_gain_is_cross_checked_under_the_other_weighting(self):
        """A re-cut planned under disbelief does not merely decline to BUY a
        flagged family — it tears down levels of it already held. So the
        dominance argument, which only holds inside one weighting, has to be
        re-run under the other one and reported. Guards the direction too:
        the cross score must come from the definitions, not from the value
        already baked into the plan rows."""
        hw = _hardware_fixture()
        sf = ihlib.suspect_free_weights()
        dis = ihlib.hardware_reset_gain(hw, hw["stats_breakdown"], 100000,
                                        weights=sf)
        raw = ihlib.hardware_reset_gain(hw, hw["stats_breakdown"], 100000)
        self.assertNotAlmostEqual(dis["gain"], dis["gain_cross"], places=3,
                                  msg="cross score reused the planned value, "
                                      "so it can never contradict `gain`")
        # the raw call's cross-check is the disbelieving one and vice versa
        self.assertAlmostEqual(raw["gain_cross"],
                               ihlib._hardware_plan_rescore(
                                   raw["reset_plan"], hw,
                                   hw["stats_breakdown"], sf)
                               - ihlib._hardware_plan_rescore(
                                   raw["keep_plan"], hw,
                                   hw["stats_breakdown"], sf),
                               places=6)

    def test_reset_gain_is_none_when_no_reset_is_available(self):
        hw = _hardware_fixture()
        hw["can_reset"] = False
        self.assertIsNone(
            ihlib.hardware_reset_gain(hw, hw["stats_breakdown"], 100000))


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
