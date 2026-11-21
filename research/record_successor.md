# Record-scale successor experiment

The target is the immediate prime after p = 2^136279841 - 1. The experiment uses the existing `FastAnalyticSuccessor`; it does not substitute a search for another Mersenne prime.

## Observed GitHub Actions run

[Run 44870723187](https://github.com/alexhraber/primeward/actions/runs/44870723187) executed the target probe and the separate calibration job at commit [0893e804](https://github.com/alexhraber/primeward/commit/0893e80426b5f32fc898acc46fc8b8f3dcf6f614). Both jobs completed. **No successor was produced for the record target.**

The target job constructed the actual 136,279,841-bit integer and passed it to the existing analytic constructor. The constructor returned `start exceeds the explicit max_seed limit` before initializing the residual. The report records `blocked_max_seed`, `successor: null` and `successor_certified: false`. The Python input object occupied 18,170,672 bytes; the bounded worker took about 0.084 seconds including process startup. This run did not re-prove primality of the starting record.

The same analytic engine produced these calibration results, independently checked by trial division for primality and minimality:

| Starting prime | Immediate successor | Initial precision (bits) | Initialization time (seconds) | Advance time (seconds) |
| --- | --- | --- | --- | --- |
| 31 | 37 | 461 | 0.000275 | 0.000032 |
| 127 | 131 | 1,297 | 0.000364 | 0.000024 |
| 8,191 | 8,209 | 114,973 | 0.073734 | 0.000046 |

These are single-run timings on GitHub-hosted runners, not performance estimates for the record input. The engine tested zero future candidates; the independent verifier did test candidates.

The original machine-readable reports are committed as [target.json](record_successor_runs/44870723187/target.json) and [calibration.json](record_successor_runs/44870723187/calibration.json). They retain the exact source commit and hashes, resource bounds, counters and interval certificates. Reports are historical observations at that source commit; a green job means the experiment completed, not that a record successor was found.

The run used a temporary work-branch workflow with separate target and calibration jobs. Each job had a five-minute limit; each case used a fresh process with a 60-second wall limit and a 1 GiB address-space cap. The hosted artifacts have 30-day retention. This main-branch change preserves the repository's accepted CI workflow and proof contract. The existing CI unit-test step discovers the new harness tests. Adding a permanent workflow is a separate Decapod policy transition requiring an authorized maintainer.

## Reproduce the experiment

The harness remains available from the command line:

```bash
python -m pip install -r requirements.txt
python -m experiments.record_successor target --output /tmp/primeward-target.json
python -m experiments.record_successor calibrate --output /tmp/primeward-calibration.json
```

The default target is M136279841. The commands write strict JSON and Markdown summaries, keep engine limits in place and distinguish a blocked target from a certified successor. A successor has been recovered only when the report contains an actual integer and `successor_certified: true`. Calibration results do not satisfy the record target.

## What the current initialization requires

Let E = 136279841 and p = 2^E - 1. Storing the input requires 17,034,981 packed bytes. The constructor can therefore receive the actual integer on an ordinary runner.

Its defaults are `max_seed=100000` and `max_precision_bits=8000000`. The record input fails the seed-limit check before a residual is initialized. The analytic class itself has no unsigned-64-bit input limit.

The barriers remain even if those numerical caps are raised. In the present implementation:

```text
s = p + 3 = 2^E + 2
successor_cap = 2*s - 3 = 2^(E+1) + 1
initial_precision_lower_budget = (2^E + 2)*(E+1) + 256 bits
seed_bytearray = p + 1 = 2^E bytes
```

The seed array alone is approximately 8.816943275 x 10^41024319 bytes. The exact pre-logarithm precision lower budget is approximately 1.201571636 x 10^41024328 bits. These formulas come directly from `_past_primes`, `_choose_exponent` and `_initial_precision`. They describe this implementation's initialization, not a universal lower bound on prime computation. The platform's index limit would also prevent the seed allocation.

The report evaluates these magnitudes with 160-bit Arb arithmetic, representing powers compactly; it never allocates the proposed seed array or enormous precision. It separately invokes the real constructor at its existing limits. Other errors, timeouts and failed workers remain distinct from an expected seed refusal.

## Why another Mersenne search is a different question

Every larger Mersenne number is at least 2^(E+1)-1 = 2p+1. Bertrand's postulate guarantees a prime strictly between p and 2p. Thus the immediate successor here cannot itself be Mersenne.

The unresolved research problem is to initialize a certified residual without enumerating the complete prime prefix and without precision proportional to p. The current recurrence reduces the cost of later updates; it does not yet remove that initialization cost.

## Sources

- [GIMPS discovery report](https://www.mersenne.org/primes/?press=M136279841).
- [Prime Pages current records](https://t5k.org/top20/page.php?id=3).
- [Analytic engine](../prime_successor/fast_analytic.py) and [seed implementation](../prime_successor/analytic.py).
- [Finite-bound theory](fast_analytic_theory.md).
- [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) and [workflow artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data).
