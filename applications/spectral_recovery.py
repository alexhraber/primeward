"""Interval recovery of finite spectra from positive thermal observations.

Finite-level traces C(beta)=sum exp(-beta E_j) and bosonic mode residuals
R(beta)=prod(1-exp(-beta E_j))^-1-1 are different observation models.
Known level removal subtracts its entire exponential interval. Known independent
boson removal uses R'=R-a-R*a. No midpoint subtraction is used.

The recovery bound requires a known complete level count, unit positive weights,
positive energies, and a truthful lower bound on adjacent energy gaps.
Bounded input uncertainty is retained. More arithmetic precision cannot remove it.
Background: https://arxiv.org/html/1903.06476v2
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from flint import arb, ctx
from .common import positive, finite_values, result

@dataclass(frozen=True)
class Observation:
    beta: float
    value: arb
    model: str = "finite_levels"

def _settings(bits):
    if isinstance(bits, bool) or not isinstance(bits, int) or not 64 <= bits <= 8192:
        raise ValueError("precision_bits must be an integer in [64, 8192]")

def observations(energies, betas, *, relative_noise=0.0, absolute_noise=0.0,
                 model="finite_levels", precision_bits=192):
    """Synthetic oracle: observations contain no hidden energy list.

    Noise parameters describe deterministic absolute bounds, not Gaussian
    standard deviations. The observation midpoint is the exact synthetic signal.
    """
    _settings(precision_bits)
    energies = finite_values(energies, "energies")
    if not energies or any(e <= 0 for e in energies):
        raise ValueError("the synthetic spectrum must contain positive energies")
    betas = [positive(b, "beta") for b in betas]
    relative_noise, absolute_noise = float(relative_noise), float(absolute_noise)
    if not all(math.isfinite(n) and n >= 0 for n in (relative_noise, absolute_noise)):
        raise ValueError("noise bounds must be finite and nonnegative")
    if model not in ("finite_levels", "boson_modes"):
        raise ValueError("unknown observation model")
    samples = []
    with ctx.workprec(precision_bits):
        for beta in betas:
            value = arb(0)
            for energy in energies:
                a = (-arb(beta) * arb(energy)).exp()
                value = value + a if model == "finite_levels" else (value + a) / (1 - a)
            error = arb(absolute_noise) + arb(relative_noise) * value.abs_upper()
            samples.append(Observation(beta, (value - error).union(value + error), model))
    return samples

def lowest_interval(samples, remaining_count, *, gap_lower_bound=0.0,
                    model="finite_levels", precision_bits=192):
    _settings(precision_bits)
    if isinstance(remaining_count, bool) or not isinstance(remaining_count, int) or remaining_count < 1:
        raise ValueError("remaining_count must be a positive integer")
    gap = float(gap_lower_bound)
    if not math.isfinite(gap) or gap < 0:
        raise ValueError("gap_lower_bound must be finite and nonnegative")
    if model not in ("finite_levels", "boson_modes"):
        raise ValueError("unknown observation model")
    if model == "boson_modes" and gap:
        raise ValueError("the boson bound currently uses only the mode count, not a gap assumption")
    bound = None
    with ctx.workprec(precision_bits):
        for sample in samples:
            positive(sample.beta, "beta")
            if sample.model != model:
                raise ValueError("observation and decoder models differ")
            if not sample.value.is_finite():
                raise ValueError("observation intervals must be finite")
            if sample.value.upper() <= 0:
                return None, "inconsistent: remaining positive spectrum has nonpositive trace"
            if not sample.value > 0:
                continue
            b = arb(sample.beta)
            lo, hi = sample.value.lower(), sample.value.upper()
            if model == "finite_levels":
                factor = 1 + (remaining_count - 1) * (-b * arb(gap)).exp()
                lower = -hi.log() / b
                upper = (factor.log() - lo.log()) / b
            else:
                # Each mode contributes a full geometric occupation series.
                lower = -(hi / (1 + hi)).log() / b
                upper = -(-(-lo.log1p() / remaining_count).expm1()).log() / b
            if upper.upper() < 0:
                return None, "inconsistent: observation excludes positive energies"
            candidate = lower.union(upper)
            if lower < 0:
                candidate = candidate.intersection(arb(0).union(upper))
            try:
                bound = candidate if bound is None else bound.intersection(candidate)
            except ValueError:
                return None, "inconsistent: observations or model assumptions conflict"
        if bound is None:
            return None, "unresolved: no strictly positive residual observation"
        return bound, "bounded"

def remove_level(samples, energy_interval, *, precision_bits=192):
    _settings(precision_bits)
    samples = list(samples)
    if any(s.model != "finite_levels" for s in samples):
        raise ValueError("level removal requires finite-level observations")
    with ctx.workprec(precision_bits):
        return [Observation(s.beta, s.value - (-arb(s.beta) * energy_interval).exp(), s.model)
                for s in samples]

def remove_boson_mode(samples, energy_interval, *, precision_bits=192):
    _settings(precision_bits)
    output = []
    with ctx.workprec(precision_bits):
        for sample in samples:
            if sample.model != "boson_modes":
                raise ValueError("boson removal requires bosonic residual observations")
            a = (-arb(sample.beta) * energy_interval).exp()
            output.append(Observation(sample.beta, sample.value - a - sample.value * a, sample.model))
    return output

def recover_levels(samples, level_count, *, tolerance=.003, gap_lower_bound=0.0, precision_bits=192):
    _settings(precision_bits)
    tolerance = positive(tolerance, "tolerance")
    if isinstance(level_count, bool) or not isinstance(level_count, int) or level_count < 1:
        raise ValueError("level_count must be a positive integer")
    remaining = list(samples)
    if not remaining or any(s.model != "finite_levels" for s in remaining):
        raise ValueError("provide finite-level observations")
    levels = []
    with ctx.workprec(precision_bits):
        for count in range(level_count, 0, -1):
            bound, reason = lowest_interval(remaining, count, gap_lower_bound=gap_lower_bound,
                                           precision_bits=precision_bits)
            if bound is None or not 2 * bound.rad() <= arb(tolerance):
                if bound is not None:
                    reason = "unresolved: energy interval wider than requested tolerance"
                return {"status": "inconsistent" if reason.startswith("inconsistent:") else ("partial" if levels else "unresolved"), "reason": reason,
                        "levels": levels, "next_interval": bound, "residuals": remaining,
                        "precision_bits": precision_bits}
            levels.append(bound)
            remaining = remove_level(remaining, bound, precision_bits=precision_bits)
        consistent = all(s.value.contains(0) for s in remaining)
    return {"status": "complete" if consistent else "inconsistent",
            "reason": "all levels enclosed" if consistent else "final residual excludes zero",
            "levels": levels, "next_interval": None, "residuals": remaining,
            "precision_bits": precision_bits}

def interval_report(value):
    if value is None:
        return None
    # These explicit outward nextafter values are for plotting and JSON consumers.
    return {"arb_enclosure": value.str(50), "midpoint": float(value.mid()),
            "lower": math.nextafter(float(value.lower()), -math.inf),
            "upper": math.nextafter(float(value.upper()), math.inf)}

def recovery_report(recovery):
    return {k: v for k, v in recovery.items() if k not in ("levels", "next_interval", "residuals")} | {
        "levels": [interval_report(v) for v in recovery["levels"]],
        "next_interval": interval_report(recovery["next_interval"]),
        "residuals": [{"beta": s.beta, "enclosure": s.value.str(50)} for s in recovery["residuals"]]
    }

def demo(primes, *, beta=1.5, seed=1729):
    truth = [1.0, 1.6, 2.7]
    betas = [4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64]
    cases, covered = {}, True
    for name, relative, absolute in [("clean", 0, 0), ("relative_noise", 1e-4, 0),
                                     ("absolute_noise", 0, 1e-4)]:
        samples = observations(truth, betas, relative_noise=relative, absolute_noise=absolute)
        recovered = recover_levels(samples, len(truth), gap_lower_bound=.5)
        coverage = all(interval.contains(arb(energy)) for interval, energy in zip(recovered["levels"], truth))
        covered = covered and coverage
        cases[name] = recovery_report(recovered) | {"truth_contained": coverage,
                                                   "relative_noise_bound": relative,
                                                   "absolute_noise_bound": absolute}
    boson_samples = observations(truth, [4, 16, 32], model="boson_modes")
    boson_bound, reason = lowest_interval(boson_samples, 3, model="boson_modes")
    data = {"truth_for_evaluation_only": truth, "betas": betas, "cases": cases,
            "boson_lowest_mode": interval_report(boson_bound), "boson_bound_status": reason,
            "assumptions": "known level count; unit weights; positive energies; adjacent gaps >= 0.5"}
    return result("spectral-recovery", "finite positive thermal traces with bounded errors",
                  {"tolerance": .003, "gap_lower_bound": .5, "precision_bits": 192}, data, {
                      "clean_recovery": {"passed": cases["clean"]["status"] == "complete"},
                      "interval_coverage": {"passed": covered and boson_bound is not None and boson_bound.contains(arb(1))},
                      "noise_refusal": {"passed": cases["absolute_noise"]["status"] != "complete"}
                  })
