# Residual-engine performance

Version 0.2 adds `ResidualAnalyticSuccessor` (`FastAnalyticSuccessor` is the
same class) and makes it the CLI default. It improves the existing analytic
construction. It does not beat the compared sieve implementations.

## What changed

The engine stores the residual `R = F - 1` instead of the near-one Euler
product `F`. After extracting `q`, it updates that residual using
`R - q**(-s) - R*q**(-s)`. The update preserves the Euler-product identity
while using fewer relative precision bits.

The new odd-tail bound permits a smaller exponent. Initialization chooses
the least even integer at least `p + 2`, compared with the original `4*p`.
Before decoding a successor, an interval comparison proves that the
unknown next prime lies inside the exponent's valid range. A failed check
causes a rebuild or a precision increase. The
[proof note](fast_analytic_theory.md) gives the inequalities and assumptions.

Precision estimates use enclosing logarithms. Euler corrections are rounded
to their required precision before multiplication. Transition precision
follows the accuracy still present in the residual. Diagnostic decimal
strings are generated when requested, while the interval checks remain in
every successor calculation.

No future candidate primality test or sieve was added to the analytic
transition. Initialization still generates the complete preceding prime
prefix. Rebuilds use that accepted history.

## Measurement procedure

The recorded environment used Python 3.12.14 and python-flint 0.9.0 on Linux
x86-64, with one FLINT thread. Full environment details, source hashes, all
raw samples, phase counters, and output hashes are in the JSON reports.

Each method was run five times per workload. Each repetition constructed a
fresh engine, generated the requested first batch, and then generated a
second, distinct batch from the retained state. Engine order rotated between
repetitions. `ctx.cleanup()` cleared internal MPFR/FLINT/Arb caches before
each fresh run, outside the timers, so another method could not supply a
precomputed library cache.

Initialization, transitions, epoch rebuilds, and built-in numerical checks
are timed. Imports, report generation, garbage collection before a run,
decimal formatting of unrequested diagnostics, and independent verification
are excluded. This does not measure Python process startup or reset operating
system caches. The previous implementations retain their existing eager
diagnostic formatting, so avoiding that work is part of the measured change.

Every returned value was compared with a separate ordinary sieve, whose
answers were never supplied to the measured engines. Bytearray controls
used 64, 512, and 4,096 odd slots per block. Each comparison below selects the
fastest measured setting for its workload. These are the repository's Python
sieves; native prime-generation libraries were not measured.

## Initialization plus first batch

All durations below are milliseconds. Speedup uses the previous optimized
implementation, not the slower original implementation.

| Start | Count | Original | Previous optimized | Residual | Speedup | Fastest compared sieve |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 200 | 54.200 | 27.722 | 5.472 | 5.07x | 0.196 |
| 113 | 100 | 17.285 | 10.427 | 2.410 | 4.33x | 0.110 |
| 997 | 30 | 55.684 | 27.128 | 2.388 | 11.36x | 0.064 |
| 10,007 | 10 | 8,240.011 | 3,460.858 | 165.821 | 20.87x | 0.061 |

The 512-slot sieve had the lowest median first-batch total in all four cases.
The original-to-residual speedup at 10,007 was 49.69x. Neither comparison is
an advantage over the sieve: even the new engine's 165.821 ms first-batch
total was about 2,701 times the 0.061382 ms sieve result for that workload.

Source: [successor_benchmarks.json](../results/successor_benchmarks.json).

## Following batch from retained state

Each following batch has the same count as its first batch and begins at the
last returned prime. Times include any epoch rebuild or sieve-block refill
that occurs during that batch. Initialization has already been paid, so these
figures must not be used as the cost of entry at an arbitrary prime.

| Initial seed | Following count | Previous optimized | Residual | Fastest compared sieve |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 200 | 359.479 ms | 7.090 ms | 0.145 ms |
| 113 | 100 | 35.822 ms | 2.581 ms | 0.071 ms |
| 997 | 30 | 7.944 ms | 0.254 ms | 0.022 ms |
| 10,007 | 10 | 64.065 ms | 0.454 ms | 0.008 ms |

At 10,007, the following ten outputs took about 141 times less time than the
previous optimized engine, but remained about 57 times slower than the
fastest compared sieve. This short continuation did not require an epoch
rebuild; the longer run below shows its cost.

## Longer sequence and rebuild cost

A separate five-repeat comparison started at 10,007 and produced 2,000
successors. The first thousand ended at 19,699; the following thousand ended
at 29,819. The second batch crossed an analytic epoch boundary.

| Timed scope | Residual | Fastest compared sieve |
| --- | ---: | ---: |
| Initialization plus first 1,000 outputs | 194.675 ms | 0.861 ms |
| Following 1,000 outputs, including rebuild | 908.818 ms | 0.864 ms |
| Entire 2,000-output session | 1,099.794 ms | 1.739 ms |

The 4,096-slot sieve was fastest in these comparisons. Medians are computed
independently for each scope, so the displayed phase medians need not add
exactly to the median session total.

Source: [residual_stream_benchmarks.json](../results/residual_stream_benchmarks.json).

## Precision and retained state

After the first ten outputs from 10,007:

| State measurement | Previous optimized | Residual |
| --- | ---: | ---: |
| Full initialization precision | 640,704 bits | 143,289 bits |
| Stored numeric midpoint | 640,703 bits | 10,155 bits |
| Stored past primes | 1,240 | 1,240 |
| Python prime-history size estimate | 44,728 bytes | 44,728 bytes |

The stored midpoint is about 63 times smaller. This is a measurement of that
numeric component, not total memory or peak allocation. It excludes the
interval radius, retained diagnostic balls, temporary arithmetic, interpreter,
and the unchanged prime history. The residual's configured relative precision
was 10,298 bits; individual updates can use fewer bits as accuracy is consumed.

## Remaining cost

In the first recorded residual run at 10,007, initialization took 165.352 ms.
Of that, Euler-product construction took 143.278 ms and zeta evaluation took
21.715 ms. The next ten transitions took 0.451 ms. Constructing and later
rebuilding the state still dominates this workload.

The results support reducing the cost of the existing formula. They do not
establish a faster general prime generator, a new prime theorem, or a
smaller asymptotic bound. A further attempt to beat the sieve needs a cheaper
way to construct and refresh the state, in addition to cheaper transitions.

## Reproduce

From the repository root after installing `requirements.txt`:

```sh
python3 -m unittest discover -s tests -v
python3 -m experiments.benchmark_successors --repeats 5
python3 -m experiments.benchmark_successors \
  --methods residual,sieve-64,sieve-512,sieve-4096 \
  --cases 10007:1000:1000 --repeats 5 \
  --output results/residual_stream_benchmarks.json
```

The full test run passed 35 tests, including nine new residual-engine tests.
The CLI default also returned the ten independently verified successors of
113. Records are in [residual_validation.json](../results/residual_validation.json)
and [residual_cli_smoke.json](../results/residual_cli_smoke.json).

The source hashes in the benchmark reports identify the measured Python files.
The reports were generated before this commit, so their Git field records the
base commit and the modified worktree; the file hashes bind the measurements
to the implementation published with these results.
