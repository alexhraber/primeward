"""Finite Gaussian Poisson trace experiment on a logarithmic orbit.

This is the textbook Poisson identity for R_+ / gamma^Z, in the form
discussed in Masullo, The Music of the Primes, introduction pp. 17-19,
40-41. Gamma need not be prime. This is not a primality test or a result
conditional on a proposed proof of GRH.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

def compare_orbit(gamma: float = 101, width: float = 0.02,
                  center: float | None = None, tolerance: float = 1e-10,
                  max_modes: int = 200_000) -> dict:
    if not math.isfinite(gamma) or gamma <= 1:
        raise ValueError("gamma must be finite and greater than 1")
    if not math.isfinite(width) or width <= 0:
        raise ValueError("width must be finite and positive")
    if not math.isfinite(tolerance) or not 0 < tolerance < 0.1:
        raise ValueError("tolerance must be between 0 and 0.1")
    if not 1 <= max_modes <= 200_000:
        raise ValueError("max_modes outside budget")
    L = math.log(gamma)
    mu = math.log(gamma) if center is None else center
    if not math.isfinite(mu):
        raise ValueError("center must be finite")
    # Fourier modes of the circle of circumference log(gamma).
    alpha = (2 * math.pi * width / L)**2 / 2
    prefactor = math.sqrt(2 * math.pi) * width / L
    # The positive-mode tail after M is bounded by the integral from M
    # to infinity of exp(-alpha*x*x). This uses only positivity and
    # monotonicity; it does not bound floating-point rounding error.
    def tail_bound(M: int) -> float:
        return (prefactor * math.sqrt(math.pi / alpha)
                * math.erfc(math.sqrt(alpha) * M))
    M = 1
    while M < max_modes and tail_bound(M) > tolerance / 4:
        M += 1
    if tail_bound(M) > tolerance / 4:
        raise ValueError("mode budget cannot meet the requested truncation tolerance")
    spectrum = prefactor * (1 + 2 * sum(
        math.exp(-alpha * m * m) * math.cos(2 * math.pi * m * mu / L)
        for m in range(1, M + 1)
    ))
    # Sum the orbit with terms beyond the cutoff far below tolerance.
    center_index = mu / L
    radius = max(4, math.ceil(
        (abs(width / L) * math.sqrt(2 * math.log(32 / tolerance))) + 2
    ))
    nearest = round(center_index)
    orbital = sum(
        math.exp(-0.5 * (((nearest + j) * L - mu) / width)**2)
        for j in range(-radius, radius + 1)
    )
    return {
        "schema_version": "primeward.orbital_trace.v1",
        "gamma": gamma, "logarithmic_width": width, "center": mu,
        "positive_modes": M, "orbit_terms": 2 * radius + 1,
        "orbital_sum": orbital, "fourier_sum": spectrum,
        "difference": abs(orbital - spectrum),
        "spectral_truncation_bound": tail_bound(M),
        "note": (
            "Finite Gaussian/Poisson toy model; gamma can be composite. "
            "Spectral truncation bound excludes floating-point roundoff. "
            "Does not find primes or imply the Riemann Hypothesis."
        ),
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gamma", type=float, default=101)
    parser.add_argument("--width", type=float, default=0.02)
    parser.add_argument("--center", type=float)
    parser.add_argument("--tolerance", type=float, default=1e-10)
    parser.add_argument("--max-modes", type=int, default=200_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    result = compare_orbit(
        args.gamma, args.width, args.center, args.tolerance, args.max_modes
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(payload, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
