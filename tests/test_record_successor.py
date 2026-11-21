import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from experiments.record_successor import (
    MAX_SEED, RECORD_EXPONENT, bounded_case, engine_probe, markdown_summary,
    requirement_report, verify_successor,
)

class RecordSuccessorTests(unittest.TestCase):
    def test_record_requirements_are_symbolic(self):
        r = requirement_report(RECORD_EXPONENT)
        self.assertEqual(r["input_binary_digits"], 136279841)
        self.assertEqual(r["input_decimal_digits"], 41024320)
        self.assertEqual(r["input_packed_bytes"], 17034981)
        self.assertEqual(r["seed_sieve_bytes"]["exact"], "2^136279841")
        self.assertEqual(r["initial_precision_lower_budget_bits"]["exact"],
                         "(2^136279841+2)*136279842+256")
        self.assertEqual(r["initial_precision_lower_budget_bits"]["decimal_digits"], 41024329)
        self.assertTrue(r["seed_exceeds_platform_index"])

    def test_guard_precedes_history_allocation(self):
        with patch("prime_successor.fast_analytic._past_primes",
                   side_effect=AssertionError("must not allocate history")):
            r = engine_probe(31)
        self.assertEqual(r["status"], "blocked_max_seed")
        self.assertFalse(r["residual_initialized"])
        self.assertFalse(r["successor_certified"])
        self.assertIsNone(r["successor"])

    def test_precision_refusal_is_distinct(self):
        r = engine_probe(13, max_precision_bits=1000)
        self.assertEqual(r["status"], "blocked_precision")
        self.assertFalse(r["successor_certified"])

    def test_composite_start_is_not_a_resource_refusal(self):
        with self.assertRaisesRegex(ValueError, "prime"):
            engine_probe(4)

    def test_real_analytic_answer_and_independent_minimality(self):
        r = engine_probe(5)
        self.assertEqual(r["successor"], 37)
        self.assertEqual(r["certificate"]["exponent"], 34)
        self.assertEqual(r["certificate"]["precision_bits"], 461)
        self.assertTrue(r["successor_certified"])
        self.assertTrue(r["certificate"]["interval_containment_checked"])
        self.assertEqual(r["future_candidate_primality_tests_engine"], 0)
        self.assertTrue(verify_successor(31, 37))
        self.assertFalse(verify_successor(31, 41))

    def test_bounded_worker(self):
        r = bounded_case(7, timeout_seconds=10)
        self.assertEqual(r["successor"], 131)
        self.assertTrue(r["successor_certified"])

    def test_summary_does_not_turn_refusal_into_discovery(self):
        case = engine_probe(31)
        text = markdown_summary({"experiment": "target", "case": case,
                                 "requirements": requirement_report(31)})
        self.assertIn("No next prime was produced", text)
        self.assertIn("Successor certified: **false**", text)

    def test_cli_writes_strict_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"result.json"
            p = subprocess.run([sys.executable, "-B", "-m", "experiments.record_successor",
                                "target", "--exponent", "31", "--output", str(output)],
                               capture_output=True, text=True, timeout=20)
            self.assertEqual(p.returncode, 0, p.stderr)
            data = json.loads(output.read_text())
            self.assertTrue(data["experiment_completed"])
            self.assertFalse(data["case"]["successor_certified"])
            self.assertTrue(output.with_suffix(".md").is_file())

    def test_invalid_exponents_and_bounds(self):
        for e in (True, 0, -1, 150000001):
            with self.assertRaises(ValueError):
                requirement_report(e)
        with self.assertRaises(ValueError):
            bounded_case(5, timeout_seconds=0)
