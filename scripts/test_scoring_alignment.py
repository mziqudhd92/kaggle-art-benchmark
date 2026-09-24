#!/usr/bin/env python3
"""Unit tests for ART scoring alignment (no Kaggle network)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "01_label_triage.py"


def _load_triage_module():
    # Stub kaggle_benchmarks so the task module imports offline.
    import functools
    import types

    kbench = types.ModuleType("kaggle_benchmarks")
    assertions = types.ModuleType("kaggle_benchmarks.assertions")

    class _Task:
        def __init__(self, fn):
            self._fn = fn
            functools.update_wrapper(self, fn)

        def __call__(self, *a, **k):
            return self._fn(*a, **k)

        def run(self, *a, **k):
            return None

        def evaluate(self, *a, **k):
            raise RuntimeError("evaluate not available in unit test stub")

    def task(**kwargs):
        def deco(fn):
            return _Task(fn)

        return deco

    kbench.task = task
    kbench.llm = None
    sys.modules["kaggle_benchmarks"] = kbench
    sys.modules["kaggle_benchmarks.assertions"] = assertions

    spec = importlib.util.spec_from_file_location("art_label_triage", TASK)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class ArtScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_triage_module()

    def test_perfect_score(self):
        items = self.mod.load_items()
        hits = {i: True for i in range(len(items))}
        self.assertEqual(self.mod.compute_art_score(items, hits), 1.0)

    def test_missing_rows_count_as_miss(self):
        items = self.mod.load_items()
        # Only first half present → not a positional shift of results.
        hits = {i: True for i in range(len(items) // 2)}
        score = self.mod.compute_art_score(items, hits)
        self.assertLess(score, 1.0)
        self.assertGreaterEqual(score, 0.0)

    def test_shifted_results_do_not_misbucket(self):
        """Regression: completed.result list order must not be used by index alone."""
        items = self.mod.load_items()
        # Simulate: item 0 failed (missing), items 1..n-1 succeeded — param ids preserved.
        hits = {i: True for i in range(1, len(items))}
        by_id = self.mod.compute_art_score(items, hits)
        # Wrong (legacy) approach would zip preds=[True]*(n-1) onto items[0:n-1]
        legacy_preds = [True] * (len(items) - 1)
        raw_hits = raw_n = patched_hits = patched_n = filler_hits = filler_n = 0
        for idx, row in enumerate(items):
            if idx >= len(legacy_preds):
                break
            hit = bool(legacy_preds[idx])
            role = row.get("twin_role")
            if role == "vuln":
                raw_n += 1
                raw_hits += int(hit)
            elif role == "patched":
                patched_n += 1
                patched_hits += int(hit)
            else:
                filler_n += 1
                filler_hits += int(hit)
        legacy = 0.4 * (raw_hits / raw_n) + 0.4 * (patched_hits / patched_n) + 0.2 * (
            filler_hits / filler_n
        )
        # With first item missing as miss, by_id scores the first row False.
        # Legacy wrongly scores the first row True (shifted). They must differ
        # whenever item 0 is in a non-empty bucket (always true for our suite).
        self.assertNotEqual(round(by_id, 6), round(legacy, 6))

    def test_hits_by_param_id_parser(self):
        df = pd.DataFrame(
            [
                {"id": 2, "result": True},
                {"id": 0, "result": False},
            ]
        )
        hits = self.mod._hits_by_param_id(df)
        self.assertEqual(hits, {2: True, 0: False})

    def test_normalize_label(self):
        self.assertEqual(self.mod._normalize_label(" patched "), "patched")
        self.assertIsNone(self.mod._normalize_label("not_a_label"))
        self.assertIsNone(self.mod._normalize_label(""))


if __name__ == "__main__":
    unittest.main()
