"""Bounded experiments with Primeward's unchanged analytic successor engine.

A completed experiment can report a blocked target. Only successor_certified=true
with an actual integer and checked interval means a successor was recovered.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

from flint import arb, ctx
from prime_successor.analytic import PrecisionLimitError
from prime_successor.fast_analytic import FastAnalyticSuccessor

RECORD_EXPONENT = 136_279_841
MAX_INPUT_EXPONENT = 150_000_000
MAX_SEED = 100_000
MAX_PRECISION_BITS = 8_000_000
GUARD_BITS = 256
CALIBRATION_EXPONENTS = (5, 7, 13)
SEED_LIMIT_MESSAGE = "start exceeds the explicit max_seed limit"

def checked_exponent(exponent):
    if isinstance(exponent, bool) or not isinstance(exponent, int) or not 2 <= exponent <= MAX_INPUT_EXPONENT:
        raise ValueError(f"exponent must be an integer in [2, {MAX_INPUT_EXPONENT}]")
    return exponent

def _scale(value):
    log10 = value.log() / arb(10).log()
    floor = log10.floor().unique_fmpz()
    if floor is None:
        raise ArithmeticError("could not enclose a unique decimal order of magnitude")
    order = int(floor)
    return {"decimal_digits": order + 1,
            "scientific_approximation": f"{float(value / arb(10)**order):.10g}e+{order}",
            "log10_enclosure": log10.str(24)}

def requirement_report(exponent):
    """Evaluate compact Arb magnitudes; never construct an integer of size 2**E."""
    e = checked_exponent(exponent)
    with ctx.workprec(160):
        power = arb(2)**e
        lower_budget = (power + 2) * (e + 1) + GUARD_BITS
        seed = _scale(power)
        precision = _scale(lower_budget)
    return {
        "target": f"2^{e}-1", "mersenne_exponent": e,
        "input_binary_digits": e, "input_decimal_digits": seed["decimal_digits"],
        "input_packed_bytes": (e + 7) // 8,
        "analytic_exponent_exact": f"2^{e}+2",
        "successor_cap_exact": f"2^{e+1}+1",
        "seed_sieve_bytes": {"exact": f"2^{e}", **seed},
        "initial_precision_lower_budget_bits": {
            "exact": f"(2^{e}+2)*{e+1}+{GUARD_BITS}", **precision},
        "seed_exceeds_platform_index": e >= sys.maxsize.bit_length(),
        "limits": {"max_seed": MAX_SEED, "max_precision_bits": MAX_PRECISION_BITS,
                   "guard_bits": GUARD_BITS},
        "interpretation": "Requirements of the current initialization implementation; not a lower bound for every possible prime algorithm.",
    }

def trial_is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, math.isqrt(n) + 1, 2))

def verify_successor(previous, candidate):
    """Independent validation only, not part of the analytic generator."""
    if previous > MAX_SEED or candidate > 2 * MAX_SEED + 3:
        raise ValueError("independent trial-division verification is restricted to calibration scale")
    return (candidate > previous and trial_is_prime(candidate)
            and not any(trial_is_prime(n) for n in range(previous + 1, candidate)))

def engine_probe(exponent, *, max_precision_bits=MAX_PRECISION_BITS):
    e = checked_exponent(exponent)
    if not 64 <= max_precision_bits <= MAX_PRECISION_BITS:
        raise ValueError("precision must stay within the reviewed engine budget")
    report = {
        "target": f"2^{e}-1", "mersenne_exponent": e, "status": "not_started",
        "successor": None, "successor_certified": False,
        "starting_primality_verified_in_run": False,
        "residual_initialized": False, "future_candidate_primality_tests_engine": 0,
    }
    began = perf_counter()
    # The input itself is only ~17 MB packed at the record. The seed history
    # would be incomparably larger. Invoke the real constructor with its limits.
    start = (1 << e) - 1
    report["input_bit_length"] = start.bit_length()
    report["python_input_object_bytes"] = sys.getsizeof(start)
    report["engine_attempted"] = True
    try:
        engine = FastAnalyticSuccessor(start, max_seed=MAX_SEED,
                                       max_precision_bits=max_precision_bits)
    except ValueError as exc:
        if str(exc) != SEED_LIMIT_MESSAGE:
            raise
        report.update(status="blocked_max_seed", rejection=str(exc))
    except PrecisionLimitError as exc:
        report.update(status="blocked_precision", rejection=str(exc))
    else:
        report["starting_primality_verified_in_run"] = True
        report["residual_initialized"] = True
        successor = engine.next_prime()
        certificate = engine.last_certificate
        independent = verify_successor(start, successor)
        certified = bool(certificate["interval_containment_checked"]) and independent
        report.update(
            status="certified" if certified else "verification_failed",
            start=start, successor=successor, gap=successor-start,
            successor_certified=certified, certificate=certificate,
            independent_trial_division_verified=independent,
            independent_verifier_tests_candidates=True,
            stats=asdict(engine.stats), precision_work=asdict(engine.precision_work),
            future_candidate_primality_tests_engine=engine.stats.future_candidate_primality_tests)
    report["elapsed_seconds"] = perf_counter() - began
    return report

def bounded_case(exponent, *, timeout_seconds=60, memory_mib=1024):
    checked_exponent(exponent)
    if not 1 <= timeout_seconds <= 180 or not 128 <= memory_mib <= 4096:
        raise ValueError("case bounds must be 1..180 seconds and 128..4096 MiB")
    command = [sys.executable, "-B", "-m", "experiments.record_successor", "worker",
               "--exponent", str(exponent), "--timeout", str(timeout_seconds),
               "--memory-mib", str(memory_mib)]
    began = perf_counter()
    try:
        process = subprocess.run(command, capture_output=True, text=True,
                                 timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired:
        return {"target": f"2^{exponent}-1", "status": "timeout",
                "successor": None, "successor_certified": False,
                "wall_seconds": perf_counter()-began}
    if process.returncode:
        return {"target": f"2^{exponent}-1", "status": "process_failed",
                "successor": None, "successor_certified": False,
                "returncode": process.returncode, "stderr_tail": process.stderr[-2000:],
                "wall_seconds": perf_counter()-began}
    report = json.loads(process.stdout)
    report["wall_seconds"] = perf_counter()-began
    report["bounds"] = {"timeout_seconds": timeout_seconds, "memory_mib": memory_mib}
    return report

def provenance():
    root = Path(__file__).resolve().parents[1]
    sources = ["prime_successor/analytic.py", "prime_successor/fast_analytic.py",
               "experiments/record_successor.py"]
    return {"commit": os.environ.get("GITHUB_SHA"), "run_id": os.environ.get("GITHUB_RUN_ID"),
            "python": platform.python_version(), "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "source_sha256": {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
                              for name in sources}}

def markdown_summary(report):
    lines = ["# Primeward successor experiment", ""]
    if report["experiment"] == "target":
        case, requirements = report["case"], report["requirements"]
        lines += [f"Target: **{case['target']}**", "",
                  f"Outcome: **{case['status']}**",
                  f"Successor certified: **{str(case['successor_certified']).lower()}**", ""]
        if case["successor_certified"]:
            lines += [f"Immediate successor: **{case['successor']}**", ""]
        else:
            lines += ["**No next prime was produced for this target.**", ""]
        lines += [f"Observed engine response: {case.get('rejection', case['status'])}", "",
                  f"Current seed sieve: `{requirements['seed_sieve_bytes']['exact']}` bytes.",
                  f"Initial precision lower budget: `{requirements['initial_precision_lower_budget_bits']['exact']}` bits.", "",
                  "These describe the current implementation. Increasing runner count does not supply the missing initialized state."]
    else:
        lines += ["These are separate calibration inputs; they do not solve the record target.", "",
                  "| Start | Status | Successor | Engine candidate tests |",
                  "| --- | --- | --- | --- |"]
        for case in report["cases"]:
            lines += [f"| {case['target']} | {case['status']} | {case.get('successor')} | {case.get('future_candidate_primality_tests_engine', 'n/a')} |"]
        lines += ["", "Trial division is used independently to verify calibration answers."]
    lines += ["", "Workflow completion means the experiment ran; only an explicit certified successor is a prime-successor result.", ""]
    return "\n".join(lines)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["target", "calibrate", "worker"])
    parser.add_argument("--exponent", type=int, default=RECORD_EXPONENT)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--memory-mib", type=int, default=1024)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        checked_exponent(args.exponent)
        if not 1 <= args.timeout <= 180 or not 128 <= args.memory_mib <= 4096:
            raise ValueError("case bounds must be 1..180 seconds and 128..4096 MiB")
        if args.mode == "worker":
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (args.memory_mib * 1024**2,) * 2)
            resource.setrlimit(resource.RLIMIT_CPU, (args.timeout, args.timeout + 1))
            print(json.dumps(engine_probe(args.exponent), allow_nan=False))
            return 0
        report = {"schema_version": "1.0", "experiment": args.mode, "provenance": provenance()}
        if args.mode == "target":
            report["requirements"] = requirement_report(args.exponent)
            report["case"] = bounded_case(args.exponent, timeout_seconds=args.timeout,
                                           memory_mib=args.memory_mib)
            good = report["case"]["status"] in ("certified", "blocked_max_seed", "blocked_precision")
        else:
            report["cases"] = [bounded_case(e, timeout_seconds=args.timeout,
                                              memory_mib=args.memory_mib)
                               for e in CALIBRATION_EXPONENTS]
            good = all(c["successor_certified"] for c in report["cases"])
        report["experiment_completed"] = good
        encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded)
            args.output.with_suffix(".md").write_text(markdown_summary(report))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a") as stream:
                stream.write(markdown_summary(report))
        print("RESULT_JSON=" + json.dumps(report, separators=(",", ":"), allow_nan=False))
        return 0 if good else 1
    except (ValueError, ArithmeticError) as exc:
        parser.error(str(exc))
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
