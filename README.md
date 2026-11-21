# Primeward

Research into exact prime succession through reusable arithmetic state.

Version 0.2.0.

This package makes the proposed stateful prime-successor project executable and
testable. The analytic engine computes exact immediate successors from a
reusable numerical state. A finite mathematical bound and enclosing arithmetic
justify the result. Its initialization and precision are expensive; an efficient
general successor breakthrough has not been established.

The construction does not depend on the Riemann Hypothesis.

## Physics applications

Eight finite physics experiments live in [applications/](applications/README.md): primon thermodynamics, spectral recovery with bounded uncertainty, prime-position scattering, one-dimensional wave transport, inverse quantum spectra, a thermal form factor, smoothed prime-orbit sums and a paired charged gas.

Install the optional scientific dependencies with Python 3.11 or newer:

```bash
python -m pip install '.[applications]'
python -m applications list
python -m applications run-all --output-dir /tmp/primeward-applications --plot --summary
```

Each result records its model, input primes, numerical checks and limitations. The default source is the certified residual engine; select `--prime-method bytearray` explicitly for larger finite populations. These examples do not change the existing sieve-performance comparison. See the [application guide](applications/README.md) and [recorded examples](applications/examples/README.md).

Development is governed by the initialized Decapod project. Its living specifications describe the core and application contracts, and `decapod validate` owns the required local checks.

## What is included

- `prime_successor/fast_analytic.py`: residual-state engine with a smaller
  exponent, an interval check for epoch reuse, and reduced transition precision.
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
- `experiments/benchmark_successors.py`: comparisons with paid initialization,
  a following warm batch, and several sieve block sizes. FLINT caches are
  cleared between fresh runs by default.
- `research/fast_analytic_theory.md`: proofs of the sharper odd-tail bound,
  the epoch acceptance check, and the residual update.
- `research/theory_review.md`: the invariant, finite extraction proof,
  nearest-odd conditioning argument, and limitations, written in English.
- `research/findings.txt`: the complete research findings, measured comparisons,
  validation record, and research targets from the initial version.
- `research/performance.md`: version 0.2 measurements and remaining costs.
- `results/`: measured results and raw predictions. Timings are observations
  from the recorded environment, not portable performance guarantees.
- `tests/`: independent arithmetic comparisons, boundary cases, resource-limit
  refusal, and checkpoint validation.

## Run the exact analytic recurrence

Use a Python virtual environment if desired, then install the small analytic
dependency and run from this directory:

```sh
python3 -m pip install -r requirements.txt
python3 -m prime_successor --method residual --start 113 --count 10 --json
```

The successors are 127, 131, 137, 139, 149, 151, 157, 163, 167, and 173.
The last enclosure and all work counters are included in JSON output.

The residual engine is the default. Use `--method analytic` for the original
implementation or `--method optimized` for the first mixed-precision version.
All three calculate exact successors
from the same Euler-product identity and check numerical enclosures before
accepting an answer.

Start at the multiplicative identity:

```sh
python3 -m prime_successor --method residual --start 1 --count 20
```

One is represented explicitly and is never called prime. The analytic unit
state computes two. Once the current prime is at least two, a mathematically
justified nearest-odd rounding rule improves numerical stability.

For a separate small-input correctness check, add `--verify`. That option runs
an independent trial-division successor search after the analytic calculation;
its verification work is deliberately not part of the analytic engine itself.

## Measured performance

The residual engine is 4.3–20.9 times faster than the previous optimized
implementation on the four workloads below, including initialization and any
rebuilds during the requested batch. It still takes more time than the sieve.

| Starting value | Successors | Previous optimized | Residual | Fastest compared sieve |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 200 | 27.722 ms | 5.472 ms | 0.196 ms |
| 113 | 100 | 10.427 ms | 2.410 ms | 0.110 ms |
| 997 | 30 | 27.128 ms | 2.388 ms | 0.064 ms |
| 10,007 | 10 | 3,460.858 ms | 165.821 ms | 0.061 ms |

These are medians of five runs on the recorded machine. Each run creates a
fresh engine after clearing FLINT's internal caches. The sieve comparison
uses the fastest measured setting among 64, 512, and 4,096 odd candidate slots
in this repository's bytearray implementation. Every output was compared with
an independent sieve outside the timers.

Longer runs still pay for rebuilding the analytic state. Starting at 10,007
and producing 2,000 successors took a median 1.100 seconds, against 0.001739
seconds for the fastest compared sieve. See [the performance report](research/performance.md)
for phase timings, numerical-state sizes, and reproduction commands.

## Reproduce the work

```sh
python3 -m unittest discover -s tests -v
python3 -m experiments.benchmark_successors --repeats 5
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

The residual engine stores this small remainder directly. If `R` is the
remainder, `q` the newly extracted prime, and `s` the exponent, its update is
`R - q**(-s) - R*q**(-s)`. This avoids carrying the unit term through every
transition at the high precision required to distinguish the remainder from it.

Within an exponent epoch, the zeta value is reused. The residual engine checks
a bound on the remaining tail to determine whether the exponent still suffices.
When the check no longer certifies a successor, the state is rebuilt with a
larger exponent or more precision. That rebuild is charged to advancing time.

The wrapper performs no primality tests on future candidates in an analytic
transition. The numerical library still performs substantial arithmetic to
evaluate special functions and powers. All that time is included.

## What remains unresolved

Initialization currently constructs all primes up to the input prime. A start
at an arbitrary large prime therefore has a large hidden history requirement
unless that history is explicitly supplied or a new initialization method is
found. This version charges for generating it and documents the requirement.

The remainder carrying the successor is extremely small. Full initialization
still needs precision roughly proportional to the numerical location times
its logarithm. The residual engine reduces the precision used for subsequent
updates, but retains the complete prime prefix and pays for rebuilding the
Euler product. These costs remain obstacles to an efficient recurrence.

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

## Record-scale successor experiment

The [record experiment](research/record_successor.md) ran the actual M136279841 input through the existing constructor on GitHub Actions. It stopped at the seed limit and produced no successor for that target. The same run certified 31 → 37, 127 → 131 and 8191 → 8209. The harness, original reports and initialization analysis are included; the current complete-prefix initialization cannot reach the record scale.
