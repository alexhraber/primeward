"""Thermal spectral form factor of a finite bosonic prime gas.

K(t)=|Z(beta+it)/Z(beta)|^2, with hbar=1 and E_p=E_scale*log(p).
This is a finite product over modes, with all bosonic occupations included.
A finite trace plot alone does not establish quantum chaos.
"""
from __future__ import annotations
import cmath
import math
from .common import positive, prime_labels, finite_values, thermal_mode, linspace, result

def thermal_form_factor(primes, times, beta=1.5, energy_scale=1.0):
    primes = prime_labels(primes)
    beta, scale = positive(beta, "beta"), positive(energy_scale, "energy_scale")
    times = finite_values(times, "times")
    energies = [scale * math.log(p) for p in primes]
    values, logs, amplitudes = [], [], []
    for t in times:
        terms = [thermal_mode(beta, e, t * e) for e in energies]
        log_k = math.fsum(row[0] for row in terms)
        angle = math.fsum(row[2] for row in terms)
        amplitude = cmath.rect(math.exp(0.5 * log_k), angle)
        values.append(math.exp(log_k))
        logs.append(log_k)
        amplitudes.append([amplitude.real, amplitude.imag])
    return {"primes": primes, "times": times, "beta": beta, "energy_scale": scale,
            "form_factor": values, "log_form_factor": logs,
            "normalized_amplitude": amplitudes, "units": "hbar=1",
            "model": "finite prime modes; unbounded boson occupations"}

def demo(primes, *, beta=1.5, seed=1729):
    data = thermal_form_factor(primes, linspace(0, 30, 241), beta)
    return result("form-factor", data["model"], {"beta": beta}, data, {
        "normalization": {"passed": data["form_factor"][0] == 1.0},
        "thermal_bound": {"passed": all(0 <= k <= 1 + 1e-14 for k in data["form_factor"])}
    })
