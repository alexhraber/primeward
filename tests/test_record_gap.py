"""Independent checks for the bounded Mersenne successor screening experiment."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from experiments.record_gap import (MAX_EXPONENT, MAX_SPAN, MAX_TRIAL_LIMIT,
                                    primes_through, screen)


def simple_next_prime(n: int) -> int:
    def prime(k):
        return k >= 2 and all(k % d for d in range(2, math.isqrt(k) + 1))
    return next(k for k in range(n + 1, n + 400) if prime(k))


class MersenneScreenTests(unittest.TestCase):
    def test_known_successors_are_certified(self):
        for exponent, expected in [(2, 5), (3, 11), (5, 37), (7, 131), (13, 8209)]:
            with self.subTest(exponent=exponent):
                result = screen(exponent, span=40, trial_limit=200)
                self.assertEqual(result["successor"], expected)
                self.assertTrue(result["successor_certified"])
                self.assertEqual(result["status"], "certified_successor")
                self.assertEqual(result["successor"], simple_next_prime((1 << exponent) - 1))

    def test_small_limit_never_certifies_big_candidate(self):
        r = screen(13, span=40, trial_limit=7)
        self.assertEqual(r["status"], "partial_screen")
        self.assertIsNone(r["successor"])
        self.assertFalse(r["successor_certified"])

    def test_all_witnesses_are_real_factors(self):
        for exponent in (5, 7, 13, 31):
            r = screen(exponent, span=100, trial_limit=1000, preview=64)
            for entry in r["composite_witness_samples"]:
                d, k = entry["divisor"], entry["offset_k"]
                self.assertEqual(((1 << exponent) - 1 + 2 * k) % d, 0)
                self.assertLess(d, (1 << exponent) - 1 + 2 * k)
            for k in r["unexcluded_offset_samples"]:
                n = (1 << exponent) - 1 + 2 * k
                self.assertFalse(any(n % d == 0 and n != d for d in primes_through(1000)))

    def test_record_does_not_materialize_start(self):
        r = screen(136_279_841, span=128, trial_limit=500)
        self.assertEqual(r["status"], "partial_screen")
        self.assertIsNone(r["successor"])
        self.assertFalse(r["successor_certified"])
        self.assertEqual(r["composite_witness_samples"][0]["divisor"], 3)
        self.assertEqual(r["composite_witness_samples"][0]["offset_k"], 1)
        self.assertEqual(r["composite_witness_samples"][1]["offset_k"], 2)
        self.assertEqual(r["composite_witness_samples"][1]["divisor"], 5)

    def test_all_composite_status(self):
        r = screen(5, span=2, trial_limit=100)
        self.assertEqual(r["status"], "all_screened_candidates_composite")
        self.assertEqual(r["lower_bound_distance_to_next_prime"], 6)

    def test_parameters_are_bounded(self):
        for kwargs in (
            {"exponent": 1}, {"exponent": MAX_EXPONENT + 1},
            {"exponent": 5, "span": MAX_SPAN + 1},
            {"exponent": 5, "trial_limit": MAX_TRIAL_LIMIT + 1},
            {"exponent": 5, "preview": 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                screen(**kwargs)

    def test_cli_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run.json"
            p = subprocess.run([sys.executable, "-m", "experiments.record_gap",
                                "--exponent", "7", "--span", "30",
                                "--trial-limit", "100", "--out", str(out)],
                               capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(p.stdout), json.loads(out.read_text()))
            self.assertEqual(json.loads(p.stdout)["successor"], 131)


if __name__ == "__main__":
    unittest.main()
