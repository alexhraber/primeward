"""Finite paired-charge primon gas with arbitrary imaginary chemical phases.

Each mode contributes [1-2*cos(theta)*p^-s+p^-2s]^-1. General phases are not an
automorphic L-function. The occupation expansion can have signed coefficients.
Reference: https://arxiv.org/html/2502.02661v2 section 6.1.
"""
from __future__ import annotations
import math
from .common import positive, prime_labels, finite_values, thermal_mode, exp_or_none, result

def occupation_coefficients(phase, order=8):
    if not math.isfinite(float(phase)) or isinstance(order, bool) or not isinstance(order, int) or order < 0:
        raise ValueError("a finite phase and nonnegative integer order are required")
    c = [1.0]
    if order:
        a = 2 * math.cos(phase)
        c.append(a)
        for _ in range(2, order + 1):
            c.append(a * c[-1] - c[-2])
    return c

def twisted_partition(primes, phases, beta=1.5, energy_scale=1.0):
    primes = prime_labels(primes)
    phases = finite_values(phases, "phases")
    if len(primes) != len(phases):
        raise ValueError("provide one phase per prime mode")
    beta, scale = positive(beta, "beta"), positive(energy_scale, "energy_scale")
    energies = [scale * math.log(p) for p in primes]
    terms = [thermal_mode(beta, energy, theta)
             for energy, theta in zip(energies, phases)]
    log_z = -2 * math.fsum(t[1] for t in terms)
    neutral = -2 * math.fsum(thermal_mode(beta, energy, 0.0)[1] for energy in energies)
    log_ratio = math.fsum(t[0] for t in terms)
    z, z0 = exp_or_none(log_z), exp_or_none(neutral)
    return {"primes": primes, "phases": phases, "beta": beta, "energy_scale": scale,
            "log_partition": log_z, "partition": z, "partition_representable": z is not None and z > 0,
            "partition_underflow": z == 0.0, "partition_overflow": z is None,
            "log_untwisted_partition": neutral, "untwisted_partition": z0,
            "normalized_twist_ratio": math.exp(log_ratio), "log_twist_ratio": log_ratio,
            "coefficient_warning": "occupation coefficients need not be positive"}

def demo(primes, *, beta=1.5, seed=1729):
    from .form_factor import thermal_form_factor
    time = 2.5
    data = twisted_partition(primes, [time * math.log(p) for p in primes], beta)
    expected = thermal_form_factor(primes, [time], beta)["form_factor"][0]
    coefficients = occupation_coefficients(math.pi, 8)
    data["pi_phase_coefficients"] = coefficients
    error = abs(data["normalized_twist_ratio"] - expected)
    return result("twisted-gas", "finite paired charged oscillators", {"beta": beta, "time_phase": time},
                  data, {
                      "form_factor_identity": {"passed": error < 1e-13, "absolute_error": error},
                      "signed_coefficients": {"passed": coefficients[1] < 0}
                  })
