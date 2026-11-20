"""Mixed precision must preserve certified, immediate succession."""

import unittest

from flint import arb, ctx

from prime_successor.analytic import AnalyticSuccessor, PrecisionLimitError
from prime_successor.engine import MillerRabinSuccessor, reference_primes
from prime_successor.optimized import PrecisionAwareSuccessor


class TestPrecisionAwareSuccessor(unittest.TestCase):
    def test_identity_and_several_epoch_changes(self):
        engine = PrecisionAwareSuccessor(1)
        self.assertEqual(engine.take(200), reference_primes(1223))
        self.assertGreater(engine.stats.state_rebuilds, 1)
        self.assertEqual(engine.stats.future_candidate_primality_tests, 0)
        self.assertEqual(engine.precision_work.decoding_attempts, 200)

    def test_arbitrary_entry_and_state_overlap(self):
        for start in (2, 3, 7, 31, 113, 997):
            with self.subTest(start=start):
                optimized = PrecisionAwareSuccessor(start)
                original = AnalyticSuccessor(start)
                expected = MillerRabinSuccessor(start).take(10)
                self.assertTrue(optimized._value.overlaps(original._value))
                for q in expected:
                    self.assertEqual(optimized.next_prime(), q)
                    self.assertEqual(original.next_prime(), q)
                    self.assertTrue(optimized._value.overlaps(original._value))
                    self.assertTrue(optimized.last_certificate["interval_containment_checked"])

    def test_precision_budget_and_reuse_are_observable(self):
        engine = PrecisionAwareSuccessor(113)
        initial_evaluations = engine.stats.zeta_evaluations
        self.assertEqual(engine.take(5), [127, 131, 137, 139, 149])
        self.assertEqual(engine.stats.zeta_evaluations, initial_evaluations)
        work = engine.precision_work
        self.assertGreater(work.reduced_precision_factors, 0)
        self.assertLess(work.factor_precision_bits_sum, work.full_precision_factor_bits_sum)
        self.assertLess(work.decoding_precision_bits_sum, work.full_decoding_precision_bits_sum)

    def test_inconclusive_interval_is_rejected_then_rebuilt(self):
        engine = PrecisionAwareSuccessor(113)
        # A deliberately broad enclosure of the true near-one state cannot
        # certify the residual.  The parent must rebuild before accepting.
        with ctx.workprec(engine.precision_bits):
            engine._value = arb(1, "0.1")
        self.assertIsNone(engine._try_extract())
        before = engine.stats.state_rebuilds
        self.assertEqual(engine.next_prime(), 127)
        self.assertGreater(engine.stats.state_rebuilds, before)
        self.assertGreater(engine.stats.precision_retries, 0)

    def test_epoch_precision_failure_preserves_state(self):
        engine = PrecisionAwareSuccessor(1, max_precision_bits=512)
        while engine.current <= engine.exponent // 2:
            engine.next_prime()
        # The first small epoch transition fits.  Continue until a prospective
        # epoch exceeds the cap, keeping the last accepted prefix intact.
        while True:
            previous = engine.current
            prefix = engine._primes[:]
            try:
                engine.next_prime()
            except PrecisionLimitError:
                self.assertEqual(engine.current, previous)
                self.assertEqual(engine._primes, prefix)
                break
        engine.max_precision_bits = 10_000
        self.assertEqual(engine.next_prime(), MillerRabinSuccessor(previous).next_prime())


if __name__ == "__main__":
    unittest.main()
