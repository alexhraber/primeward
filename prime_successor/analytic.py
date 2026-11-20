"""Certified finite Euler-product successor extraction.

This is an implementation of a known analytic family (Golomb, 1976), with a
finite-exponent rounding lemma and a reusable state. It is not a claim of a
new fast prime-generation algorithm. Initialization enumerates past primes;
the transition performs no primality tests on future candidates. High
precision and special-function evaluation are real, measured costs.

The theory and trust assumptions are in research/theory_review.md.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isqrt
from time import perf_counter

try:
    from flint import arb, ctx
except ImportError as exc:
    raise ImportError("The analytic engine needs python-flint==0.9.0.") from exc


class PrecisionLimitError(RuntimeError):
    """No answer was returned because the interval did not certify one."""


def _past_primes(limit: int) -> list[int]:
    """Seed construction only: enumerate primes at or below the input."""
    if limit < 2:
        return []
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[:2] = b"\x00\x00"
    for p in range(2, isqrt(limit) + 1):
        if sieve[p]:
            sieve[p * p : limit + 1 : p] = b"\x00" * (
                (limit - p * p) // p + 1
            )
    return [n for n in range(2, limit + 1) if sieve[n]]


@dataclass
class AnalyticStats:
    initialization_seconds: float = 0.0
    advance_seconds: float = 0.0
    seed_sieve_seconds: float = 0.0
    zeta_seconds: float = 0.0
    euler_product_seconds: float = 0.0
    extraction_seconds: float = 0.0
    transition_updates_seconds: float = 0.0
    zeta_evaluations: int = 0
    euler_factors_evaluated: int = 0
    state_rebuilds: int = 0
    precision_retries: int = 0
    successor_steps: int = 0
    future_candidate_primality_tests: int = 0
    past_primes_enumerated_at_initialization: int = 0
    maximum_precision_bits: int = 0


class AnalyticSuccessor:
    """Produce exact immediate successors, with certified numeric enclosures.

    At a fixed integer exponent s, F is zeta(s) times the Euler factors for
    all primes at or below current. F-1 has the next prime's inverse power
    as its first term. When s is at least that next prime, a proven rounding
    lemma recovers the successor by taking a reciprocal root. For current>=2
    the successor is odd, so nearest-odd decoding avoids an ill-conditioned
    ceiling near an integer. The identity start uses the same residual with
    the original ceiling rule and produces 2.

    An epoch begins with s=4*current (s=4 for the identity start). Bertrand's
    theorem justifies s>=next_prime until current exceeds s//2. Within the
    epoch, one new Euler factor updates F; at an epoch boundary it is rebuilt.

    The default limits are explicit experiment limits, not mathematical
    boundaries. Increase them only when the initialization and precision
    costs are acceptable. FLINT's global precision context makes concurrent
    use from Python threads unsupported by this wrapper; use processes.
    """

    def __init__(
        self,
        start: int = 1,
        *,
        guard_bits: int = 256,
        max_precision_bits: int = 8_000_000,
        max_seed: int = 100_000,
    ):
        began = perf_counter()
        if isinstance(start, bool) or not isinstance(start, int) or start < 1:
            raise ValueError("start must be 1 or a positive prime integer")
        for name, value in (
            ("guard_bits", guard_bits),
            ("max_precision_bits", max_precision_bits),
            ("max_seed", max_seed),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
        if guard_bits < 16:
            raise ValueError("guard_bits must be at least 16")
        if max_precision_bits < 64:
            raise ValueError("max_precision_bits must be at least 64")
        if max_seed < 1 or start > max_seed:
            raise ValueError("start exceeds the explicit max_seed limit")
        self.current = start
        self.guard_bits = int(guard_bits)
        self.max_precision_bits = int(max_precision_bits)
        self.max_seed = int(max_seed)
        self.stats = AnalyticStats()
        self.last_certificate: dict | None = None
        self.exponent = max(4, 4 * start)
        self.precision_bits = self._initial_precision(self.exponent)
        self._check_precision(self.precision_bits)
        t = perf_counter()
        self._primes = _past_primes(start)
        self.stats.seed_sieve_seconds = perf_counter() - t
        self.stats.past_primes_enumerated_at_initialization = len(self._primes)
        if start != 1 and (not self._primes or self._primes[-1] != start):
            raise ValueError("start must be 1 or a prime")
        self._rebuild()
        self.stats.initialization_seconds = perf_counter() - began

    def _initial_precision(self, exponent: int) -> int:
        # A conservative magnitude budget, not an assumed error guarantee.
        return exponent * exponent.bit_length() + self.guard_bits

    def _check_precision(self, precision: int) -> None:
        if precision > self.max_precision_bits:
            raise PrecisionLimitError(
                f"requested {precision} bits exceeds limit "
                f"{self.max_precision_bits}; no successor was returned"
            )

    def _rebuild(self) -> None:
        self._check_precision(self.precision_bits)
        with ctx.workprec(self.precision_bits):
            t = perf_counter()
            value = arb(self.exponent).zeta()
            self.stats.zeta_seconds += perf_counter() - t
            self.stats.zeta_evaluations += 1
            t = perf_counter()
            for p in self._primes:
                value *= 1 - arb(p) ** (-self.exponent)
            self.stats.euler_product_seconds += perf_counter() - t
            self.stats.euler_factors_evaluated += len(self._primes)
            self._value = value
        self.stats.state_rebuilds += 1
        self.stats.maximum_precision_bits = max(
            self.stats.maximum_precision_bits, self.precision_bits
        )

    def _try_extract(self):
        with ctx.workprec(self.precision_bits):
            residual = self._value - 1
            if not residual.is_finite() or not residual > 0:
                return None
            root = (-residual.log() / self.exponent).exp()
            if not root.is_finite():
                return None
            if self.current == 1:
                candidate = root.ceil().unique_fmpz()
                if candidate is None:
                    return None
                q = int(candidate)
                upper = q
                rounding = "ceiling (identity start)"
            else:
                half_floor = (root / 2).floor().unique_fmpz()
                if half_floor is None:
                    return None
                q = 2 * int(half_floor) + 1
                upper = q + 1
                rounding = "nearest odd integer"
            # These interval comparisons must hold for the ENTIRE enclosure.
            if not (root > q - 1 and root < upper):
                return None
            if q <= self.current or q > self.exponent:
                raise ArithmeticError("certified result violates state invariants")
            return q, root, residual, upper, rounding

    def next_prime(self) -> int:
        began = perf_counter()
        previous = self.current
        try:
            if self.current > self.exponent // 2:
                new_exponent = 4 * self.current
                new_precision = self._initial_precision(new_exponent)
                self._check_precision(new_precision)
                self.exponent = new_exponent
                self.precision_bits = new_precision
                self._rebuild()
            while True:
                t = perf_counter()
                extracted = self._try_extract()
                self.stats.extraction_seconds += perf_counter() - t
                if extracted is not None:
                    break
                new_precision = max(
                    self.precision_bits + 256, 2 * self.precision_bits
                )
                self._check_precision(new_precision)
                self.precision_bits = new_precision
                self.stats.precision_retries += 1
                self._rebuild()
            q, root, residual, upper, rounding = extracted
            with ctx.workprec(self.precision_bits):
                # Strings are explanatory summaries, not standalone proof files.
                self.last_certificate = {
                    "previous": previous,
                    "next": q,
                    "exponent": self.exponent,
                    "precision_bits": self.precision_bits,
                    "root_enclosure": root.str(24),
                    "residual_enclosure": residual.str(12),
                    "strict_lower_integer": q - 1,
                    "strict_upper_integer": upper,
                    "rounding": rounding,
                    "interval_containment_checked": True,
                    "epoch_upper_current": self.exponent // 2,
                    "past_euler_factors_before_step": len(self._primes),
                    "future_candidate_primality_tests": 0,
                    "assumptions": [
                        "complete prime prefix in state",
                        "finite-exponent extraction lemma",
                        "Bertrand's postulate (identity start handled separately)",
                        "correct FLINT/Arb enclosure implementation",
                    ],
                    "standalone_formal_certificate": False,
                }
                t = perf_counter()
                updated = self._value * (1 - arb(q) ** (-self.exponent))
                self.stats.transition_updates_seconds += perf_counter() - t
            self._value = updated
            self._primes.append(q)
            self.current = q
            self.stats.euler_factors_evaluated += 1
            self.stats.successor_steps += 1
            return q
        finally:
            self.stats.advance_seconds += perf_counter() - began

    def take(self, count: int) -> list[int]:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("count must be a nonnegative integer")
        return [self.next_prime() for _ in range(count)]

    def status(self) -> dict:
        return {
            "current": self.current,
            "exponent": self.exponent,
            "precision_bits": self.precision_bits,
            "stored_past_primes": len(self._primes),
            "stats": asdict(self.stats),
            "last_certificate": self.last_certificate,
        }
