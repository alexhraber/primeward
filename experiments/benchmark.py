"""Reproducible exact-engine comparisons; no native-library speed claims."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import statistics
import time
from dataclasses import asdict
from pathlib import Path

import flint

from prime_successor.analytic import AnalyticSuccessor
from prime_successor.engine import (
    BytearraySieveSuccessor, MillerRabinSuccessor, ResidueBitsetSuccessor,
)


def measure(kind, start, count, repeats):
    runs = []
    outputs = None
    for _ in range(repeats):
        t = time.perf_counter()
        engine = kind(start)
        setup = time.perf_counter() - t
        t = time.perf_counter()
        values = engine.take(count)
        advance = time.perf_counter() - t
        if outputs is not None:
            assert values == outputs
        outputs = values
        runs.append({
            "setup_seconds": setup,
            "advance_seconds": advance,
            "total_seconds": setup + advance,
            "stats": asdict(engine.stats),
        })
    return {
        "method": kind.__name__, "start": start, "count": count,
        "first": outputs[0], "last": outputs[-1],
        "outputs": outputs,
        "outputs_sha256": hashlib.sha256(json.dumps(outputs).encode()).hexdigest(),
        "median_setup_seconds": statistics.median(r["setup_seconds"] for r in runs),
        "median_advance_seconds": statistics.median(r["advance_seconds"] for r in runs),
        "median_total_seconds": statistics.median(r["total_seconds"] for r in runs),
        "runs": runs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "python_flint": flint.__version__,
        "repeats": args.repeats,
        "timing_scope": "Wall-clock medians on this machine; initialization plus advance. Separate verifier excluded. All baselines are our Python implementations, not optimized native prime libraries.",
        "cases": [],
    }
    small = [(1, 200), (113, 100), (997, 30), (10_007, 10)]
    for start, count in small:
        expected = MillerRabinSuccessor(start).take(count)
        for kind in [AnalyticSuccessor, BytearraySieveSuccessor, MillerRabinSuccessor]:
            row = measure(kind, start, count, args.repeats)
            assert row["outputs"] == expected
            row["matches_independent_candidate_scan"] = True
            report["cases"].append(row)
            print(json.dumps({k: row[k] for k in ["method", "start", "count", "last", "median_total_seconds"]}), flush=True)
    for start in [1, 1_000_003, 1_000_000_007]:
        count = 5_000
        expected = MillerRabinSuccessor(start).take(count)
        for kind in [ResidueBitsetSuccessor, BytearraySieveSuccessor, MillerRabinSuccessor]:
            row = measure(kind, start, count, args.repeats)
            assert row["outputs"] == expected
            row["matches_independent_candidate_scan"] = True
            report["cases"].append(row)
            print(json.dumps({k: row[k] for k in ["method", "start", "count", "last", "median_total_seconds"]}), flush=True)
    (args.output / "exact_benchmarks.json").write_text(json.dumps(report, indent=2) + "\n")
    fields = ["method", "start", "count", "first", "last", "median_setup_seconds", "median_advance_seconds", "median_total_seconds", "outputs_sha256", "matches_independent_candidate_scan"]
    with (args.output / "exact_benchmarks.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(report["cases"])


if __name__ == "__main__":
    main()
