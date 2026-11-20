"""Exact successor baselines with explicit arithmetic state and work accounting.

``ResidueBitsetSuccessor`` is a segmented sieve.  It marks odd arithmetic
progressions in integer bitsets and extracts the lowest surviving bit.  It does
not test individual candidates for primality, but it does materialize and sieve
whole blocks.  It is NOT a newly discovered direct prime recurrence.

Correctness invariant: before a block is exposed, every prime divisor up to the
square root of its last integer has been included.  Every composite in the block
therefore has a cleared bit, and every prime has a surviving bit.  Blocks and
surviving bits are consumed in increasing order, proving immediate succession.

The initial value 1 is accepted as an explicit identity seed, and its successor
is 2.  The implementation never classifies 1 as prime.  Other seeds must be prime.
Primality validation and the scalar Miller--Rabin baseline are restricted to
unsigned 64-bit integers.  Sieve engines have an additional, explicit resource
budget on the largest small prime they generate.

All engines accept ``start``, expose ``current``, ``stats``, ``next_prime()`` and
``take(count)``.  The sieve engines additionally support checkpoint/resume.
The seed itself is not included in ``take``.  Setup and advancing time are
separate; base-generation and block-building time are subsets of advancing time,
so those nested timings must not be added to total time again.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isqrt
from time import perf_counter
from typing import Any, Iterator
import json
import sys


UINT64_MAX = (1 << 64) - 1
DEFAULT_BASE_LIMIT = 2_000_000
DEFAULT_BLOCK_SIZE = 4096  # Number of odd positions, not numeric interval width.
MAX_BLOCK_SIZE = 1_048_576
CHECKPOINT_VERSION = 1


class SieveLimitError(ValueError):
    """The next block exceeds the configured resource budget, not mathematics."""


def _integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def is_prime_u64(n: int) -> bool:
    """Deterministic Miller--Rabin for 0 <= n <= 2**64 - 1.

    Uses the standard seven-witness unsigned-64-bit set, recorded by Jim Sinclair
    at https://miller-rabin.appspot.com/ and described by Forisek and Jancina in
    https://ceur-ws.org/Vol-1326/020-Forisek.pdf .  This is an exact bounded-domain
    test, not a claim about arbitrary Python integers.  Invalid domains are
    rejected explicitly instead of silently becoming probabilistic.
    """
    _integer(n, "n", 0, UINT64_MAX)
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d = n - 1
    powers_of_two = 0
    while d % 2 == 0:
        powers_of_two += 1
        d //= 2
    for witness in (2, 325, 9375, 28178, 450775, 9780504, 1795265022):
        a = witness % n
        if a == 0:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(powers_of_two - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def is_prime_trial(n: int) -> bool:
    """Slow independent exact reference; primarily useful for small tests."""
    _integer(n, "n", 0, UINT64_MAX)
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    return all(n % divisor for divisor in range(3, isqrt(n) + 1, 2))


def reference_primes(limit: int) -> list[int]:
    """Independent ordinary bytearray sieve, inclusive at ``limit``.

    This deliberately regenerates all primes up to the limit.  It is used to
    make finite test datasets, not as the successor algorithm.
    """
    _integer(limit, "limit", 0, UINT64_MAX)
    if limit < 2:
        return []
    flags = bytearray(b"\x01") * (limit + 1)
    flags[0:2] = b"\x00\x00"
    for p in range(2, isqrt(limit) + 1):
        if flags[p]:
            count = (limit - p * p) // p + 1
            flags[p * p::p] = bytes(count)
    return [n for n, flag in enumerate(flags) if flag]


@dataclass
class EngineStats:
    setup_seconds: float = 0.0
    advance_seconds: float = 0.0
    base_generation_seconds: float = 0.0
    block_build_seconds: float = 0.0
    seed_primality_tests: int = 0
    candidates_tested: int = 0
    blocks_built: int = 0
    base_extensions: int = 0
    base_primes_generated: int = 0
    candidate_slots_materialized: int = 0
    prime_progressions: int = 0
    composite_marks: int = 0  # Counts overlapping markings, not unique composites.
    outputs: int = 0
    intervening_integers: int = 0

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


class _SuccessorBase:
    """Shared input handling and accounting, not a prime-generation strategy."""

    def __init__(self, start: int = 1) -> None:
        began = perf_counter()
        self.stats = EngineStats()
        self.start = _integer(start, "start", 1, UINT64_MAX)
        if start != 1:
            self.stats.seed_primality_tests = 1
            if not is_prime_u64(start):
                raise ValueError("start must be 1 or a known prime")
        self.current = start
        self.last_step: dict[str, Any] | None = None
        self.stats.setup_seconds = perf_counter() - began

    def _accept(self, result: int, method: str) -> int:
        previous = self.current
        self.current = result
        self.stats.outputs += 1
        self.stats.intervening_integers += result - previous - 1
        self.last_step = {
            "previous": previous,
            "prime": result,
            "gap": result - previous,
            "method": method,
        }
        return result

    def take(self, count: int) -> list[int]:
        _integer(count, "count", 0, UINT64_MAX)
        return [self.next_prime() for _ in range(count)]

    def __iter__(self) -> _SuccessorBase:
        return self

    def __next__(self) -> int:
        return self.next_prime()

    def next_prime(self) -> int:
        raise NotImplementedError


class MillerRabinSuccessor(_SuccessorBase):
    """Scalar baseline: test successive odd candidates, with exact u64 tests."""

    def next_prime(self) -> int:
        began = perf_counter()
        try:
            if self.current == 1:
                return self._accept(2, "deterministic Miller-Rabin candidate scan")
            candidate = 3 if self.current == 2 else self.current + 2
            while candidate <= UINT64_MAX:
                self.stats.candidates_tested += 1
                if is_prime_u64(candidate):
                    return self._accept(candidate, "deterministic Miller-Rabin candidate scan")
                candidate += 2
            raise OverflowError("No successor available within the unsigned 64-bit domain")
        finally:
            self.stats.advance_seconds += perf_counter() - began


class TrialDivisionSuccessor(_SuccessorBase):
    """Slower independent scalar reference, for small benchmark ranges only."""

    def next_prime(self) -> int:
        began = perf_counter()
        try:
            if self.current == 1:
                return self._accept(2, "trial division candidate scan")
            candidate = 3 if self.current == 2 else self.current + 2
            while candidate <= UINT64_MAX:
                self.stats.candidates_tested += 1
                if is_prime_trial(candidate):
                    return self._accept(candidate, "trial division candidate scan")
                candidate += 2
            raise OverflowError("No successor available within the unsigned 64-bit domain")
        finally:
            self.stats.advance_seconds += perf_counter() - began


class _SegmentedSuccessorBase(_SuccessorBase):
    """A complete small-prime table and carried strike positions for odd blocks."""

    engine_name = "abstract"

    def __init__(
        self,
        start: int = 1,
        block_size: int = DEFAULT_BLOCK_SIZE,
        max_base_limit: int = DEFAULT_BASE_LIMIT,
    ) -> None:
        began = perf_counter()
        super().__init__(start)
        self.block_size = _integer(block_size, "block_size", 1, MAX_BLOCK_SIZE)
        self.max_base_limit = _integer(max_base_limit, "max_base_limit", 2, isqrt(UINT64_MAX))
        self.max_integer = min(UINT64_MAX, self.max_base_limit * self.max_base_limit)
        if start >= self.max_integer:
            raise SieveLimitError("Seed exceeds the small-prime resource budget; increase max_base_limit")
        self._base_primes: list[int] = [2]
        self._base_limit = 2
        self._next_strike: dict[int, int] = {}
        self._block_low = 3 if start <= 2 else start + 2
        self._block_count = 0
        self._next_block_low = self._block_low
        self._reset_payload()
        self.stats.base_primes_generated = 1
        self.stats.setup_seconds = perf_counter() - began

    def _extend_base_primes(self, target: int) -> None:
        """Extend the complete small-prime table without restarting it at zero."""
        if target <= self._base_limit:
            return
        root = isqrt(target)
        if root > self._base_limit:
            self._extend_base_primes(root)
        low = self._base_limit + 1
        if low % 2 == 0:
            low += 1
        count = max(0, (target - low) // 2 + 1)
        if count:
            flags = bytearray(b"\x01") * count
            for p in self._base_primes:
                if p == 2:
                    continue
                if p * p > target:
                    break
                first = max(p * p, ((low + p - 1) // p) * p)
                if first % 2 == 0:
                    first += p
                index = (first - low) // 2
                if index < count:
                    flags[index::p] = bytes((count - 1 - index) // p + 1)
            new_primes = [low + 2 * i for i, present in enumerate(flags) if present]
            self._base_primes.extend(new_primes)
            self.stats.base_primes_generated += len(new_primes)
        self._base_limit = target
        self.stats.base_extensions += 1

    def _ensure_base_primes(self, required: int) -> None:
        if required > self.max_base_limit:
            raise SieveLimitError("Small-prime budget exhausted; increase max_base_limit")
        if required <= self._base_limit:
            return
        began = perf_counter()
        target = min(self.max_base_limit, max(required, 2 * self._base_limit))
        self._extend_base_primes(target)
        self.stats.base_generation_seconds += perf_counter() - began

    def _progressions(self, low: int, count: int) -> Iterator[tuple[int, int, int]]:
        """Yield first bit, stride, count for each composite progression."""
        high = low + 2 * (count - 1)
        for p in self._base_primes:
            if p == 2:
                continue
            if p * p > high:
                break
            first = self._next_strike.get(p)
            if first is None or first < low:
                first = max(p * p, ((low + p - 1) // p) * p)
                if first % 2 == 0:
                    first += p
            if first > high:
                self._next_strike[p] = first
                continue
            index = (first - low) // 2
            marks = (count - 1 - index) // p + 1
            self._next_strike[p] = first + 2 * p * marks
            self.stats.prime_progressions += 1
            self.stats.composite_marks += marks
            yield index, p, marks

    def _build_next_block(self) -> None:
        began = perf_counter()
        low = self._next_block_low
        if low > self.max_integer:
            raise SieveLimitError("No further block fits the small-prime resource budget")
        count = min(self.block_size, (self.max_integer - low) // 2 + 1)
        if count <= 0:
            raise SieveLimitError("No further block fits the small-prime resource budget")
        high = low + 2 * (count - 1)
        self._ensure_base_primes(isqrt(high))
        self._block_low = low
        self._block_count = count
        self._make_payload(low, count)
        self._next_block_low = high + 2
        self.stats.blocks_built += 1
        self.stats.candidate_slots_materialized += count
        self.stats.block_build_seconds += perf_counter() - began

    def next_prime(self) -> int:
        began = perf_counter()
        try:
            if self.current == 1:
                return self._accept(2, self.engine_name)
            while True:
                index = self._pop_index()
                if index is not None:
                    result = self._block_low + 2 * index
                    result = self._accept(result, self.engine_name)
                    self.last_step["complete_small_prime_table_through"] = self._base_limit
                    self.last_step["block_low"] = self._block_low
                    self.last_step["block_high"] = self._block_low + 2 * (self._block_count - 1)
                    return result
                self._build_next_block()
        finally:
            self.stats.advance_seconds += perf_counter() - began

    def _reset_payload(self) -> None:
        raise NotImplementedError

    def _make_payload(self, low: int, count: int) -> None:
        raise NotImplementedError

    def _pop_index(self) -> int | None:
        raise NotImplementedError

    def payload_bytes(self) -> int:
        raise NotImplementedError

    def memory_bytes_estimate(self) -> int:
        """Approximate live Python state; excludes interpreter and shared code.

        Integer object sizes may be counted twice if Python shares an object.
        The payload, base table and strike-position dictionary are included.
        This is an instrumented estimate, not process peak resident memory.
        """
        return (
            sys.getsizeof(self._base_primes)
            + sum(sys.getsizeof(p) for p in self._base_primes)
            + sys.getsizeof(self._next_strike)
            + sum(sys.getsizeof(p) + sys.getsizeof(n) for p, n in self._next_strike.items())
            + self.payload_bytes()
        )

    def snapshot(self) -> dict[str, Any]:
        """Compact resume token.  Arithmetic caches are intentionally rebuilt.

        Only the current location and parameters are persisted.  Rebuilding
        avoids trusting unvalidated user-supplied survivor bits.  Initialization
        at an arbitrary prime still requires small primes through its square
        root; this is not a free random-access state construction.
        """
        return {
            "version": CHECKPOINT_VERSION,
            "engine": self.engine_name,
            "current": self.current,
            "block_size": self.block_size,
            "max_base_limit": self.max_base_limit,
            "cache_policy": "rebuild from validated current prime",
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> _SegmentedSuccessorBase:
        if not isinstance(data, dict):
            raise TypeError("snapshot must be an object")
        expected = {"version", "engine", "current", "block_size", "max_base_limit", "cache_policy"}
        if set(data) != expected:
            raise ValueError("Snapshot has missing or unexpected fields")
        if data["version"] != CHECKPOINT_VERSION or isinstance(data["version"], bool):
            raise ValueError("Unsupported checkpoint version")
        if data["engine"] != cls.engine_name:
            raise ValueError("Checkpoint engine does not match this class")
        if data["cache_policy"] != "rebuild from validated current prime":
            raise ValueError("Unsupported checkpoint cache policy")
        return cls(data["current"], data["block_size"], data["max_base_limit"])

    def dumps(self) -> str:
        return json.dumps(self.snapshot(), sort_keys=True)

    @classmethod
    def loads(cls, text: str) -> _SegmentedSuccessorBase:
        return cls.from_snapshot(json.loads(text))


class ResidueBitsetSuccessor(_SegmentedSuccessorBase):
    """Exact segmented sieve using bulk bit masks and least-set-bit extraction."""

    engine_name = "residue_bitset_sieve"

    def _reset_payload(self) -> None:
        self._bits = 0

    def _make_payload(self, low: int, count: int) -> None:
        bits = (1 << count) - 1
        for first, stride, marks in self._progressions(low, count):
            if marks == 1:
                pattern = 1 << first
            else:
                # A finite geometric progression, evaluated with exact integers.
                pattern = (((1 << (stride * marks)) - 1) // ((1 << stride) - 1)) << first
            bits &= ~pattern
        self._bits = bits

    def _pop_index(self) -> int | None:
        if self._bits == 0:
            return None
        least_bit = self._bits & -self._bits
        self._bits ^= least_bit
        return least_bit.bit_length() - 1

    def payload_bytes(self) -> int:
        return sys.getsizeof(self._bits)


class BytearraySieveSuccessor(_SegmentedSuccessorBase):
    """Same complete sieve with C-level bytearray slices as a practical baseline."""

    engine_name = "bytearray_segmented_sieve"

    def _reset_payload(self) -> None:
        self._flags = bytearray()
        self._position = 0

    def _make_payload(self, low: int, count: int) -> None:
        flags = bytearray(b"\x01") * count
        for first, stride, marks in self._progressions(low, count):
            flags[first::stride] = bytes(marks)
        self._flags = flags
        self._position = 0

    def _pop_index(self) -> int | None:
        index = self._flags.find(b"\x01", self._position)
        if index < 0:
            return None
        self._position = index + 1
        return index

    def payload_bytes(self) -> int:
        return sys.getsizeof(self._flags)


# Convenient names for notebooks; both names explicitly preserve sieve provenance.
BitsetSuccessor = ResidueBitsetSuccessor
SegmentedSieveSuccessor = BytearraySieveSuccessor


__all__ = [
    "UINT64_MAX", "EngineStats", "SieveLimitError", "is_prime_u64",
    "is_prime_trial", "reference_primes", "MillerRabinSuccessor",
    "TrialDivisionSuccessor", "ResidueBitsetSuccessor", "BytearraySieveSuccessor",
    "BitsetSuccessor", "SegmentedSieveSuccessor",
]
