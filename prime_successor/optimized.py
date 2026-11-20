"""Precision-aware evaluation of the same certified analytic successor rule.

This changes how much relative precision is spent on tiny Euler corrections.
The mathematical successor rule, initialization, epoch transitions, and Arb
acceptance conditions remain the same.  No rounded float is used as evidence.

A correction associated with prime p has magnitude at most approximately
p**(-s).  It needs fewer relative bits than the near-one accumulated state to
achieve comparable absolute accuracy.  We compute that correction at reduced
precision, then subtract its complete Arb enclosure at full state precision.
Arb's enclosing interval, rather than a heuristic error estimate, remains the
authority.  An inconclusive interval follows the parent's rebuild/retry path.

The parent still performs individual transition updates at full precision.
This variant targets initialization/rebuild costs and decoding first; those
costs dominated the measured original prototype.  This is a performance
engineering experiment on a known analytic construction, not a faster-than-
sieving claim or a new prime theorem.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter

from flint import arb, ctx

from .analytic import AnalyticSuccessor


@dataclass
class PrecisionWork:
    """Precision budgets are descriptive counters, not a CPU complexity model."""

    reduced_precision_factors: int = 0
    factor_precision_bits_sum: int = 0
    full_precision_factor_bits_sum: int = 0
    minimum_factor_precision_bits: int = 0
    maximum_factor_precision_bits: int = 0
    decoding_attempts: int = 0
    decoding_precision_bits_sum: int = 0
    full_decoding_precision_bits_sum: int = 0


class PrecisionAwareSuccessor(AnalyticSuccessor):
    """AnalyticSuccessor with rigorous mixed-precision rebuilding and decoding.

    The constructor and all public successor APIs are inherited unchanged.
    The arithmetic history, state exponent, resource limits, and initialization
    cost have exactly the same meaning as in AnalyticSuccessor.
    """

    def __init__(self, *args, **kwargs):
        # The parent constructor invokes our overridden _rebuild.
        self.precision_work = PrecisionWork()
        super().__init__(*args, **kwargs)

    def _factor_precision(self, p: int) -> int:
        # floor(log2(p)) is exact via bit_length; no floating logarithm enters
        # the precision budget.  Since p >= 2**floor(log2(p)), this conservative
        # magnitude estimate never understates the inverse-power magnitude.
        return min(
            self.precision_bits,
            max(64, self.precision_bits - self.exponent * (p.bit_length() - 1) + 32),
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
            local_bits = self._factor_precision(p)
            with ctx.workprec(local_bits):
                correction = value * (arb(p) ** (-self.exponent))
            with ctx.workprec(self.precision_bits):
                value = value - correction

            work = self.precision_work
            work.reduced_precision_factors += int(local_bits < self.precision_bits)
            work.factor_precision_bits_sum += local_bits
            work.full_precision_factor_bits_sum += self.precision_bits
            if work.minimum_factor_precision_bits == 0:
                work.minimum_factor_precision_bits = local_bits
            else:
                work.minimum_factor_precision_bits = min(work.minimum_factor_precision_bits, local_bits)
            work.maximum_factor_precision_bits = max(work.maximum_factor_precision_bits, local_bits)

        self.stats.euler_product_seconds += perf_counter() - t
        self.stats.euler_factors_evaluated += len(self._primes)
        self._value = value
        self.stats.state_rebuilds += 1
        self.stats.maximum_precision_bits = max(
            self.stats.maximum_precision_bits, self.precision_bits
        )

    def _try_extract(self):
        # Decoding distinguishes neighboring integers; it does not need the
        # full relative precision used to resolve the tiny residual near one.
        # Arb subtraction retains a rigorous enclosure even with cancellation.
        decode_bits = min(self.precision_bits, max(64, 128 + self.current.bit_length()))
        work = self.precision_work
        work.decoding_attempts += 1
        work.decoding_precision_bits_sum += decode_bits
        work.full_decoding_precision_bits_sum += self.precision_bits

        with ctx.workprec(decode_bits):
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
            if not (root > q - 1 and root < upper):
                return None
            if q <= self.current or q > self.exponent:
                raise ArithmeticError("certified result violates state invariants")
            return q, root, residual, upper, rounding

    def status(self) -> dict:
        result = super().status()
        result["precision_work"] = asdict(self.precision_work)
        result["variant"] = "precision-aware Euler corrections and decoding"
        result["transition_update_precision"] = "full state precision (inherited)"
        return result


OptimizedAnalyticSuccessor = PrecisionAwareSuccessor


__all__ = ["PrecisionAwareSuccessor", "OptimizedAnalyticSuccessor", "PrecisionWork"]


def run_benchmarks(output_path: str, repeats: int = 3) -> dict:
    """Reproduce the four measured comparison cases, including initialization."""
    import hashlib
    import json
    from pathlib import Path
    import platform
    import statistics
    import flint
    from .engine import BytearraySieveSuccessor, MillerRabinSuccessor

    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("repeats must be a positive integer")
    methods = (AnalyticSuccessor, PrecisionAwareSuccessor, BytearraySieveSuccessor)
    source_dir = Path(__file__).resolve().parent
    result = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "python_flint": flint.__version__,
        "repeats": repeats,
        "timing_scope": "Initialization plus advancing, with independent verification excluded. "
                        "Method order rotates each repetition. FLINT process caches are retained. "
                        "Bytearray baseline is our Python implementation, not an optimized native library.",
        "source_sha256": {
            filename: hashlib.sha256((source_dir / filename).read_bytes()).hexdigest()
            for filename in ("analytic.py", "optimized.py", "engine.py")
        },
        "cases": [],
        "comparisons": [],
    }
    for start, count in ((1, 200), (113, 100), (997, 30), (10007, 10)):
        expected = MillerRabinSuccessor(start).take(count)
        measurements = {cls.__name__: [] for cls in methods}
        for repeat in range(repeats):
            offset = repeat % len(methods)
            for cls in methods[offset:] + methods[:offset]:
                t = perf_counter()
                engine = cls(start)
                setup = perf_counter() - t
                t = perf_counter()
                outputs = engine.take(count)
                advancing = perf_counter() - t
                if outputs != expected:
                    raise AssertionError(f"Successor mismatch for {cls.__name__} at {start}")
                run = {
                    "setup_seconds": setup,
                    "advance_seconds": advancing,
                    "total_seconds": setup + advancing,
                    "stats": asdict(engine.stats),
                }
                if hasattr(engine, "precision_work"):
                    run["precision_work"] = asdict(engine.precision_work)
                measurements[cls.__name__].append(run)
        totals = {}
        for cls in methods:
            runs = measurements[cls.__name__]
            median_total = statistics.median(run["total_seconds"] for run in runs)
            totals[cls.__name__] = median_total
            result["cases"].append({
                "method": cls.__name__,
                "start": start,
                "count": count,
                "first": expected[0],
                "last": expected[-1],
                "outputs": expected,
                "outputs_sha256": hashlib.sha256(
                    json.dumps(expected, separators=(",", ":")).encode()
                ).hexdigest(),
                "median_setup_seconds": statistics.median(run["setup_seconds"] for run in runs),
                "median_advance_seconds": statistics.median(run["advance_seconds"] for run in runs),
                "median_total_seconds": median_total,
                "runs": runs,
                "matches_independent_candidate_scan": True,
            })
        comparison = {
            "start": start,
            "count": count,
            "original_seconds": totals["AnalyticSuccessor"],
            "precision_aware_seconds": totals["PrecisionAwareSuccessor"],
            "bytearray_seconds": totals["BytearraySieveSuccessor"],
            "original_over_precision_aware": totals["AnalyticSuccessor"] / totals["PrecisionAwareSuccessor"],
            "precision_aware_over_bytearray": totals["PrecisionAwareSuccessor"] / totals["BytearraySieveSuccessor"],
        }
        result["comparisons"].append(comparison)
        print(json.dumps(comparison), flush=True)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", required=True, help="Output JSON path")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    run_benchmarks(args.benchmark, args.repeats)
