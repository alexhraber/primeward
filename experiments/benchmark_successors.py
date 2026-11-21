"""Compare exact successors with paid setup and a subsequent warm batch.

Run from the repository root. Each case is START:COLD_COUNT:WARM_COUNT;
omitting WARM_COUNT repeats the cold count. Every repetition creates a fresh
engine, produces two consecutive batches, and verifies every result outside
its timed phases. Several bytearray block sizes provide measured controls.
FLINT caches are cleared before each run unless explicitly retained; the warm
batch always reuses its own engine and caches. Imports and process startup are
excluded. State inventories are counters/estimates, not peak native memory.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import asdict
from datetime import datetime, timezone
import gc
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import time

import flint

from prime_successor.analytic import PrecisionLimitError
from prime_successor.engine import SieveLimitError, reference_primes


ROOT = Path(__file__).resolve().parents[1]
METHODS = {
    "original": ("prime_successor.analytic", "AnalyticSuccessor", "analytic"),
    "optimized": ("prime_successor.optimized", "PrecisionAwareSuccessor", "analytic"),
    "residual": ("prime_successor.fast_analytic", "FastAnalyticSuccessor", "analytic"),
    "sieve": ("prime_successor.engine", "BytearraySieveSuccessor", "sieve"),
    "bitset": ("prime_successor.engine", "ResidueBitsetSuccessor", "sieve"),
    "miller-rabin": ("prime_successor.engine", "MillerRabinSuccessor", "candidate-scan"),
}
ALIASES = {"analytic": "original", "fast": "residual", "bytearray": "sieve"}


def parse_cases(text: str) -> list[tuple[int, int, int]]:
    cases = []
    for item in text.split(","):
        parts = tuple(int(value) for value in item.split(":"))
        if len(parts) == 2:
            parts = (*parts, parts[1])
        if len(parts) != 3 or parts[0] < 1 or parts[1] < 1 or parts[2] < 0:
            raise ValueError("cases must be START:COLD_COUNT[:WARM_COUNT], with positive start/cold count")
        if parts in cases:
            raise ValueError("duplicate case")
        cases.append(parts)
    return cases


def parse_methods(text: str, block_sizes: list[int]) -> list[tuple[str, int | None]]:
    selected = []
    for item in text.split(","):
        match = re.fullmatch(r"(sieve|bytearray|bitset)-(\d+)", item)
        if match:
            method, size = ALIASES.get(match[1], match[1]), int(match[2])
            if not 1 <= size <= 1048576:
                raise ValueError("sieve block size must be from 1 through 1048576")
            options = [(method, size)]
        else:
            method = ALIASES.get(item, item)
            if method not in METHODS:
                raise ValueError(f"unknown method: {item}")
            options = [(method, size) for size in block_sizes] if METHODS[method][2] == "sieve" else [(method, None)]
        for option in options:
            if option in selected:
                raise ValueError(f"duplicate method configuration: {item}")
            selected.append(option)
    return selected


def expected_outputs(start: int, count: int, maximum: int) -> list[int]:
    """Independent whole-range sieve; its primes are never given to an engine."""
    bound = min(maximum, start + max(64, 32 * count))
    while True:
        primes = reference_primes(bound)
        index = bisect_right(primes, start)
        if start != 1 and (index == 0 or primes[index - 1] != start):
            raise ValueError(f"start {start} is not prime")
        if len(primes) - index >= count:
            return primes[index:index + count]
        if bound == maximum:
            raise ValueError("independent oracle range exhausted; raise --oracle-max-integer")
        bound = min(maximum, max(bound + 1, 2 * bound))


def inventory(engine) -> dict:
    result = {}
    if hasattr(engine, "precision_bits"):
        history = engine._primes
        result.update(
            precision_bits=engine.precision_bits,
            stored_past_primes=len(history),
            prime_history_python_bytes=sys.getsizeof(history) + sum(map(sys.getsizeof, history)),
        )
        residual = getattr(engine, "_residual", None)
        value = residual if residual is not None else getattr(engine, "_value", None)
        if value is not None:
            result.update(
                numeric_state="residual" if residual is not None else "euler_product",
                stored_midpoint_bits=value.bits(),
                stored_relative_accuracy_bits=value.rel_accuracy_bits(),
            )
        if hasattr(engine, "residual_precision_bits"):
            result["residual_precision_bits"] = engine.residual_precision_bits
    if hasattr(engine, "memory_bytes_estimate"):
        result["sieve_python_state_estimate_bytes"] = engine.memory_bytes_estimate()
        result["sieve_payload_bytes"] = engine.payload_bytes()
    return result


def measure(spec: dict, start: int, cold_count: int, warm_count: int, expected: list[int], retain_flint_caches: bool) -> dict:
    gc.collect()
    if not retain_flint_caches:
        # Public python-flint API; free internal MPFR/FLINT/Arb caches before
        # a fresh-engine run so another method cannot donate a zeta cache.
        flint.ctx.cleanup()
    begin = time.perf_counter_ns()
    engine = spec["class"](start, **spec["options"])
    setup_ns = time.perf_counter_ns() - begin
    begin = time.perf_counter_ns()
    cold = engine.take(cold_count)
    cold_ns = time.perf_counter_ns() - begin
    cold_stats = asdict(engine.stats)
    cold_inventory = inventory(engine)
    if warm_count:
        begin = time.perf_counter_ns()
        warm = engine.take(warm_count)
        warm_ns = time.perf_counter_ns() - begin
    else:
        warm, warm_ns = [], 0
    if cold + warm != expected:
        raise AssertionError(f"Incorrect successors for {spec['key']} at {(start, cold_count, warm_count)}")
    result = {
        "setup_seconds": setup_ns / 1e9,
        "cold_advance_seconds": cold_ns / 1e9,
        "cold_total_seconds": (setup_ns + cold_ns) / 1e9,
        "warm_advance_seconds": warm_ns / 1e9,
        "session_total_seconds": (setup_ns + cold_ns + warm_ns) / 1e9,
        "cold_stats": cold_stats,
        "final_stats": asdict(engine.stats),
        "cold_state_inventory": cold_inventory,
        "final_state_inventory": inventory(engine),
        "all_outputs_match_independent_sieve": True,
    }
    if hasattr(engine, "precision_work"):
        result["precision_work"] = asdict(engine.precision_work)
    return result


def source_metadata() -> dict:
    def git(*args):
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None

    files = sorted((ROOT / "prime_successor").glob("*.py")) + [Path(__file__).resolve()]
    return {
        "git_commit": git("rev-parse", "HEAD"),
        "git_worktree_dirty": bool(git("status", "--porcelain", "--untracked-files=normal")),
        "sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
    }


def run(args) -> dict:
    specs = []
    for method, size in parse_methods(args.methods, args.sieve_block_sizes):
        module, name, category = METHODS[method]
        cls = getattr(importlib.import_module(module), name)
        options = {"max_seed": args.max_seed, "max_precision_bits": args.max_precision_bits} if category == "analytic" else {}
        if size is not None:
            options["block_size"] = size
        specs.append({"key": f"{method}-{size}" if size else method, "method": method, "class": cls, "category": category, "options": options})
    report = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": source_metadata(),
        "runtime": {
            "python": platform.python_version(), "platform": platform.platform(),
            "machine": platform.machine(), "python_flint": flint.__version__,
            "cpu_count": os.cpu_count(), "flint_threads": getattr(flint.ctx, "threads", None),
            "cpu_affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
            "timer_resolution_seconds": time.get_clock_info("perf_counter").resolution,
            "gc_enabled": gc.isenabled(),
            "native_sieve_modules": {name: importlib.util.find_spec(name) is not None for name in ("primesieve", "pyprimesieve")},
        },
        "request": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        "timing_scope": "Fresh engine setup plus cold batch, then a distinct sequential warm batch. Setup is paid once and whole-session totals include both batches. Imports, GC collection, report instrumentation, and independent verification excluded; all built-in engine accounting, epoch rebuilds, and sieve block construction included. Engine order rotates. These are Python sieve baselines, not optimized native prime libraries.",
        "cache_policy": "Retain internal FLINT caches across all runs." if args.retain_flint_caches else "Call ctx.cleanup() before each fresh-engine run outside timers to clear internal MPFR/FLINT/Arb caches. The subsequent warm batch reuses its own state and caches. This does not reset the Python process or all operating-system caches.",
        "state_inventory_scope": "Precision budgets, actual retained Arb midpoint bit length/relative accuracy, and historical-prime counts. Python object estimates exclude native Arb allocations and temporary peak memory. Midpoint bits omit interval radii and diagnostic balls. These are not total process memory or CPU complexity.",
        "cases": [],
    }
    for start, cold_count, warm_count in args.cases:
        expected = expected_outputs(start, cold_count + warm_count, args.oracle_max_integer)
        case = {
            "start": start, "cold_count": cold_count, "warm_count": warm_count,
            "warm_start": expected[cold_count - 1], "first": expected[0], "last": expected[-1],
            "outputs_sha256": hashlib.sha256(json.dumps(expected, separators=(",", ":")).encode()).hexdigest(),
            "methods": [], "comparisons": [],
        }
        rows = {}
        for spec in specs:
            row = {"engine": spec["key"], "class": spec["class"].__name__, "options": spec["options"], "status": "complete", "runs": []}
            if spec["category"] == "analytic" and start > args.max_seed:
                row.update(status="resource_limit", error="start exceeds --max-seed")
            rows[spec["key"]] = row
            case["methods"].append(row)
        for repeat in range(args.repeats):
            offset = repeat % len(specs)
            for spec in specs[offset:] + specs[:offset]:
                row = rows[spec["key"]]
                if row["status"] != "complete":
                    continue
                try:
                    sample = measure(spec, start, cold_count, warm_count, expected, args.retain_flint_caches)
                except (PrecisionLimitError, SieveLimitError, OverflowError) as exc:
                    row.update(status="resource_limit", error=f"{type(exc).__name__}: {exc}")
                    continue
                sample["repetition"] = repeat
                row["runs"].append(sample)
        durations = ("setup_seconds", "cold_advance_seconds", "cold_total_seconds", "warm_advance_seconds", "session_total_seconds")
        for row in case["methods"]:
            if row["status"] != "complete":
                continue
            if len(row["runs"]) != args.repeats:
                raise AssertionError("Incomplete timing samples marked complete")
            row["timings"] = {
                duration: {"median": statistics.median(values), "min": min(values), "max": max(values)}
                for duration in durations for values in [[sample[duration] for sample in row["runs"]]]
            }
            if warm_count:
                row["median_warm_seconds_per_prime"] = row["timings"]["warm_advance_seconds"]["median"] / warm_count
        sieves = [row for row in case["methods"] if row["engine"].startswith("sieve-") and row["status"] == "complete"]
        if sieves:
            for duration in ("cold_total_seconds", "warm_advance_seconds", "session_total_seconds"):
                if duration == "warm_advance_seconds" and not warm_count:
                    continue
                baseline = min(sieves, key=lambda row: row["timings"][duration]["median"])
                baseline_seconds = baseline["timings"][duration]["median"]
                for row in case["methods"]:
                    if row["status"] == "complete" and not row["engine"].startswith("sieve-"):
                        case["comparisons"].append({
                            "engine": row["engine"], "duration": duration, "median_seconds": row["timings"][duration]["median"],
                            "fastest_measured_bytearray": baseline["engine"], "bytearray_median_seconds": baseline_seconds,
                            "engine_over_bytearray": row["timings"][duration]["median"] / baseline_seconds,
                        })
        report["cases"].append(case)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"start": start, "cold_count": cold_count, "warm_count": warm_count, "comparisons": case["comparisons"]}), flush=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Fresh-state and continued-state exact successor benchmarks")
    parser.add_argument("--output", type=Path, default=Path("results/successor_benchmarks.json"))
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--methods", "--engines", dest="methods", default="original,optimized,residual,sieve-64,sieve-512,sieve-4096", help="comma-separated original,optimized,residual,sieve-N,bitset-N,miller-rabin; aliases analytic,fast,bytearray")
    parser.add_argument("--cases", default="1:200:200,113:100:100,997:30:30,10007:10:10", help="comma-separated START:COLD_COUNT[:WARM_COUNT]")
    parser.add_argument("--sieve-block-sizes", default="64,512,4096", help="comma-separated numbers of odd candidate slots")
    parser.add_argument("--max-seed", type=int, default=10007, help="explicit analytic initialization limit")
    parser.add_argument("--max-precision-bits", type=int, default=1000000, help="explicit analytic arithmetic resource budget")
    parser.add_argument("--oracle-max-integer", type=int, default=2000000, help="maximum integer materialized by the independent verification sieve")
    parser.add_argument("--retain-flint-caches", action="store_true", help="keep library caches across methods/repetitions instead of clearing them before each fresh-engine run")
    args = parser.parse_args()
    try:
        args.cases = parse_cases(args.cases)
        args.sieve_block_sizes = [int(value) for value in args.sieve_block_sizes.split(",")]
        if len(set(args.sieve_block_sizes)) != len(args.sieve_block_sizes) or any(not 1 <= size <= 1048576 for size in args.sieve_block_sizes):
            raise ValueError("sieve block sizes must be distinct integers from 1 through 1048576")
        parse_methods(args.methods, args.sieve_block_sizes)
        if args.repeats < 1 or args.max_seed < 1 or args.max_precision_bits < 64 or args.oracle_max_integer < 2:
            raise ValueError("repeats/max-seed must be positive, precision at least 64, and oracle limit at least 2")
        if any(start >= args.oracle_max_integer for start, _, _ in args.cases):
            raise ValueError("every seed must be below --oracle-max-integer")
    except ValueError as exc:
        parser.error(str(exc))
    run(args)


if __name__ == "__main__":
    main()
