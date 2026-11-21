"""Input validation, prime sources, and stable thermal factors."""
from __future__ import annotations
import math
from numbers import Integral
from typing import Iterable
from prime_successor.engine import is_prime_u64

def positive(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite positive number")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return value

def finite_values(values: Iterable[float], name: str) -> list[float]:
    result = [float(v) for v in values]
    if not all(math.isfinite(v) for v in result):
        raise ValueError(f"{name} must contain finite numbers")
    return result

def prime_labels(primes: Iterable[int]) -> list[int]:
    values = list(primes)
    if any(isinstance(p, bool) or not isinstance(p, Integral) for p in values):
        raise ValueError("prime labels must be integers, excluding booleans")
    values = [int(p) for p in values]
    if any(p < 2 or p >= 2**64 or not is_prime_u64(p) for p in values):
        raise ValueError("prime labels must be primes below 2**64")
    if any(b <= a for a, b in zip(values, values[1:])):
        raise ValueError("prime labels must be strictly increasing")
    return values

def prime_sequence(count=32, start=1, method="residual"):
    if isinstance(count, bool) or not isinstance(count, Integral) or count < 0:
        raise ValueError("count must be a nonnegative integer")
    if method == "residual":
        from prime_successor.fast_analytic import FastAnalyticSuccessor
        engine = FastAnalyticSuccessor(start)
    elif method == "bytearray":
        from prime_successor.engine import BytearraySieveSuccessor
        engine = BytearraySieveSuccessor(start)
    else:
        raise ValueError("method must be residual or bytearray")
    return engine.take(int(count))

def thermal_mode(beta, energy, phase):
    """Return log(normalized paired factor), log denominator, phase of Z(beta+it).

    phase is dimensionless. The stable expression avoids subtracting nearly
    equal partition logarithms or squaring a tiny 1-exp(-beta*energy).
    """
    b = beta * energy
    if not math.isfinite(b) or b <= 0 or not math.isfinite(phase):
        raise ValueError("effective inverse temperature or phase is outside binary64 range")
    a = -math.expm1(-b)
    r = math.exp(-b)
    sine = math.sin(0.5 * phase)
    u = 2 * math.exp(-0.5 * b) * abs(sine)
    if u <= a:
        ratio = -math.log1p((u / a)**2)
    else:
        ratio = 2 * (math.log(a) - math.log(u)) - math.log1p((a / u)**2)
    denominator = math.hypot(a, u)
    argument = -math.atan2(r * math.sin(phase), a + 2 * r * sine**2)
    log_denominator = (0.5 * math.log1p(r * (r - 2 * math.cos(phase)))
                       if b >= math.log(2) else math.log(denominator))
    return ratio, log_denominator, argument

def exp_or_none(log_value):
    """JSON-safe exponentiation; a null means overflow, not zero."""
    try:
        return math.exp(log_value)
    except OverflowError:
        return None

def linspace(start, stop, count):
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("count must be a positive integer")
    if count == 1:
        return [float(start)]
    return [start + (stop - start) * i / (count - 1) for i in range(count)]

def result(name, model, parameters, data, checks):
    return {"application": name, "model": model, "parameters": parameters,
            "data": data, "checks": checks,
            "passed": all(bool(c["passed"]) for c in checks.values())}
