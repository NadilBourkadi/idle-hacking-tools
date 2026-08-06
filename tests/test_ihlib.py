"""Seed test suite — the eight highest-confidence-per-line tests from the
public-release audit (6 Aug 2026). unittest-style on purpose: the project is
zero-dependency, so the suite must run on a bare interpreter with
`python3 -m unittest discover tests`. pytest runs it unchanged in CI.

Each test names the incident it guards against where one exists; regression
tests without a story are just tests, but most of these have one.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
        self.phases = [(name, to) for name, _from, to, _att, _meas
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
        for _name, _from, target, _attempts, _measured in plan["steps"]:
            self.assertGreaterEqual(target, 1)
        capped = ihlib.plan_craft(item, ladders, tier_cap=3)
        for _name, _from, target, _attempts, _measured in capped["steps"]:
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
