"""Exact analytic successors with a residual state and a smaller exponent.

The stored value is R = zeta(s) * product(1 - p**(-s)) - 1, over the
complete prime prefix.  Its least surviving term is q**(-s), where q is the
unknown next prime.  The transition performs no future candidate tests.

After the identity start, all surviving integers are odd.  A midpoint
integral bound on their tail proves q-1 < R**(-1/s) < q whenever
s >= (q+3)/2.  This improves the original sufficient condition s >= q.
The unknown q is bounded without testing candidates: with L=2*s-1, an
enclosed R greater than

    T(L) = L**(-s) + (L+1)**(1-s) / (2*(s-1))

rules out q >= L.  Thus q <= 2*s-3, and nearest-odd decoding is justified.
If this check is inconclusive, the engine rebuilds with a larger exponent
or more precision.  It never treats an approximate root as evidence.

Initialization still constructs the complete past prime prefix and an
expensive high-precision Euler product.  Once that work is done, storing
R directly avoids repeatedly representing a tiny residual beside 1.  A
step uses R' = R - q**(-s) - R*q**(-s), at much lower relative precision.
Even exponents use FLINT's specialized zeta implementation.  Diagnostic
decimal strings are formatted only when requested.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter

from flint import arb, ctx

from .analytic import AnalyticStats, AnalyticSuccessor, _past_primes


@dataclass
class ResidualPrecisionWork:
    reduced_precision_factors: int = 0
    factor_precision_bits_sum: int = 0
    full_precision_factor_bits_sum: int = 0
    decoding_attempts: int = 0
    decoding_precision_bits_sum: int = 0
    full_decoding_precision_bits_sum: int = 0
    transition_precision_bits_sum: int = 0
    full_transition_precision_bits_sum: int = 0
    minimum_transition_precision_bits: int = 0
    maximum_transition_precision_bits: int = 0
    maximum_residual_precision_bits: int = 0
    epoch_bound_checks: int = 0
    epoch_bound_rebuilds: int = 0
    factor_precision_logarithms: int = 0


class FastAnalyticSuccessor(AnalyticSuccessor):
    """A residual-state implementation of the exact Euler-product method.

    ``precision_bits`` is the full precision budget for initialization and
    rebuilding. ``residual_precision_bits`` is the much smaller precision
    used to retain and update the residual. Both are reported in status.
    The resource limits and identity-start semantics match AnalyticSuccessor.
    FLINT's precision context is process-global; use processes, not threads.
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
        self.guard_bits = guard_bits
        self.max_precision_bits = max_precision_bits
        self.max_seed = max_seed
        self.stats = AnalyticStats()
        self.precision_work = ResidualPrecisionWork()
        self._certificate_data = None
        self._certificate_cache = None
        self.exponent = self._choose_exponent(start)
        self.precision_bits = self._initial_precision(self.exponent)
        self._check_precision(self.precision_bits)
        self._precision_extra_bits = 0

        t = perf_counter()
        self._primes = _past_primes(start)
        self.stats.seed_sieve_seconds = perf_counter() - t
        self.stats.past_primes_enumerated_at_initialization = len(self._primes)
        if start != 1 and (not self._primes or self._primes[-1] != start):
            raise ValueError("start must be 1 or a prime")
        self._rebuild()
        self.stats.initialization_seconds = perf_counter() - began

    @staticmethod
    def _choose_exponent(current: int) -> int:
        # Round upward: FLINT has a specialized algorithm for even zeta values.
        return max(4, 2 * ((current + 3) // 2))

    def _initial_precision(self, exponent: int) -> int:
        # The gate below bounds q by 2*s-3, rather than the original q<=s.
        successor_cap = 2 * exponent - 3
        # Refuse huge custom seed requests before evaluating their logarithm.
        lower_budget = exponent * (successor_cap.bit_length() - 1) + self.guard_bits
        self._check_precision(lower_budget)
        # Use an enclosing logarithm rather than spending up to s extra bits
        # by rounding log2(q) to an integer before multiplying by s.
        with ctx.workprec(96):
            bits = exponent * arb(successor_cap).log() / arb(2).log()
            upper_bits = bits.upper().ceil().unique_fmpz()
        if upper_bits is None:
            return exponent * successor_cap.bit_length() + self.guard_bits
        return int(upper_bits) + self.guard_bits

    def _rebuild(self) -> None:
        self._check_precision(self.precision_bits)
        self.epoch_successor_limit = 2 * self.exponent - 3
        self.residual_precision_bits = min(
            self.precision_bits,
            self.exponent + self.guard_bits + 32 + self._precision_extra_bits,
        )
        with ctx.workprec(self.precision_bits):
            t = perf_counter()
            value = arb(self.exponent).zeta()
            self.stats.zeta_seconds += perf_counter() - t
            self.stats.zeta_evaluations += 1

        t = perf_counter()
        with ctx.workprec(96):
            inverse_log_two = 1 / arb(2).log()
        for p in self._primes:
            with ctx.workprec(96):
                magnitude = self.exponent * arb(p).log() * inverse_log_two
                magnitude_floor = int(magnitude.lower().floor().unique_fmpz())
            local_bits = min(
                self.precision_bits,
                max(64, self.precision_bits - magnitude_floor + 32),
            )
            with ctx.workprec(local_bits):
                rounded_value = +value
                correction = rounded_value * arb(p) ** (-self.exponent)
            with ctx.workprec(self.precision_bits):
                value = value - correction
            work = self.precision_work
            work.reduced_precision_factors += int(local_bits < self.precision_bits)
            work.factor_precision_bits_sum += local_bits
            work.full_precision_factor_bits_sum += self.precision_bits
            work.factor_precision_logarithms += 1

        # Do the subtraction before rounding the result. Rounding F to the
        # residual precision first would destroy the tiny information in F-1.
        with ctx.workprec(self.residual_precision_bits):
            self._residual = value - 1
        self.stats.euler_product_seconds += perf_counter() - t
        self.stats.euler_factors_evaluated += len(self._primes)

        with ctx.workprec(96):
            first_excluded = 2 * self.exponent - 1
            self._tail_bound = (
                arb(first_excluded) ** (-self.exponent)
                + arb(first_excluded + 1) ** (1 - self.exponent)
                / (2 * (self.exponent - 1))
            )
        self.stats.state_rebuilds += 1
        self.stats.maximum_precision_bits = max(
            self.stats.maximum_precision_bits, self.precision_bits
        )
        self.precision_work.maximum_residual_precision_bits = max(
            self.precision_work.maximum_residual_precision_bits,
            self.residual_precision_bits,
        )

    def _try_extract(self):
        decode_bits = min(self.precision_bits, max(64, 64 + self.current.bit_length()))
        work = self.precision_work
        work.decoding_attempts += 1
        work.decoding_precision_bits_sum += decode_bits
        work.full_decoding_precision_bits_sum += self.precision_bits
        with ctx.workprec(decode_bits):
            residual = +self._residual
            if not residual.is_finite() or not residual > 0:
                return None
            if self.current != 1:
                work.epoch_bound_checks += 1
                if not residual > self._tail_bound:
                    return None
            root = 1 / residual.root(self.exponent)
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
            if not (root > q - 1 and root < upper):
                return None
            if q <= self.current or q > self.epoch_successor_limit:
                raise ArithmeticError("certified result violates state invariants")
            return q, root, residual, upper, rounding

    def _retry(self) -> None:
        new_exponent = self._choose_exponent(self.current)
        # When the certified successor range is exhausted, rebuild the epoch.
        # A wide interval earlier in the epoch instead receives more precision.
        if new_exponent > self.exponent and not self._residual > self._tail_bound:
            new_precision = self._initial_precision(new_exponent)
            self._check_precision(new_precision)
            self.exponent = new_exponent
            self.precision_bits = new_precision
            self._precision_extra_bits = 0
            self.precision_work.epoch_bound_rebuilds += 1
        else:
            new_precision = max(self.precision_bits + 256, 2 * self.precision_bits)
            self._check_precision(new_precision)
            self._precision_extra_bits += new_precision - self.precision_bits
            self.precision_bits = new_precision
            self.stats.precision_retries += 1
        self._rebuild()

    def next_prime(self) -> int:
        began = perf_counter()
        previous = self.current
        try:
            while True:
                t = perf_counter()
                extracted = self._try_extract()
                self.stats.extraction_seconds += perf_counter() - t
                if extracted is not None:
                    break
                self._retry()
            q, root, residual, upper, rounding = extracted
            t = perf_counter()
            transition_bits = min(
                self.residual_precision_bits,
                max(64, self._residual.rel_accuracy_bits() + 32),
            )
            with ctx.workprec(transition_bits):
                inverse_power = arb(q) ** (-self.exponent)
                updated = self._residual - inverse_power - self._residual * inverse_power
            self.stats.transition_updates_seconds += perf_counter() - t
            work = self.precision_work
            work.transition_precision_bits_sum += transition_bits
            self.precision_work.full_transition_precision_bits_sum += self.precision_bits
            if work.minimum_transition_precision_bits == 0:
                work.minimum_transition_precision_bits = transition_bits
            else:
                work.minimum_transition_precision_bits = min(
                    work.minimum_transition_precision_bits, transition_bits
                )
            work.maximum_transition_precision_bits = max(
                work.maximum_transition_precision_bits, transition_bits
            )
            self._certificate_data = {
                "previous": previous,
                "next": q,
                "exponent": self.exponent,
                "precision_bits": self.precision_bits,
                "residual_precision_bits": self.residual_precision_bits,
                "transition_precision_bits": transition_bits,
                "root": root,
                "residual": residual,
                "tail_bound": self._tail_bound,
                "strict_lower_integer": q - 1,
                "strict_upper_integer": upper,
                "rounding": rounding,
                "epoch_successor_limit": self.epoch_successor_limit,
                "past_euler_factors_before_step": len(self._primes),
            }
            self._certificate_cache = None
            self._residual = updated
            self._primes.append(q)
            self.current = q
            self.stats.euler_factors_evaluated += 1
            self.stats.successor_steps += 1
            return q
        finally:
            self.stats.advance_seconds += perf_counter() - began

    @property
    def last_certificate(self):
        if self._certificate_data is None:
            return None
        if self._certificate_cache is None:
            data = self._certificate_data
            self._certificate_cache = {
                key: value
                for key, value in data.items()
                if key not in ("root", "residual", "tail_bound")
            }
            self._certificate_cache.update({
                "root_enclosure": data["root"].str(24),
                "residual_enclosure": data["residual"].str(12),
                "epoch_tail_bound_enclosure": data["tail_bound"].str(12),
                "interval_containment_checked": True,
                "epoch_bound_checked": data["previous"] != 1,
                "future_candidate_primality_tests": 0,
                "assumptions": [
                    "complete prime prefix in state",
                    "odd-lattice finite-exponent extraction lemma (identity handled separately)",
                    "certified residual tail bound for unknown successor",
                    "correct FLINT/Arb enclosure implementation",
                ],
                "standalone_formal_certificate": False,
            })
        return self._certificate_cache

    def status(self) -> dict:
        result = super().status()
        result["residual_precision_bits"] = self.residual_precision_bits
        result["epoch_successor_limit"] = self.epoch_successor_limit
        result["precision_work"] = asdict(self.precision_work)
        result["variant"] = "residual state with certified odd-tail exponent bound"
        result["diagnostics"] = "decimal enclosure strings are formatted on access"
        return result


ResidualAnalyticSuccessor = FastAnalyticSuccessor

__all__ = ["FastAnalyticSuccessor", "ResidualAnalyticSuccessor", "ResidualPrecisionWork"]
