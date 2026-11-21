# Record-scale modular screening and finite orbital traces

Primeward investigates whether the next prime can be determined from
reusable arithmetic state without reconstructing the complete prime
prefix. Its exact analytic engine still needs that prefix at initialization.

The two experiments in this directory test distinct finite mathematical
constructions. **Neither proves that a 41-million-digit candidate is prime.**

## Mersenne record-screening experiment

In experiments/record_gap.py the starting integer is represented symbolically
as P = 2^136279841 - 1. Its k-th odd successor candidate is P + 2*k.
For each odd prime factor r under a bounded ceiling, the algorithm solves

    2*k == 1 - 2^136279841 (mod r)

and marks the residue class as composite. This uses modular exponentiation
with small integers. It never allocates the record-sized starting integer,
nor the arithmetic state of the existing analytic engine.

A witnessed proper factor certifies a candidate composite. A survivor is
not prime until all potential factors through its square root have been
excluded. The algorithm checks that complete condition for small inputs.

### Measured local computation, November 20, 2026

At exponent 136279841, 200,000 odd offsets, and prime factors through
2,000,000:

- 184,458 odd candidates have a proper small prime divisor.
- 15,542 survive this partial factor screen, with primality unresolved.
- The first surviving offset is k=11 (candidate P+22).
- The first ten odd offsets k=1..10 have proper factors respectively
  3, 5, 37, 3, 11, 43, 3, 17, 7, 3, easily verified with modular exponentiation.
- The distance to the next prime is at least 22, but P+22 is not
  known prime and no exact successor was found.

The recorded result and first-factor witnesses are in
research/record_gap_runs/2026-11-20/record.json.

## Orbital trace toy model

Reference: Alessandro Maria Masullo, The Music of the Primes (2026
manuscript), Introduction pp. 17-19 and 40-41, on the toy quotient of
the positive reals by gamma raised to integral powers. Poisson
summation equates an orbital sum to a sum over Fourier frequencies.
The local dilation difference becomes the reciprocal Euler factor under
the Mellin transform. The divisorial filtration is on pp. 25-27.

experiments/orbital_trace.py computes both sides independently for a
Gaussian in log(t). It supplies a conservative bound on the omitted
positive Fourier modes, excluding floating-point roundoff error.

With gamma=101 and Gaussian log-width 0.002, the test uses 2,451
positive frequencies, finds an absolute discrepancy around 2.47e-11,
and bounds the uncomputed spectral tail below 2.5e-11. Tenfold finer
resolution requires roughly tenfold more modes. The same identity
holds for composite gamma=100, demonstrating that it is not a
primality detector. The measured result is in
research/record_gap_runs/2026-11-20/orbital_trace.json.

A short ordinary interval of length h near x occupies roughly h/x in
logarithmic space. At the record integer, this requires extremely fine
localization. The manuscript's S-local construction also retains a
dependency on primes below the chosen support threshold. We have
not found a low-cost way to recover the unknown successor using it.

The manuscript's claimed GRH result is not assumed or used in these
unconditional finite experiments.

## GitHub Actions and limits

The workflow at .github/workflows/primeward-successor-experiment.yml
supports manual inputs and automatically runs its default calculations
when relevant code reaches main. Defaults are 200,000 candidate offsets
and a factor ceiling of 2,000,000, with an explicit 10-minute job
timeout. The Python code limits inputs even when dispatched manually.

The workflow runs independent checks for certified small successors:
31 to 37, 127 to 131, and 8191 to 8209, as well as the finite
Gaussian trace check, and uploads JSON outputs as artifacts.

A successful run means that these bounded experiments completed and
were checked. It does not constitute discovery of a record prime.

## Open mathematical question

Can a locally computed analytic prime-counting or trace quantity
certify nonzero or zero prime counts over a short interval without
initializing all prior primes? Any answer must account for smoothing,
the prime-power terms, numerical tail and truncation error, and total
state construction cost. A positive smoothed signal or an unresolved
small-factor survivor is not proof of prime succession.
