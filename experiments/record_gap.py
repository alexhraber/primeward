"""Bounded modular screening above 2**exponent - 1.

This experiment does not depend on the Riemann hypothesis or the analytic
successor engine. A survivor is not called prime without a complete
small-factor certificate, which is unavailable at the record scale.
"""
from __future__ import annotations

import argparse
from array import array
import json
import math
from pathlib import Path
from time import perf_counter

RECORD_EXPONENT = 136_279_841
MAX_EXPONENT = 150_000_000
MAX_SPAN = 200_000
MAX_TRIAL_LIMIT = 2_000_000
MAX_PREVIEW = 64


def primes_through(limit: int) -> list[int]:
    if not 2 <= limit <= MAX_TRIAL_LIMIT:
        raise ValueError(f"factor limit must be in [2, {MAX_TRIAL_LIMIT}]")
    flags = bytearray(b"\x01") * (limit + 1)
    flags[0:2] = b"\x00\x00"
    for factor in range(2, math.isqrt(limit) + 1):
        if flags[factor]:
            start = factor * factor
            flags[start::factor] = b"\x00" * (((limit - start) // factor) + 1)
    return [n for n in range(2, limit + 1) if flags[n]]


def screen(exponent: int, span: int = 10_000,
           trial_limit: int = 250_000, preview: int = 12) -> dict:
    if type(exponent) is not int or not 2 <= exponent <= MAX_EXPONENT:
        raise ValueError(f"exponent must be in [2, {MAX_EXPONENT}]")
    if type(span) is not int or not 1 <= span <= MAX_SPAN:
        raise ValueError(f"span must be in [1, {MAX_SPAN}]")
    if type(trial_limit) is not int or not 3 <= trial_limit <= MAX_TRIAL_LIMIT:
        raise ValueError(f"trial limit must be in [3, {MAX_TRIAL_LIMIT}]")
    if type(preview) is not int or not 1 <= preview <= MAX_PREVIEW:
        raise ValueError(f"preview must be in [1, {MAX_PREVIEW}]")

    started = perf_counter()
    # Candidate k is 2**exponent - 1 + 2*k, for k in 1..span.
    # Mark one divisor per candidate. Zero means no divisor yet found.
    witness = array("I", [0]) * span
    small_base = (1 << exponent) - 1 if exponent <= 64 else None
    factor_primes = primes_through(trial_limit)
    for divisor in factor_primes:
        if divisor == 2:
            continue  # all candidates are odd
        # 2*k == 1 - 2**exponent (mod divisor).
        inverse_two = (divisor + 1) // 2
        residue = ((1 - pow(2, exponent, divisor)) * inverse_two) % divisor
        first = residue if residue else divisor
        for k in range(first, span + 1, divisor):
            i = k - 1
            if witness[i]:
                continue
            # A prime equals its own divisor; such a candidate is not composite.
            if small_base is not None and small_base + 2 * k == divisor:
                continue
            witness[i] = divisor

    rejected = sum(bool(w) for w in witness)
    first_unexcluded = next((i + 1 for i, d in enumerate(witness) if not d), None)
    unexcluded_samples = [i + 1 for i, d in enumerate(witness) if not d][:preview]
    rejected_samples = [
        {"offset_k": i + 1, "divisor": d}
        for i, d in enumerate(witness) if d
    ][:preview]
    # Every excluded candidate has a valid small factor; the first survivor
    # is prime only if the tested factors reach its square root.
    certified = False
    successor = None
    if first_unexcluded is not None and small_base is not None:
        candidate = small_base + 2 * first_unexcluded
        certified = math.isqrt(candidate) <= trial_limit
        if certified:
            successor = candidate

    # For an odd starting value > 2, all unexamined even numbers are composite.
    # This is a lower bound on the distance to the immediate next prime, not
    # an assertion that an unexcluded candidate is prime.
    lower_k = first_unexcluded if first_unexcluded is not None else span + 1
    if certified:
        status = "certified_successor"
    elif first_unexcluded is None:
        status = "all_screened_candidates_composite"
    else:
        status = "partial_screen"
    return {
        "schema_version": "primeward.mersenne_gap.v1",
        "status": status,
        "start": f"2^{exponent}-1",
        "exponent": exponent,
        "span": span,
        "trial_limit": trial_limit,
        "factor_primes_used": len(factor_primes),
        "candidates_proven_composite": rejected,
        "candidates_not_excluded": span - rejected,
        "first_unexcluded_offset_k": first_unexcluded,
        "first_unexcluded_candidate": (
            f"2^{exponent}-1+{2 * first_unexcluded}"
            if first_unexcluded is not None else None
        ),
        "unexcluded_offset_samples": unexcluded_samples,
        "composite_witness_samples": rejected_samples,
        "lower_bound_distance_to_next_prime": 2 * lower_k,
        "successor_certified": certified,
        "successor": successor,
        "notes": (
            "A nonexcluded candidate has no factor up to trial_limit; it is not "
            "a proven prime. Only a full square-root trial bound certifies it. "
            "This method does not certify a successor at the record scale."
        ),
        "elapsed_seconds": round(perf_counter() - started, 6),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exponent", type=int, default=RECORD_EXPONENT)
    parser.add_argument("--span", type=int, default=10_000)
    parser.add_argument("--trial-limit", type=int, default=250_000)
    parser.add_argument("--preview", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    result = screen(args.exponent, args.span, args.trial_limit, args.preview)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
