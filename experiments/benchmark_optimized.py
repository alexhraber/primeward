"""Reproduce precision-aware analytic successor comparisons.

Run from the project root after installing requirements:
    python experiments/benchmark_optimized.py
"""

from pathlib import Path
import argparse
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prime_successor.optimized import run_benchmarks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "optimized_benchmarks.json"))
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    run_benchmarks(args.output, repeats=args.repeats)
