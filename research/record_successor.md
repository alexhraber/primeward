# Record-scale successor experiment

The target is the immediate prime after p = 2^136279841 - 1. The experiment uses the existing `FastAnalyticSuccessor`; it does not substitute a search for another Mersenne prime.

## GitHub Actions

[Record successor experiment](../.github/workflows/record-successor.yml) runs two separate jobs on standard GitHub-hosted Linux runners:

- The target job constructs the actual starting integer, invokes the analytic constructor with its reviewed limits, and records the observed outcome plus a symbolic resource analysis.
- The calibration job calculates successors after M5, M7 and M13 using the same analytic engine and independently checks primality and minimality by trial division.

Each job has a five-minute limit. Every numerical case uses a fresh process with a 60-second wall limit and a 1 GiB address-space cap. JSON reports, source hashes, timing/cost counters and Markdown summaries are uploaded with 30-day retention. The experiment runs on relevant pushes and can also be started with **Run workflow**.

A successful workflow means the experiment completed. A successor has been recovered only when the report contains an actual integer and `successor_certified: true`. Calibration results do not satisfy the record target.

```bash
python -m pip install -r requirements.txt
python -m experiments.record_successor target --output /tmp/primeward-target.json
python -m experiments.record_successor calibrate --output /tmp/primeward-calibration.json
```

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
