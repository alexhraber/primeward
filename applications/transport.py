"""Coherent 1D transport through real delta-function potentials.

-psi'' + sum_j g_j delta(x-x_j) psi = k^2 psi, in hbar^2/(2m)=1 units.
Scattering amplitudes are composed without large transfer-matrix products.
"""
from __future__ import annotations
import cmath
import math
from numbers import Real
from .common import positive, finite_values, prime_labels, linspace, result

def scattering_amplitudes(positions, wavenumber, strengths=1.0):
    x = finite_values(positions, "positions")
    k = positive(wavenumber, "wavenumber")
    if any(b <= a for a, b in zip(x, x[1:])):
        raise ValueError("positions must be strictly increasing")
    g = ([float(strengths)] * len(x) if isinstance(strengths, Real)
         else finite_values(strengths, "strengths"))
    if len(g) != len(x) or not all(math.isfinite(a) for a in g):
        raise ValueError("provide one finite real strength per position, or a scalar")
    t, left, right, log_t = 1 + 0j, 0j, 0j, 0.0
    previous = x[0] if x else 0.0
    for position, strength in zip(x, g):
        eta = strength / (2 * k)
        if not math.isfinite(eta):
            raise ArithmeticError("delta strength/wavenumber exceeds binary64 range")
        single_t = 1 / complex(1, eta)
        single_r = single_t - 1
        phase = k * (position - previous)
        if not math.isfinite(phase):
            raise ArithmeticError("propagation phase exceeds binary64 range")
        z = cmath.exp(1j * phase)
        z2 = z * z
        denominator = 1 - right * single_r * z2
        if denominator == 0:
            raise ArithmeticError("unresolved resonance denominator in binary64")
        old_t, old_right = t, right
        t = old_t * single_t * z / denominator
        left = left + old_t**2 * single_r * z2 / denominator
        right = single_r + single_t**2 * old_right * z2 / denominator
        log_t += -2 * math.log(math.hypot(1, eta)) - 2 * math.log(abs(denominator))
        previous = position
    return {"t": t, "r_left": left, "r_right": right, "log_transmission": log_t}

def transport(positions, wavenumbers, strengths=1.0):
    positions = finite_values(positions, "positions")
    if not isinstance(strengths, Real):
        strengths = finite_values(strengths, "strengths")
    ks = finite_values(wavenumbers, "wavenumbers")
    rows = [scattering_amplitudes(positions, k, strengths) for k in ks]
    ts = [abs(row["t"])**2 for row in rows]
    rs = [abs(row["r_left"])**2 for row in rows]
    r_right = [abs(row["r_right"])**2 for row in rows]
    flux = [t + r - 1 for t, r in zip(ts, rs)]
    return {"wavenumbers": ks, "transmission": ts, "reflection": rs,
            "reflection_right": r_right, "log_transmission": [r["log_transmission"] for r in rows],
            "flux_residual": flux, "max_flux_error": max(map(abs, flux), default=0.0),
            "positions": list(positions), "units": "hbar^2/(2m)=1",
            "amplitude_reference": "end faces of the scatterer chain"}

def demo(primes, *, beta=1.5, seed=1729):
    from .scattering import matched_controls
    primes = prime_labels(primes)[:16]
    if not primes:
        raise ValueError("at least one prime position is required")
    controls = matched_controls(primes, seed)
    ks = linspace(.15, 3.5, 241)
    strength = 1.0
    data = {name: transport(positions, ks, strength) for name, positions in
            [("prime", primes), ("periodic", controls["periodic"]),
             ("random_odd_lattice", controls["random_odd_lattice"])]}
    flux = max(d["max_flux_error"] for d in data.values())
    return result("transport", "lossless one-dimensional delta-scatterer chains",
                  {"strength": strength, "seed": seed, "units": "hbar^2/(2m)=1"}, data, {
                      "flux_conservation": {"passed": flux < 1e-9, "max_error": flux},
                      "finite_log_transmission": {
                          "passed": all(math.isfinite(x) for d in data.values() for x in d["log_transmission"])}
                  })
