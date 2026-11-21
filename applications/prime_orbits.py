"""Finite Gaussian-smoothed prime-orbit trace signal.

This is a deliberately truncated trace-formula analogue, not a convergent raw
Euler product on the critical line and not a certified zeta-zero computation.
Reference: Berry and Keating (1999), The Riemann Zeros and Eigenvalue Asymptotics.
"""
from __future__ import annotations
import math
from .common import prime_labels, finite_values, positive, linspace, result

def prime_orbit_signal(primes, ordinates, smoothing=0.25, max_repetitions=8):
    primes = prime_labels(primes)
    ordinates = finite_values(ordinates, "ordinates")
    smoothing = positive(smoothing, "smoothing")
    if isinstance(max_repetitions, bool) or not isinstance(max_repetitions, int) or not 1 <= max_repetitions <= 10000:
        raise ValueError("max_repetitions must be an integer in [1, 10000]")
    terms = []
    for p in primes:
        lp = math.log(p)
        for m in range(1, max_repetitions + 1):
            period = m * lp
            z = smoothing * period
            damping = 0.0 if z > 40 else math.exp(-0.5 * z * z)
            amplitude = -lp * math.exp(-0.5 * period) * damping / math.pi
            terms.append((period, amplitude))
    signal = []
    for x in ordinates:
        phases = [x * period for period, _ in terms]
        if not all(math.isfinite(v) for v in phases):
            raise ValueError("spectral ordinate times period exceeds binary64 range")
        signal.append(math.fsum(a * math.cos(theta) for (_, a), theta in zip(terms, phases)))
    return {"primes": primes, "ordinates": ordinates, "signal": signal,
            "smoothing": smoothing, "max_repetitions": max_repetitions,
            "term_count": len(terms), "prime_cutoff": max(primes, default=None),
            "spectral_variable": "dimensionless ordinate; not physical time",
            "formula": "-sum(log(p)*p^(-m/2)*exp(-(sigma*m*log(p))^2/2)*cos(x*m*log(p)))/pi"}

def demo(primes, *, beta=1.5, seed=1729):
    data = prime_orbit_signal(primes, linspace(-30, 30, 241))
    error = max(abs(a - b) for a, b in zip(data["signal"], reversed(data["signal"])))
    return result("prime-orbits", "finite smoothed prime trace analogue",
                  {"smoothing": 0.25, "max_repetitions": 8}, data,
                  {"even_signal": {"passed": error < 1e-12, "max_error": error}})
