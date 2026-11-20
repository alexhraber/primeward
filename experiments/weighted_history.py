#!/usr/bin/env python3
"""Past-only empirical test of a weighted prime-successor state.

This is a predictor experiment, not a prime generator or an exact algorithm.
An independent Eratosthenes sieve supplies ground truth. No claimed speedup
includes or hides the cost of generating that truth, features, or training.

Run from any directory:
    python3 experiments/weighted_history.py --output results

Dependencies: numpy, scipy, scikit-learn. All hyperparameters and magnitude
boundaries are specified before evaluating the test and distant blocks.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import time
from pathlib import Path

import numpy as np
import sklearn
from sklearn.ensemble import ExtraTreesClassifier


SMALL_PRIMES = (2, 3, 5, 7, 11, 13)
WINDOWS = (8, 16, 32, 64, 128)
SPLITS = {
    "train": (1_000, 600_000),
    "validation": (600_000, 800_000),
    "test": (800_000, 1_100_000),
    "distant": (1_600_000, 2_000_001),
}


def sieve(limit: int) -> tuple[np.ndarray, np.ndarray]:
    flags = np.ones(limit + 1, dtype=np.bool_)
    flags[:2] = False
    for p in range(2, math.isqrt(limit) + 1):
        if flags[p]:
            flags[p * p :: p] = False
    return flags, np.flatnonzero(flags).astype(np.int64)


def arithmetic_prefixes(limit: int, primes: np.ndarray) -> dict[str, np.ndarray]:
    """Every entry at n is calculated solely from arithmetic at or below n."""
    mangoldt = np.zeros(limit + 1, dtype=np.float64)
    omega = np.zeros(limit + 1, dtype=np.float64)
    for p_raw in primes:
        p = int(p_raw)
        if p > limit:
            break
        omega[p::p] += 1
        power = p
        weight = math.log(p)
        while power <= limit:
            mangoldt[power] = weight
            power *= p
    index = np.arange(limit + 1, dtype=np.float64)
    return {
        "lambda": np.cumsum(mangoldt),
        "index_lambda": np.cumsum(index * mangoldt),
        "omega": np.cumsum(omega),
        "index_omega": np.cumsum(index * omega),
    }


def feature_sets(primes: np.ndarray, limit: int) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], dict[str, list[str]]]:
    indices = np.flatnonzero((primes >= 1_000) & (primes <= limit))
    # The extra ground-truth tail guarantees each label exists.
    current = primes[indices]
    labels = primes[indices + 1] - current
    logs = np.log(current)
    base = np.column_stack([logs]).astype(np.float32)
    base_names = ["log_current_prime"]

    residues = np.column_stack([current % q for q in SMALL_PRIMES[1:]])
    # Prospective divisibility by already known small primes is legitimate.
    # These are not primality labels, and numbers with larger factors survive.
    offsets = np.arange(2, 66, 2)
    alive = np.ones((len(current), len(offsets)), dtype=np.bool_)
    for q in SMALL_PRIMES[1:]:
        alive &= (current[:, None] + offsets[None, :]) % q != 0
    residue = np.column_stack([base, residues, alive]).astype(np.float32)
    residue_names = base_names + [f"current_mod_{q}" for q in SMALL_PRIMES[1:]] + [f"small_prime_survivor_offset_{d}" for d in offsets]

    lag_count = 32
    # lag one is current minus preceding prime; never includes the label gap.
    lags = np.column_stack([primes[indices - j] - primes[indices - j - 1] for j in range(lag_count)]).astype(np.float64)
    normalized_lags = lags / logs[:, None]
    history_columns = [normalized_lags]
    history_names = [f"preceding_gap_{j + 1}_over_log_current" for j in range(lag_count)]
    for count in (4, 8, 16, 32):
        x = normalized_lags[:, :count]
        old_heavy = np.arange(1, count + 1, dtype=np.float64)
        recent_heavy = old_heavy[::-1]
        decaying = np.exp(-np.arange(count) / max(1, count / 4))
        out = np.column_stack([
            x.mean(axis=1), x.std(axis=1),
            x @ old_heavy / old_heavy.sum(),
            x @ recent_heavy / recent_heavy.sum(),
            x @ decaying / decaying.sum(),
        ])
        history_columns.append(out)
        history_names.extend([f"past_{count}_gaps_{name}" for name in ("mean", "std", "older_linear_weight", "recent_linear_weight", "exponential_weight")])

    prefixes = arithmetic_prefixes(limit, primes)
    for width in WINDOWS:
        for name in ("lambda", "omega"):
            total = prefixes[name][current] - prefixes[name][current - width]
            index_total = prefixes["index_" + name][current] - prefixes["index_" + name][current - width]
            # At current: weight one; each integer step backward adds one.
            weighted = (current + 1) * total - index_total
            scaling = logs if name == "lambda" else np.ones_like(logs)
            history_columns.append(np.column_stack([
                total / (width * scaling),
                weighted / ((width * (width + 1) / 2) * scaling),
            ]))
            history_names.extend([f"preceding_{width}_integers_{name}_mean", f"preceding_{width}_integers_{name}_older_linear_weight"])
    history = np.column_stack([residue] + history_columns).astype(np.float32)
    return current, labels, {"position": base, "residue_state": residue, "residue_plus_history": history}, {
        "position": base_names,
        "residue_state": residue_names,
        "residue_plus_history": residue_names + history_names,
    }


def score(model: ExtraTreesClassifier, features: np.ndarray, current: np.ndarray, actual: np.ndarray, mask_impossible: bool) -> tuple[dict[str, float | int], np.ndarray, np.ndarray]:
    probabilities = model.predict_proba(features)
    classes = model.classes_.astype(np.int64)
    if mask_impossible:
        for q in SMALL_PRIMES[1:]:
            probabilities[(current[:, None] + classes[None, :]) % q == 0] = 0
    ranked = np.argsort(-probabilities, axis=1, kind="stable")
    predicted = classes[ranked[:, 0]]
    top5 = classes[ranked[:, :5]]
    result = {
        "count": int(len(actual)),
        "exact_accuracy": float(np.mean(predicted == actual)),
        "mean_absolute_gap_error": float(np.mean(np.abs(predicted - actual))),
        "top5_gap_recall": float(np.mean(np.any(top5 == actual[:, None], axis=1))),
        "unseen_gap_class_fraction": float(np.mean(~np.isin(actual, classes))),
        "all_class_probabilities_zero_fraction": float(np.mean(probabilities.sum(axis=1) == 0)),
    }
    return result, predicted, top5


def first_survivor(current: np.ndarray, actual: np.ndarray) -> tuple[dict, np.ndarray, np.ndarray]:
    """Elementary control: choose the earliest small-prime sieve survivor.

    This is not an exact next-prime rule. Multiples of larger primes survive.
    The fixed 256-offset window suffices for five survivors in this experiment;
    the assertion makes that assumption visible rather than silently falling back.
    """
    offsets = np.arange(2, 258, 2)
    valid = np.ones((len(current), len(offsets)), dtype=np.bool_)
    for q in SMALL_PRIMES[1:]:
        valid &= (current[:, None] + offsets[None, :]) % q != 0
    assert np.all(valid.sum(axis=1) >= 5)
    ranking = np.argsort(~valid, axis=1, kind="stable")[:, :5]
    top5 = offsets[ranking]
    predicted = top5[:, 0]
    return {
        "count": int(len(actual)),
        "exact_accuracy": float(np.mean(predicted == actual)),
        "mean_absolute_gap_error": float(np.mean(np.abs(predicted - actual))),
        "top5_gap_recall": float(np.mean(np.any(top5 == actual[:, None], axis=1))),
        "unseen_gap_class_fraction": 0.0,
        "all_class_probabilities_zero_fraction": 0.0,
    }, predicted, top5


def paired_block_interval(actual: np.ndarray, left: np.ndarray, right: np.ndarray) -> dict:
    """Exploratory uncertainty from resampling contiguous 256-row blocks."""
    difference = (left == actual).astype(np.int8) - (right == actual).astype(np.int8)
    starts = np.arange(0, len(difference), 256)
    totals = np.add.reduceat(difference, starts)
    counts = np.minimum(256, len(difference) - starts)
    rng = np.random.default_rng(20261120)
    draws = rng.integers(0, len(starts), size=(2000, len(starts)))
    samples = totals[draws].sum(axis=1) / counts[draws].sum(axis=1)
    return {
        "accuracy_difference": float(difference.mean()),
        "exploratory_block_bootstrap_95_percent_interval": np.quantile(samples, [0.025, 0.975]).tolist(),
        "block_size": 256,
        "resamples": 2000,
        "left_only_correct": int(np.sum(difference == 1)),
        "right_only_correct": int(np.sum(difference == -1)),
        "caution": "One dataset and fixed fitted models; exploratory block bootstrap does not establish generalization to arbitrary magnitude.",
    }


def check_future_independence() -> dict:
    """Changing all future values must change a label but no input feature."""
    _, primes = sieve(2_000)
    prefix = primes[primes <= 1_009]
    real = np.concatenate([prefix, primes[primes > 1_009]])
    corrupted = np.concatenate([prefix, np.arange(1_010, 1_050)])
    locations, actual, real_features, _ = feature_sets(real, 1_009)
    _, changed, changed_features, _ = feature_sets(corrupted, 1_009)
    report = {
        "check": "Replace every value after the current-prime cutoff with deliberately false future data. Past-only feature matrices must remain unchanged while the final successor label changes.",
        "cutoff": 1_009,
        "all_features_unchanged": all(np.array_equal(real_features[key], changed_features[key]) for key in real_features),
        "last_label_changed": bool(actual[-1] != changed[-1]),
        "true_last_gap": int(actual[-1]),
        "corrupted_last_gap": int(changed[-1]),
        "row_count": int(len(locations)),
    }
    assert report["all_features_unchanged"] and report["last_label_changed"]
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    parser.add_argument("--trees", type=int, default=48)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    _, primes = sieve(2_001_000)
    sieve_seconds = time.perf_counter() - started
    feature_started = time.perf_counter()
    current, labels, sets, feature_names = feature_sets(primes, 2_000_000)
    for name, features in sets.items():
        assert features.shape[1] == len(feature_names[name])
        assert np.all(np.isfinite(features))
    feature_seconds = time.perf_counter() - feature_started
    masks = {name: (current >= lower) & (current < upper) for name, (lower, upper) in SPLITS.items()}
    results = {
        "description": "Chronological, past-only next-prime-gap prediction; not an exact successor algorithm.",
        "seed": 20261120,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "sklearn": sklearn.__version__},
        "split_boundaries": SPLITS,
        "split_counts": {name: int(mask.sum()) for name, mask in masks.items()},
        "sieve_seconds": sieve_seconds,
        "feature_seconds": feature_seconds,
        "features": feature_names,
        "selection_rule": "Choose min_samples_leaf from 16 or 64 by validation exact accuracy; ties choose 64. All other hyperparameters fixed. Refit on train only; no validation or test labels added.",
        "models": {},
        "leakage_check": check_future_independence(),
        "limitations": [
            "Data are consecutive primes only within the stated range, not a proof about all primes.",
            "Ground-truth sieving and arithmetic-history feature costs are real setup costs, not eliminated discovery work.",
            "Predictions do not certify primality or that a smaller prime was not skipped.",
            "No model can output a gap class absent from training; the unseen-label rate is reported.",
            "The test data were not used for feature design, hyperparameter selection, or fitting.",
            "Farther holdout changes numerical scale only modestly; it is not validation at cryptographic sizes.",
            "Scores are one-step forecasts supplied with the true current prime and true past arithmetic history; they do not describe repeated autonomous rollout of the predictor's own outputs.",
            "Arbitrary-start initialization of the required preceding thirty-two primes and factor information is not solved by this experiment.",
            "Small-prime masking uses only divisibility rules for already known primes, not ground-truth primality.",
            "The elementary first-survivor comparator was added after the initial exploratory run to audit whether a fitted predictor beats simple known arithmetic; no feature, model hyperparameter, or fit was revised in response to test scores. These remain exploratory holdouts, not a preregistered confirmatory study.",
        ],
    }
    prediction_rows: dict[str, list] = {}
    train_mode = int(np.bincount(labels[masks["train"]]).argmax())
    results["constant_training_mode"] = {
        "gap": train_mode,
        **{name: {"exact_accuracy": float(np.mean(labels[mask] == train_mode)), "mean_absolute_gap_error": float(np.mean(np.abs(labels[mask] - train_mode)))} for name, mask in masks.items() if name != "train"},
    }
    for name, features in sets.items():
        candidates = []
        for leaf in (64, 16):
            model = ExtraTreesClassifier(n_estimators=args.trees, min_samples_leaf=leaf, max_depth=18, max_features=1.0, n_jobs=args.jobs, random_state=20261120)
            start = time.perf_counter()
            model.fit(features[masks["train"]], labels[masks["train"]])
            fit_seconds = time.perf_counter() - start
            validation, _, _ = score(model, features[masks["validation"]], current[masks["validation"]], labels[masks["validation"]], name != "position")
            candidates.append((validation["exact_accuracy"], leaf, model, fit_seconds, validation))
            print(json.dumps({"stage": "validation", "model": name, "min_samples_leaf": leaf, "fit_seconds": fit_seconds, **validation}), flush=True)
        winner = max(candidates, key=lambda item: (item[0], item[1]))
        _, leaf, model, fit_seconds, validation = winner
        entry = {"selected_min_samples_leaf": leaf, "trees": args.trees, "feature_count": features.shape[1], "fit_seconds": fit_seconds, "validation": validation, "validation_candidates": [{"leaf": item[1], "fit_seconds": item[3], **item[4]} for item in candidates]}
        for split in ("test", "distant"):
            mask = masks[split]
            start = time.perf_counter()
            scores, predicted, top5 = score(model, features[mask], current[mask], labels[mask], name != "position")
            scores["inference_seconds"] = time.perf_counter() - start
            entry[split] = scores
            prediction_rows[f"{name}_{split}"] = [current[mask], labels[mask], predicted, top5]
            print(json.dumps({"stage": split, "model": name, **scores}), flush=True)
        entry["top_features"] = sorted(zip(feature_names[name], model.feature_importances_.tolist()), key=lambda pair: pair[1], reverse=True)[:20]
        results["models"][name] = entry

    control = {"description": "Earliest survivor of division by known primes up to thirteen; no fitting or history weights.", "fit_seconds": 0.0}
    for split in ("validation", "test", "distant"):
        mask = masks[split]
        start = time.perf_counter()
        metrics, predicted, top5 = first_survivor(current[mask], labels[mask])
        metrics["inference_seconds"] = time.perf_counter() - start
        control[split] = metrics
        if split != "validation":
            prediction_rows[f"first_survivor_{split}"] = [current[mask], labels[mask], predicted, top5]
    results["models"]["first_survivor"] = control
    results["paired_comparisons"] = {}
    for split in ("test", "distant"):
        actual = prediction_rows[f"residue_plus_history_{split}"][1]
        history = prediction_rows[f"residue_plus_history_{split}"][2]
        for baseline in ("residue_state", "first_survivor"):
            other = prediction_rows[f"{baseline}_{split}"][2]
            results["paired_comparisons"][f"history_minus_{baseline}_{split}"] = paired_block_interval(actual, history, other)

    (args.output / "history_results.json").write_text(json.dumps(results, indent=2) + "\n")
    (args.output / "history_leakage_check.json").write_text(json.dumps(results["leakage_check"], indent=2) + "\n")
    with (args.output / "history_metrics.csv").open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["model", "split", "count", "exact_accuracy", "mean_absolute_gap_error", "top5_gap_recall", "unseen_gap_class_fraction", "inference_seconds"])
        for name, entry in results["models"].items():
            for split in ("validation", "test", "distant"):
                metrics = entry[split]
                writer.writerow([name, split] + [metrics.get(field, "") for field in ("count", "exact_accuracy", "mean_absolute_gap_error", "top5_gap_recall", "unseen_gap_class_fraction", "inference_seconds")])
    with (args.output / "history_predictions.csv").open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["model", "split", "current_prime", "actual_next_gap", "predicted_next_gap", "top_five_gap_predictions"])
        for key, (locations, actual, predicted, top5) in prediction_rows.items():
            name, split = key.rsplit("_", 1)
            for values in zip(locations, actual, predicted, top5):
                p, true_gap, guess, ranked = values
                writer.writerow([name, split, int(p), int(true_gap), int(guess), " ".join(map(str, ranked))])
    (args.output / "history_notes.txt").write_text(
        "Purpose: test whether weighted arithmetic history adds predictive information beyond position and small-prime divisibility.\n"
        "This prediction experiment begins above one thousand to supply complete history windows and does not exercise a start at one. In its arithmetic representation, one has zero logarithmic prime-power weight and zero distinct prime factors.\n"
        "All features use the current prime, fixed small primes, or numbers at or below the current prime. Labels alone use the next prime. Current-prime membership in the ground-truth list is known at prediction time.\n"
        "Chronological blocks are fixed in the script. Gaps in numerical coverage separate the distant holdout. Hyperparameters are selected solely on validation. No feature, model hyperparameter, or fit was revised after test inspection. An elementary first-survivor control and exploratory paired uncertainty were added after the initial run to check the apparent small history gain against a stronger baseline. This is an exploratory study.\n"
        "A source sieve creates data; a second pass derives arithmetic prefixes. Neither is claimed to be avoided by the experimental model. Past lambda and prime-factor features could be maintained incrementally, but those update costs are not benchmarked here.\n"
        "The reported forecasts are one step at a time, supplied with the true current prime and true past history. They do not evaluate repeated rollout using erroneous model outputs. Constructing that history at an arbitrary large initial prime remains additional work.\n"
        "Exact accuracy is the fraction of immediate successors predicted correctly. Top-five recall reports whether one of five proposed gaps matches; it does not certify a successor. Mean absolute error is in integer positions.\n"
        "History features include thirty-two preceding prime gaps, equal/linear/exponential weighted summaries, and preceding-integer windows of logarithmic prime-power weights and distinct-prime-factor counts. Linear old-heavy weights increase by one for each step back, as proposed in the conversation.\n"
        "Position-only uses no divisibility filter. Both arithmetic models mask predictions inconsistent with divisibility by three, five, seven, eleven, or thirteen. This gives the main residue-versus-history comparison identical masking.\n"
        "A finite improvement would be empirical evidence for this representation only. Failure would not prove that no exact recurrence exists. Both outcomes remain distinct from a proof of an exact general successor rule.\n"
    )
    print(json.dumps({"done": True, "total_seconds": time.perf_counter() - started, "output": str(args.output)}), flush=True)


if __name__ == "__main__":
    main()
