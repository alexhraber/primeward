"""Finite structure factors for prime positions and matched controls.

S(k)=|sum_j exp(-i*k*x_j)|^2/N. Coordinates use a common length unit.
Finite plots do not establish asymptotic hyperuniformity.
Reference: https://arxiv.org/html/1802.10498v1
"""
from __future__ import annotations
import math
import numpy as np
from .common import prime_labels, finite_values, linspace, result

def structure_factor(positions, wavenumbers):
    x = np.asarray(finite_values(positions, "positions"), dtype=float)
    k = np.asarray(finite_values(wavenumbers, "wavenumbers"), dtype=float)
    if len(x) == 0:
        raise ValueError("at least one scatterer is required")
    x = x - x[0]
    phases = k[:, None] * x
    if not np.isfinite(phases).all():
        raise ValueError("position times wavenumber exceeds binary64 range")
    return (np.abs(np.exp(-1j * phases).sum(axis=1))**2 / len(x)).tolist()

def matched_controls(primes, seed=1729):
    primes = prime_labels(primes)
    if not primes:
        raise ValueError("at least one prime position is required")
    lo, hi = primes[0], primes[-1]
    first_odd = lo if lo % 2 else lo + 1
    odd_count = max(0, (hi - first_odd) // 2 + 1)
    include_two = int(lo <= 2 <= hi)
    rng = np.random.default_rng(seed)
    indices = rng.choice(odd_count + include_two, size=len(primes), replace=False)
    random = sorted(2 if include_two and i == 0 else first_odd + 2 * (int(i) - include_two)
                    for i in indices)
    periodic = np.linspace(lo, hi, len(primes)).tolist()
    return {"periodic": periodic, "random_odd_lattice": random,
            "window": [lo, hi], "count": len(primes),
            "number_density": len(primes) / (hi - lo) if hi > lo else None,
            "periodic_support": "continuous equal-spacing positions within the same window",
            "random_support": "odd integer sites without replacement; 2 is eligible when in the window",
            "seed": int(seed)}

def demo(primes, *, beta=1.5, seed=1729):
    primes = prime_labels(primes)
    controls = matched_controls(primes, seed)
    k = linspace(0, math.pi, 401)
    observed = structure_factor(primes, k)
    periodic = structure_factor(controls["periodic"], k)
    ensembles = [structure_factor(matched_controls(primes, seed + n)["random_odd_lattice"], k)
                 for n in range(16)]
    mean = np.mean(ensembles, axis=0).tolist()
    stderr = (np.std(ensembles, axis=0, ddof=1) / 4).tolist()
    data = {"wavenumbers": k, "prime_structure_factor": observed,
            "periodic_structure_factor": periodic, "random_mean": mean,
            "random_standard_error": stderr, "random_realizations": 16,
            "prime_positions": primes, "controls": controls}
    error = max(abs(a - b) for a, b in zip(observed, structure_factor([p + .25 for p in primes], k)))
    return result("scattering", "finite point-scatterer structure factor",
                  {"seed": seed, "length_unit": "integer lattice spacing"}, data, {
                      "forward_normalization": {"passed": abs(observed[0] - len(primes)) < 1e-12},
                      "translation_invariance": {"passed": error < 1e-10, "max_error": error}
                  })
