# Primeward

Research into exact prime succession through reusable arithmetic state.

Version 0.1. Research snapshot prepared on November 20, 2026.

This package makes the proposed stateful prime-successor project executable and
testable. The analytic engine computes exact immediate successors from a
reusable numerical state. A finite mathematical bound and enclosing arithmetic
justify the result. Its initialization and precision are expensive; an efficient
general successor breakthrough has not been established.

The construction does not depend on the Riemann Hypothesis.

## What is included

- `prime_successor/analytic.py`: finite Euler-product extraction, explicit unit
  state, numerical enclosure checks, epoch updates, and cost counters.
- `prime_successor/optimized.py`: the same exact rule with less precision spent
  on tiny correction terms and on the final integer decoding.
- `prime_successor/engine.py`: exact stateful segmented-sieve baselines and
  scalar successor baselines, with explicit unsigned-64-bit boundaries.
- `experiments/weighted_history.py`: chronological tests of weighted arithmetic
  history, including a weight that increases by one with each backward step.
- `experiments/benchmark.py`: exact-engine timings, separately charging
  initialization and subsequent advances.
- `research/theory_review.md`: the invariant, finite extraction proof,
  nearest-odd conditioning argument, and limitations, written in English.
- `research/findings.txt`: the complete research findings, measured comparisons,
  validation record, and next research targets in plain English.
- `results/`: measured results and raw predictions. Timings are observations
  from the recorded environment, not portable performance guarantees.
- `tests/`: independent arithmetic comparisons, boundary cases, resource-limit
  refusal, and checkpoint validation.

## Run the exact analytic recurrence

Use a Python virtual environment if desired, then install the small analytic
dependency and run from this directory:

```sh
python3 -m pip install -r requirements.txt
python3 -m prime_successor --method analytic --start 113 --count 10 --json
```

The successors are 127, 131, 137, 139, 149, 151, 157, 163, 167, and 173.
The last enclosure and all work counters are included in JSON output.

Use `--method optimized` for the measured mixed-precision variant. It retains
the same mathematical invariant and enclosing arithmetic acceptance checks.

Start at the multiplicative identity:

```sh
python3 -m prime_successor --method analytic --start 1 --count 20
```

One is represented explicitly and is never called prime. The analytic unit
state computes two. Once the current prime is at least two, a mathematically
justified nearest-odd rounding rule improves numerical stability.

For a separate small-input correctness check, add `--verify`. That option runs
an independent trial-division successor search after the analytic calculation;
its verification work is deliberately not part of the analytic engine itself.

## Reproduce the work

```sh
python3 -m unittest discover -s tests -v
python3 -m experiments.benchmark --repeats 3
python3 -m experiments.benchmark_optimized --repeats 3
```

For the history experiment, install its separate dependencies. The recorded
environment used Python 3.12.14, NumPy 2.3.5, and scikit-learn 1.8.0.

```sh
python3 -m pip install -r requirements-experiments.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -m experiments.weighted_history
```

The predictor experiment reports one-step forecasts supplied with true past
history. It is not an exact generator. It selects model settings on validation
data and evaluates later chronological ranges. Its raw labels come from an
independent sieve; those preparation costs are disclosed. The elementary
first-survivor control was added after the exploratory first run, and this is
recorded in the results. No fitted model was tuned against the holdout scores.

## What the exact state means

The numerical state represents a weighted sum of positive integers after the
prime factors already accounted for have been removed. One is the explicit unit
term. The smallest remaining integer beyond that unit is the immediate next
prime. A finite root extraction recovers it with a certified rounding interval.
One additional Euler factor then incorporates that prime into the state.

Within an exponent epoch, the zeta value is reused. At an epoch boundary, the
exponent and state are rebuilt. That rebuild is charged to advancing time.

The wrapper performs no primality tests on future candidates in an analytic
transition. The numerical library still performs substantial arithmetic to
evaluate special functions and powers. All that time is included.

## What remains unresolved

Initialization currently constructs all primes up to the input prime. A start
at an arbitrary large prime therefore has a large hidden history requirement
unless that history is explicitly supplied or a new initialization method is
found. This version charges for generating it and documents the requirement.

The remainder carrying the successor is extremely small. The arithmetic
precision grows roughly with the numerical location times its logarithm for
this conservative construction. A single numerical variable can therefore
contain a huge number of bits. This is the main obstacle to the desired compact,
efficient recurrence.

The default analytic seed and precision limits are research resource limits.
The exact sieve and Miller-Rabin baselines have explicit unsigned-64-bit or
small-prime-table limits. Exceeding a limit raises an error, never a guessed
successor.

Sieve checkpoint restoration revalidates the current prime and reconstructs
arithmetic caches. It preserves the successor sequence but does not claim a
cost-free restore of every cached bit.

Numerical enclosure records are diagnostic outputs. They are not independent
theorem-prover certificates. Correctness rests on the supplied mathematical
argument, complete initialization, and FLINT/Arb's enclosing arithmetic.

## Attribution and claim boundary

The analytic family is established research, especially Solomon W. Golomb's
1976 paper *Formulas for the next prime*. This package implements and studies a
finite extraction argument and state update; it makes no priority claim for
that argument or a new discovery of prime succession.

- Golomb: https://msp.org/pjm/1976/63-2/pjm-v63-n2-p11-p.pdf
- Kawalec: https://arxiv.org/abs/2009.02640
- Sorenson, incremental sieve algorithms:
  https://www.cambridge.org/core/journals/lms-journal-of-computation-and-mathematics/article/two-compact-incremental-prime-sieves/8C93ED669EABD7C3074BD44BC487747F
- FLINT ball arithmetic:
  https://flintlib.org/doc/guide/types/ball-arithmetic.html
- Python bindings: https://python-flint.readthedocs.io/en/stable/arb.html

The next research target is reducing the information and precision needed to
initialize, update, and decode the exact state. The weighted-history experiment
tests one proposed compression route and records both successes and failures.
