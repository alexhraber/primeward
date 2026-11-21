"""Command-line runner for the reproducible physics applications."""
from __future__ import annotations
import argparse
import importlib
import json
from pathlib import Path
import sys
from .common import prime_sequence

APPLICATIONS = {
    "primon-gas": ("primon_gas", "Finite boson/fermion thermodynamics and exact prime-mode recovery"),
    "spectral-recovery": ("spectral_recovery", "Recover finite energy intervals from noisy thermal traces"),
    "scattering": ("scattering", "Prime-position structure factors with matched controls"),
    "transport": ("transport", "Lossless 1D delta-scatterer wave transport"),
    "inverse-spectrum": ("inverse_spectrum", "Fit a quantum potential and check grid/box errors"),
    "form-factor": ("form_factor", "Thermal spectral form factor of a finite prime gas"),
    "prime-orbits": ("prime_orbits", "Finite Gaussian-smoothed prime-orbit trace signal"),
    "twisted-gas": ("twisted_gas", "Paired-charge prime gas with arbitrary phases"),
}

def run(name, primes, *, beta=1.5, seed=1729, prime_method="residual", start=1):
    module = importlib.import_module("." + APPLICATIONS[name][0], __package__)
    output = module.demo(primes, beta=beta, seed=seed)
    output["prime_source"] = {"method": prime_method, "start": start,
                              "count": len(primes), "primes": list(primes)}
    output["schema_version"] = "1.0"
    return output

def _write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("application", choices=["list", "run-all", "verify", *APPLICATIONS])
    parser.add_argument("--count", type=int, default=32, help="number of input primes (default: 32)")
    parser.add_argument("--start", type=int, default=1, help="generate primes strictly above this integer")
    parser.add_argument("--prime-method", choices=["residual", "bytearray"], default="residual")
    parser.add_argument("--beta", type=float, default=1.5)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--output", type=Path, help="JSON output for one application")
    parser.add_argument("--output-dir", type=Path, help="directory for run-all JSON and optional figures")
    parser.add_argument("--plot", nargs="?", const="auto", help="save a figure; optional filename for one app")
    parser.add_argument("--summary", action="store_true", help="print only checks and success status")
    args = parser.parse_args(argv)
    if args.application == "list":
        for name, (_, description) in APPLICATIONS.items():
            print(f"{name}: {description}")
        return 0
    if args.count < 1 or args.count > 4096:
        parser.error("--count must be in [1, 4096]")
    multiple = args.application in ("run-all", "verify")
    if multiple and args.output:
        parser.error("use --output-dir with run-all")
    if not multiple and args.output_dir:
        parser.error("use --output for one application")
    if args.application == "verify" and (args.output_dir or args.plot):
        parser.error("verify writes no artifacts; use run-all to save examples")
    try:
        primes = prime_sequence(args.count, args.start, args.prime_method)
        names = list(APPLICATIONS) if multiple else [args.application]
        outputs = []
        for name in names:
            data = run(name, primes, beta=args.beta, seed=args.seed,
                       prime_method=args.prime_method, start=args.start)
            outputs.append(data)
            path = args.output_dir / (name + ".json") if args.output_dir else args.output
            if path:
                _write(path, data)
            if args.plot:
                from .plotting import plot_result
                image_path = ((args.output_dir or Path(".")) / (name + ".png")
                              if multiple or args.plot == "auto" else Path(args.plot))
                plot_result(data, image_path)
        payload = outputs if multiple else outputs[0]
        if args.summary or args.application == "verify":
            payload = [{"application": o["application"], "passed": o["passed"], "checks": o["checks"]}
                       for o in outputs]
        print(json.dumps(payload, indent=2, allow_nan=False))
        return 0 if all(o["passed"] for o in outputs) else 1
    except ImportError as exc:
        parser.error(f"{exc}; install the optional applications dependencies: pip install '.[applications]'")
    except (ValueError, ArithmeticError) as exc:
        parser.error(str(exc))
    return 2

if __name__ == "__main__":
    sys.exit(main())
