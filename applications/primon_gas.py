"""Finite bosonic/fermionic prime gases and exact prime-mode extraction.

H = sum_p E_scale*log(p)*n_p. Bosons have occupations 0,1,...; fermions 0,1.
Finite products need beta>0. Infinite zeta comparisons require beta*E_scale>1.
Reference: https://arxiv.org/html/1401.8190v3
"""
from __future__ import annotations
import math
from .common import positive, prime_labels, result

def thermodynamics(primes, beta=1.5, energy_scale=1.0, statistics="boson"):
    primes = prime_labels(primes)
    beta, scale = positive(beta, "beta"), positive(energy_scale, "energy_scale")
    if statistics not in ("boson", "fermion"):
        raise ValueError("statistics must be boson or fermion")
    logs, energies, variances, capacities = [], [], [], []
    for p in primes:
        energy = scale * math.log(p)
        b = beta * energy
        if not math.isfinite(b) or b <= 0:
            raise ValueError("beta*mode energy is outside binary64 range")
        r = math.exp(-b)
        denominator = -math.expm1(-b) if statistics == "boson" else 1 + r
        log_boson = (-math.log1p(-r) if b >= math.log(2) else -math.log(denominator)) if statistics == "boson" else None
        logs.append(log_boson if statistics == "boson" else math.log1p(r))
        energies.append(energy * r / denominator)
        variances.append((energy / denominator)**2 * r if r else 0.0)
        capacities.append((b / denominator)**2 * r if r else 0.0)
    log_z, mean = math.fsum(logs), math.fsum(energies)
    variance, capacity = math.fsum(variances), math.fsum(capacities)
    entropy = log_z + beta * mean
    if not all(math.isfinite(v) for v in (log_z, mean, variance, capacity, entropy)):
        raise ArithmeticError("thermodynamic moments exceed binary64 range")
    return {"primes": primes, "beta": beta, "energy_scale": scale,
            "statistics": statistics, "mode_count": len(primes),
            "log_partition": log_z, "mean_energy": mean, "energy_variance": variance,
            "heat_capacity_over_kB": capacity, "entropy_over_kB": entropy,
            "occupations": "unbounded" if statistics == "boson" else "0 or 1",
            "precision": "binary64", "prime_cutoff": max(primes, default=None)}

def infinite_partition(beta=1.5, energy_scale=1.0, statistics="boson", bits=128):
    from flint import arb, ctx
    beta, scale = positive(beta, "beta"), positive(energy_scale, "energy_scale")
    if beta * scale <= 1:
        raise ValueError("the infinite gas comparison requires beta*energy_scale > 1")
    if statistics not in ("boson", "fermion"):
        raise ValueError("statistics must be boson or fermion")
    with ctx.workprec(bits):
        s = arb(beta) * arb(scale)
        value = s.zeta()
        if statistics == "fermion":
            value /= (2 * s).zeta()
        return {"enclosure": str(value), "approximation": float(value),
                "precision_bits": bits, "s": beta * scale}

def recover_prime_modes(start=1, count=5, energy_scale=1.0):
    from prime_successor.fast_analytic import FastAnalyticSuccessor
    scale = positive(energy_scale, "energy_scale")
    engine = FastAnalyticSuccessor(start)
    modes = []
    for _ in range(count):
        prime = engine.next_prime()
        modes.append({"prime": prime, "energy": scale * math.log(prime),
                      "prime_certificate": engine.last_certificate})
    return {"start": start, "modes": modes,
            "energy_precision": "binary64 logarithm; the integer prime has the Arb certificate",
            "identity": "1 is the vacuum contribution, not a prime"}

def demo(primes, *, beta=1.5, seed=1729):
    boson = thermodynamics(primes, beta, statistics="boson")
    fermion = thermodynamics(primes, beta, statistics="fermion")
    recovery = recover_prime_modes(count=5)
    reference = infinite_partition(beta) if beta > 1 else None
    checks = {
        "positive_moments": {"passed": all(x["mean_energy"] >= 0 and x["energy_variance"] >= 0
                                          for x in (boson, fermion))},
        "exact_first_modes": {"passed": [x["prime"] for x in recovery["modes"]] == [2, 3, 5, 7, 11]},
    }
    if reference is not None:
        checks["finite_below_infinite"] = {
            "passed": boson["log_partition"] <= math.log(reference["approximation"]) + 1e-14}
    return result("primon-gas", "finite independent prime oscillators",
                  {"beta": beta, "energy_scale": 1.0, "units": "kB=1"},
                  {"boson": boson, "fermion": fermion, "infinite_boson_reference": reference,
                   "exact_mode_recovery": recovery}, checks)
