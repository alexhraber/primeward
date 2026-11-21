"""The cheaper representation must still prove immediate succession."""

import unittest
from unittest.mock import patch

from flint import arb, ctx

from prime_successor.analytic import PrecisionLimitError, _past_primes
from prime_successor.engine import MillerRabinSuccessor, reference_primes
from prime_successor.fast_analytic import FastAnalyticSuccessor, ResidualAnalyticSuccessor


class TestResidualAnalyticSuccessor(unittest.TestCase):
    def test_identity_and_many_epoch_changes(self):
        engine = FastAnalyticSuccessor(1)
        expected = reference_primes(3000)
        for q in expected:
            self.assertEqual(engine.next_prime(), q)
        self.assertEqual(engine.stats.successor_steps, len(expected))
        self.assertGreater(engine.precision_work.epoch_bound_rebuilds, 4)
        self.assertEqual(engine.stats.future_candidate_primality_tests, 0)
        self.assertEqual(engine.stats.precision_retries, 0)
        self.assertIs(ResidualAnalyticSuccessor, FastAnalyticSuccessor)

    def test_arbitrary_entries_and_large_gaps(self):
        # 113->127, 523->541, and 1327->1361 exercise unusually large gaps.
        for start in (2, 3, 7, 31, 113, 523, 997, 1327, 10007):
            with self.subTest(start=start):
                engine = FastAnalyticSuccessor(start)
                self.assertEqual(engine.take(10), MillerRabinSuccessor(start).take(10))
                self.assertEqual(engine.exponent % 2, 0)
                self.assertTrue(engine.last_certificate["interval_containment_checked"])
                self.assertTrue(engine.last_certificate["epoch_bound_checked"])

    def test_residual_matches_independent_euler_product(self):
        engine = FastAnalyticSuccessor(113)
        for _ in range(12):
            with ctx.workprec(engine.precision_bits + 128):
                value = arb(engine.exponent).zeta()
                # Reconstruct independently, using a sieve solely in the test.
                for p in _past_primes(engine.current):
                    value *= 1 - arb(p) ** (-engine.exponent)
                self.assertTrue(engine._residual.overlaps(value - 1))
            engine.next_prime()

    def test_epoch_gate_rejects_out_of_range_successor(self):
        engine = FastAnalyticSuccessor(2)
        self.assertEqual(engine.epoch_successor_limit, 5)
        self.assertEqual(engine.take(2), [3, 5])
        exponent = engine.exponent
        self.assertIsNone(engine._try_extract())
        self.assertEqual(engine.next_prime(), 7)
        self.assertGreater(engine.exponent, exponent)
        self.assertGreater(engine.precision_work.epoch_bound_rebuilds, 0)

    def test_broad_enclosure_is_rejected_and_rebuilt(self):
        engine = FastAnalyticSuccessor(113)
        engine._residual = arb(0, 1)
        self.assertIsNone(engine._try_extract())
        rebuilds = engine.stats.state_rebuilds
        self.assertEqual(engine.next_prime(), 127)
        self.assertGreater(engine.stats.state_rebuilds, rebuilds)
        self.assertGreater(engine.stats.precision_retries, 0)

    def test_resource_refusal_preserves_prime_prefix_and_recovers(self):
        engine = FastAnalyticSuccessor(1, max_precision_bits=512)
        while True:
            previous = engine.current
            prefix = engine._primes[:]
            exponent = engine.exponent
            try:
                engine.next_prime()
            except PrecisionLimitError:
                self.assertEqual(engine.current, previous)
                self.assertEqual(engine._primes, prefix)
                self.assertEqual(engine.exponent, exponent)
                break
        engine.max_precision_bits = 10000
        self.assertEqual(engine.next_prime(), MillerRabinSuccessor(previous).next_prime())

    def test_lower_guard_and_precision_reuse(self):
        engine = FastAnalyticSuccessor(113, guard_bits=16)
        expected = MillerRabinSuccessor(113).take(100)
        # Once initialized, both updates and rebuilds must use the accepted
        # prime prefix, rather than another sieve or an oracle for future primes.
        with patch("prime_successor.fast_analytic._past_primes", side_effect=AssertionError):
            self.assertEqual(engine.take(100), expected)
        work = engine.precision_work
        self.assertLess(work.factor_precision_bits_sum, work.full_precision_factor_bits_sum)
        self.assertLess(work.transition_precision_bits_sum, work.full_transition_precision_bits_sum)
        self.assertLess(work.decoding_precision_bits_sum, work.full_decoding_precision_bits_sum)

    def test_diagnostics_are_lazy_and_consistent(self):
        engine = FastAnalyticSuccessor(113)
        self.assertIsNone(engine.last_certificate)
        self.assertEqual(engine.next_prime(), 127)
        self.assertIsNone(engine._certificate_cache)
        certificate = engine.last_certificate
        self.assertEqual(certificate["next"], 127)
        self.assertIs(certificate, engine.last_certificate)
        engine.next_prime()
        self.assertIsNone(engine._certificate_cache)
        self.assertEqual(certificate["next"], 127)
        self.assertEqual(engine.status()["last_certificate"]["next"], 131)

    def test_invalid_parameters_and_count(self):
        for start in (0, -1, 4, 9, True, 1.0):
            with self.subTest(start=start), self.assertRaises(ValueError):
                FastAnalyticSuccessor(start)
        for options in (
            {"guard_bits": 15},
            {"guard_bits": True},
            {"max_precision_bits": 63},
            {"max_precision_bits": 64.0},
            {"max_seed": 0},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                FastAnalyticSuccessor(1, **options)
        with self.assertRaises(PrecisionLimitError):
            FastAnalyticSuccessor(113, max_precision_bits=64)
        with self.assertRaises(PrecisionLimitError):
            FastAnalyticSuccessor(10 ** 100 + 1, max_seed=10 ** 101)
        with self.assertRaises(ValueError):
            FastAnalyticSuccessor(113, max_seed=100)
        engine = FastAnalyticSuccessor(1)
        for count in (-1, True, 1.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                engine.take(count)
        self.assertEqual(engine.take(0), [])


if __name__ == "__main__":
    unittest.main()
