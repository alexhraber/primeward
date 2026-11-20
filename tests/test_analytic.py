"""Independent arithmetic checks, boundary cases and precision refusal."""

import unittest

from prime_successor.analytic import AnalyticSuccessor, PrecisionLimitError


def independent_trial_prime(n):
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def independent_successor(n):
    q = n + 1
    while not independent_trial_prime(q):
        q += 1
    return q


class TestAnalyticSuccessor(unittest.TestCase):
    def test_identity_and_multiple_epoch_changes(self):
        engine = AnalyticSuccessor(1)
        previous = 1
        for _ in range(80):
            expected = independent_successor(previous)
            actual = engine.next_prime()
            self.assertEqual(actual, expected)
            self.assertTrue(engine.last_certificate["interval_containment_checked"])
            previous = actual
        self.assertGreater(engine.stats.state_rebuilds, 1)
        self.assertEqual(engine.stats.future_candidate_primality_tests, 0)

    def test_arbitrary_starts(self):
        for seed in [2, 3, 7, 31, 113, 997, 1009]:
            with self.subTest(seed=seed):
                engine = AnalyticSuccessor(seed)
                previous = seed
                for _ in range(5):
                    actual = engine.next_prime()
                    self.assertEqual(actual, independent_successor(previous))
                    previous = actual

    def test_reuses_state_inside_epoch(self):
        engine = AnalyticSuccessor(113)
        before = engine.stats.zeta_evaluations
        self.assertEqual(engine.take(5), [127, 131, 137, 139, 149])
        self.assertEqual(engine.stats.zeta_evaluations, before)

    def test_rejects_nonprime_or_invalid_seed(self):
        for value in [0, -1, 4, 9, 100, True, 3.0]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                AnalyticSuccessor(value)

    def test_precision_limit_is_honest(self):
        with self.assertRaises(PrecisionLimitError):
            AnalyticSuccessor(113, max_precision_bits=64)

    def test_bad_count(self):
        engine = AnalyticSuccessor(1)
        for count in [-1, True, 1.5]:
            with self.assertRaises(ValueError):
                engine.take(count)

    def test_epoch_precision_refusal_preserves_prime_state(self):
        engine = AnalyticSuccessor(1, max_precision_bits=300)
        self.assertEqual(engine.take(2), [2, 3])
        prefix = engine._primes.copy()
        exponent = engine.exponent
        with self.assertRaises(PrecisionLimitError):
            engine.next_prime()
        self.assertEqual(engine.current, 3)
        self.assertEqual(engine._primes, prefix)
        self.assertEqual(engine.exponent, exponent)
        engine.max_precision_bits = 1_000
        self.assertEqual(engine.next_prime(), 5)


if __name__ == "__main__":
    unittest.main()
