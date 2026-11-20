"""Correctness tests target boundaries, completeness and resume validation."""

import bisect
import json
import random
import unittest

from prime_successor.engine import (
    BytearraySieveSuccessor,
    MillerRabinSuccessor,
    ResidueBitsetSuccessor,
    SieveLimitError,
    TrialDivisionSuccessor,
    UINT64_MAX,
    is_prime_trial,
    is_prime_u64,
    reference_primes,
)


SIEVES = (ResidueBitsetSuccessor, BytearraySieveSuccessor)
ENGINES = SIEVES + (MillerRabinSuccessor, TrialDivisionSuccessor)


class PrimalityTests(unittest.TestCase):
    def test_independent_agreement_for_small_domain(self):
        actual = set(reference_primes(20_000))
        for n in range(20_001):
            self.assertEqual(is_prime_u64(n), n in actual, n)
            self.assertEqual(is_prime_trial(n), n in actual, n)

    def test_pseudoprimes_and_u64_boundary(self):
        # These composites defeat some weaker, small fixed-base tests.
        for n in (341, 561, 1105, 1729, 3215031751, 341550071728321,
                  3825123056546413051, UINT64_MAX):
            self.assertFalse(is_prime_u64(n), n)
        self.assertTrue(is_prime_u64(18446744073709551557))
        self.assertTrue(is_prime_u64(2305843009213693951))

    def test_domain_is_explicit(self):
        for invalid in (-1, UINT64_MAX + 1):
            with self.assertRaises(ValueError):
                is_prime_u64(invalid)
        for invalid in (True, 2.0, "2"):
            with self.assertRaises(TypeError):
                is_prime_u64(invalid)


class SuccessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.primes = reference_primes(250_000)

    def test_identity_seed_is_not_a_prime(self):
        self.assertFalse(is_prime_u64(1))
        for engine_type in ENGINES:
            engine = engine_type(1)
            self.assertEqual(engine.take(25), self.primes[:25], engine_type.__name__)
            self.assertEqual(engine.stats.seed_primality_tests, 0)

    def test_seed_is_excluded_and_bad_seeds_rejected(self):
        for engine_type in ENGINES:
            self.assertEqual(engine_type(113).next_prime(), 127)
            self.assertEqual(engine_type(2).next_prime(), 3)
            for composite in (0, 4, 9, 25, 121):
                with self.assertRaises(ValueError):
                    engine_type(composite)
            with self.assertRaises(TypeError):
                engine_type(True)

    def test_many_block_sizes_and_square_boundaries(self):
        # One-slot blocks force complete exhaustion; other lengths move square
        # crossings through every part of a block.  Tiny blocks also contain
        # zero-prime segments, so skipping an empty block is exercised.
        starts = (1, 2, 3, 7, 23, 47, 113, 127, 241, 997, 10_007)
        for engine_type in SIEVES:
            for block_size in (1, 2, 3, 7, 31, 128, 4096):
                for start in starts:
                    engine = engine_type(start, block_size=block_size)
                    position = bisect.bisect_right(self.primes, start)
                    self.assertEqual(engine.take(100), self.primes[position:position + 100],
                                     (engine_type.__name__, block_size, start))
                    self.assertEqual(engine.stats.candidates_tested, 0)

    def test_arbitrary_entries_and_evolving_base_table(self):
        rng = random.Random(20261120)
        for engine_type in SIEVES:
            for index in rng.sample(range(100, len(self.primes) - 100), 25):
                engine = engine_type(self.primes[index], block_size=17)
                self.assertEqual(engine.take(50), self.primes[index + 1:index + 51])
                self.assertEqual(engine._base_primes, reference_primes(engine._base_limit))

    def test_long_stream_crosses_new_divisor_squares(self):
        for engine_type in SIEVES:
            engine = engine_type(1, block_size=19)
            self.assertEqual(engine.take(10_000), self.primes[:10_000])
            self.assertGreater(engine.stats.base_extensions, 1)
            self.assertGreater(engine.stats.blocks_built, 1)
            self.assertEqual(engine.stats.outputs, 10_000)
            self.assertEqual(engine._base_primes, reference_primes(engine._base_limit))

    def test_large_arbitrary_entry_matches_separate_scalar_method(self):
        # Large enough to exercise a nontrivial initialization cost, still small
        # enough to keep this a targeted portable test.
        start = 1_000_000_007
        expected = MillerRabinSuccessor(start).take(100)
        for engine_type in SIEVES:
            engine = engine_type(start, block_size=509)
            self.assertEqual(engine.take(100), expected)

    def test_resume_in_middle_and_after_empty_payload(self):
        for engine_type in SIEVES:
            for block_size in (1, 7, 4096):
                engine = engine_type(113, block_size=block_size)
                engine.take(23)
                checkpoint = json.loads(engine.dumps())
                resumed = engine_type.from_snapshot(checkpoint)
                self.assertEqual(resumed.current, engine.current)
                self.assertEqual(resumed.take(200), engine.take(200))
                self.assertEqual(resumed.stats.outputs, 200)  # New process counters.
                self.assertGreaterEqual(resumed.stats.setup_seconds, 0)

    def test_checkpoint_tampering_does_not_bypass_seed_validation(self):
        checkpoint = ResidueBitsetSuccessor(113).snapshot()
        checkpoint["current"] = 121
        with self.assertRaises(ValueError):
            ResidueBitsetSuccessor.from_snapshot(checkpoint)
        checkpoint = ResidueBitsetSuccessor(113).snapshot()
        checkpoint["survivor_bits"] = "fabricated"
        with self.assertRaises(ValueError):
            ResidueBitsetSuccessor.from_snapshot(checkpoint)
        with self.assertRaises(ValueError):
            BytearraySieveSuccessor.from_snapshot(ResidueBitsetSuccessor(113).snapshot())

    def test_resource_boundary_is_not_claimed_to_be_end_of_primes(self):
        for engine_type in SIEVES:
            engine = engine_type(19, block_size=100, max_base_limit=5)
            self.assertEqual(engine.next_prime(), 23)
            with self.assertRaises(SieveLimitError):
                engine.next_prime()
            with self.assertRaises(SieveLimitError):
                engine_type(101, max_base_limit=5)

    def test_scalar_domain_boundary(self):
        engine = MillerRabinSuccessor(18446744073709551557)
        with self.assertRaises(OverflowError):
            engine.next_prime()

    def test_accounting_and_empty_requests(self):
        for engine_type in SIEVES:
            engine = engine_type(113, block_size=64)
            self.assertEqual(engine.take(0), [])
            self.assertEqual(engine.current, 113)
            self.assertEqual(next(engine), 127)
            self.assertEqual(engine.last_step["previous"], 113)
            self.assertEqual(engine.last_step["prime"], 127)
            self.assertEqual(engine.stats.intervening_integers, 13)
            self.assertGreater(engine.memory_bytes_estimate(), 0)
            self.assertGreater(engine.stats.candidate_slots_materialized, 0)
            self.assertGreaterEqual(engine.stats.advance_seconds, engine.stats.block_build_seconds)
            json.dumps(engine.stats.to_dict())
            with self.assertRaises(ValueError):
                engine.take(-1)


if __name__ == "__main__":
    unittest.main()
