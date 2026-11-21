"""Command-line entry point; all predictions and exact engines are labelled."""

from __future__ import annotations

import argparse
import json

from .engine import (
    BytearraySieveSuccessor,
    MillerRabinSuccessor,
    ResidueBitsetSuccessor,
    TrialDivisionSuccessor,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prime successor research lab")
    parser.add_argument(
        "--method", choices=["analytic", "optimized", "residual", "bitset", "bytearray", "miller-rabin", "trial"],
        default="residual",
    )
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--block-size", type=int, default=4096)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verify", action="store_true", help="Independently scan after computing; verification work is separate")
    args = parser.parse_args()
    analytic_method = args.method in ("analytic", "optimized", "residual")
    if analytic_method:
        if args.method == "analytic":
            from .analytic import AnalyticSuccessor
            engine = AnalyticSuccessor(args.start)
        elif args.method == "optimized":
            from .optimized import PrecisionAwareSuccessor
            engine = PrecisionAwareSuccessor(args.start)
        else:
            from .fast_analytic import FastAnalyticSuccessor
            engine = FastAnalyticSuccessor(args.start)
    else:
        kinds = {
            "bitset": ResidueBitsetSuccessor,
            "bytearray": BytearraySieveSuccessor,
            "miller-rabin": MillerRabinSuccessor,
            "trial": TrialDivisionSuccessor,
        }
        options = {"block_size": args.block_size} if args.method in ("bitset", "bytearray") else {}
        engine = kinds[args.method](args.start, **options)
    outputs = engine.take(args.count)
    verified = None
    if args.verify:
        verified = outputs == TrialDivisionSuccessor(args.start).take(args.count)
        if not verified:
            raise AssertionError("Independent verification failed")
    status = engine.status() if analytic_method else {
        "current": engine.current, "stats": engine.stats.to_dict()
    }
    result = {
        "method": args.method,
        "start": args.start,
        "successors": outputs,
        "independent_trial_verification": verified,
        "verification_cost_included_in_engine_times": False,
        **status,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Successors:", ", ".join(map(str, outputs)))
        print("Method:", args.method)
        if verified is not None:
            print("Independent verification:", "passed" if verified else "failed")
        print("Accounting:", json.dumps(status["stats"], sort_keys=True))


if __name__ == "__main__":
    main()
