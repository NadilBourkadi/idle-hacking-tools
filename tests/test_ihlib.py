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
