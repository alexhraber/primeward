# Physics applications

Eight runnable experiments connect Primeward's arithmetic state to finite statistical-mechanics, spectral and wave models. They are research examples: each states its assumptions, returns machine-readable results, and includes numerical checks. The existing prime successor remains the source of exact prime labels; most physical observables use floating-point arithmetic.

## Run

Use Python 3.11 or newer for the optional scientific dependencies (the core package supports Python 3.10).

```bash
python -m pip install '.[applications]'
python -m applications list
python -m applications primon-gas --summary
python -m applications spectral-recovery --output recovery.json --plot recovery.png
python -m applications scattering --prime-method bytearray --count 256 --output scattering.json --plot scattering.png
python -m applications run-all --output-dir /tmp/primeward-applications --plot --summary
python -m applications verify
```

The installed entry point `primeward-applications` accepts the same arguments. The default source is the certified residual prime-successor engine. Select `--prime-method bytearray` explicitly when studying larger finite systems; this uses the existing sieve baseline. The output records the method and every input prime. Neither source changes the mathematical model.

Defaults are 32 primes strictly greater than 1, inverse temperature 1.5 and random seed 1729. `--start`, `--count`, `--beta` and `--seed` set these values. The inverse-potential example needs at least five primes and fits the first five. `verify` runs the default scientific checks without writing artifacts; it returns a nonzero status if any check fails. Invalid arguments return status 2.

## What each experiment does

| Command | Calculation | Independent comparison or limit |
| --- | --- | --- |
| `primon-gas` | Finite boson and fermion gases with energies log p; certified prime-mode extraction | Explicit occupation sums, derivatives of log Z, infinite zeta-product reference |
| `spectral-recovery` | Energy intervals inferred from finite positive thermal traces, with bounded noise | Hidden synthetic levels, whole-interval subtraction, unresolved-noise cases |
| `scattering` | Static structure factor of prime positions | Periodic positions and a seeded random odd-lattice ensemble with matched count and window |
| `transport` | Transmission and reflection through real delta scatterers | Single barrier formula, direct boundary-condition solve, flux conservation |
| `inverse-spectrum` | Smooth one-dimensional potential fitted to five prime-valued levels | A finer grid and a larger spatial box with the fitted potential held fixed |
| `form-factor` | Thermal spectral form factor of a finite boson gas | Direct occupation trace and K(0) = 1 |
| `prime-orbits` | A finite, Gaussian-smoothed prime-orbit oscillatory sum | Single-term formula and explicit damping/cutoff checks |
| `twisted-gas` | Paired charged modes with arbitrary phases | Direct two-occupation sum and neutral-gas identity |

### Primon thermodynamics

Use dimensionless energies E_p = log p, inverse temperature beta > 0 and k_B = 1. For the selected finite prime set P,

```text
Z_boson(beta)   = product_p (1 - p^(-beta))^(-1)
Z_fermion(beta) = product_p (1 + p^(-beta))
```

The code sums log factors, mean energy and energy variance using stable small-argument expressions. Heat capacity is beta^2 Var(E); entropy is log Z + beta U. Finite products converge for every positive beta. The infinite references zeta(beta) and zeta(beta)/zeta(2 beta) are evaluated only for beta > 1.

`recover_prime_modes` calls the existing certified residual engine and includes its integer certificates. This demonstrates the arithmetic extraction/removal connection for the primon model. It does not infer unknown laboratory energies from measured thermodynamic data, and the displayed floating-point values log p are not interval certificates.

### Recovery from thermal traces

For a complete finite list of N levels with positive weights equal to one, the observation is

```text
C(beta) = sum_j exp(-beta E_j).
```

When an observed interval is [C_lo, C_hi] with C_lo > 0, the smallest level satisfies

```text
-log(C_hi)/beta <= E_min <= (log N - log(C_lo))/beta.
```

A known lower bound on the gap sharpens the upper bound by replacing N with 1 + (N - 1) exp(-beta gap). Bounds from different temperatures are intersected using Arb ball arithmetic. The number of levels and any gap bound are assumptions supplied to the decoder. Unknown weights, missing levels and a continuous spectrum require a different inference model.

After a level is enclosed, the implementation subtracts the entire interval exp(-beta E), preserving uncertainty. It never substitutes the interval midpoint. An observation whose uncertainty reaches zero cannot provide a logarithmic lower-tail constraint. Results distinguish complete recovery, unresolved precision/noise and inconsistent supplied observations.

A separate bosonic residual model uses R = product_j(1 - exp(-beta E_j))^(-1) - 1. It has its own bounds and removal rule R' = R - a - R a. Those bounds must not be substituted for the finite-level trace bounds.

The demo's ground-truth energies are used only to create observations and assess coverage; the decoder receives observations, level count and a stated gap assumption. Relative and absolute noise are bounded interval uncertainties, not statistical confidence intervals. Increasing arithmetic precision does not remove uncertainty in the measurements.

### Scattering and transport

For N point positions, the normalized static structure factor is

```text
S(k) = |sum_j exp(-i k x_j)|^2 / N.
```

The forward peak is S(0) = N. Prime positions are compared with equally spaced positions and independent random subsets of the same odd-integer lattice/window, with the exceptional prime 2 included in the eligible lattice when applicable. The default random control uses 16 realizations and reports the standard error of their mean. Finite-window plots alone do not establish an asymptotic hyperuniformity claim.

Transport uses the Hamiltonian -d^2/dx^2 + sum_j g_j delta(x-x_j), in units hbar^2/(2m) = 1. The same real external medium is used on both sides. A reciprocal scattering-matrix composition avoids the exponentially growing entries of transfer-matrix multiplication. The code reports T, R, flux error and log T; log T remains informative when T underflows. It reports numerical failures rather than clipping T or R into a plausible range.

These are ideal coherent one-dimensional models. No absorption, disorder dynamics or experimental fabrication model is assumed.

### Inverse quantum spectrum

The default target is [2, 3, 5, 7, 11], in chosen energy units. A harmonic confining potential plus eight smooth adjustable basis functions is fitted on a finite Dirichlet grid. The optimizer uses eigenvalue derivatives from the computed eigenvectors and a small coefficient penalty.

The returned parameters define the same continuous potential for three calculations: the fitting grid, a finer grid, and a larger box at the finer spacing. The independent checks require a refined-grid maximum target error below 0.002 and a maximum box-change error below 0.0002. Grid and box sizes, optimizer termination and all observed errors are included in the result.

Fitting finitely many levels does not determine a unique potential, an exact infinite prime spectrum or a practical prime generator. Changing the targets can make the default basis or tolerances insufficient; that is reported as a failed check.

### Form factor, prime orbits and charged modes

The form factor is K(t) = |Z(beta + i t)/Z(beta)|^2 for the finite boson product. Its time variable is in reciprocal energy units. The calculation uses log magnitudes and stable denominators and is checked against a direct occupation sum.

The prime-orbit example evaluates the finite sum

```text
-(1/pi) sum_p sum_{m=1..M} (log p) p^(-m/2)
          exp[-(sigma m log p)^2 / 2] cos(x m log p).
```

Here x is an ordinate parameter, sigma is a positive smoothing width and M is an explicit repetition cutoff. This is a trace-formula-inspired numerical signal. It does not evaluate an Euler product on the critical line or certify zeta zeros. A finite prime cutoff and smoothing alter the signal; a complete explicit formula would also require its other terms and error analysis.

The paired charged gas has one factor
[1 - 2 p^(-beta) cos(theta_p) + p^(-2 beta)]^(-1) per prime. Arbitrary phases are supported; they need not be Dirichlet characters or automorphic data. The paired product is real and positive, while its formal occupation expansion can have signed coefficients. At theta = pi the coefficients are 1, -2, 3, -4, and so on. The output explicitly marks partition-function underflow or overflow and preserves log Z.

## Numerical contracts

Every result contains the application name, model, parameters, data, checks, aggregate `passed`, schema version and prime-source metadata. JSON does not contain NaN or Infinity; unavailable floating-point exponentials are represented by null with the corresponding log quantity retained.

Only the certified integer successor and Arb spectral intervals provide enclosing-arithmetic guarantees, under their stated assumptions. Thermodynamics, structure factors, wave amplitudes, fitted potentials and trace signals are floating-point computations whose diagnostics are part of the result. They are not promoted to exact claims.

The common prime-label validator accepts strictly increasing actual primes below 2^64. The finite physics functions can also be called directly from Python. Arb's precision context is process-global, so the command runner executes applications sequentially.

## Verification and examples

`tests/test_app_thermal.py`, `test_app_recovery.py`, `test_app_waves.py` and `test_app_cli.py` contain comparisons that do not merely call the same formula twice: occupation sums, a direct continuity/derivative-jump linear system, the analytic free-particle box, refined discretization and hidden-spectrum interval coverage. The original prime-successor tests remain in the suite.

For project contributors, `decapod validate` owns the configured required unit-test and application-example commands. GitHub Actions also installs the pinned application requirements and runs these commands explicitly, because Decapod's CI scope checks repository governance rather than the local machine's measured runtime contract.

The local measured runtime can be rebuilt with the [contributor provisioner](tools/README.md). It records a suggested contract for review and does not edit governance.

See [examples/README.md](examples/README.md) for saved outputs and their provenance. Regenerate examples after changing a model rather than treating them as ground truth.

## Related work

These experiments implement small, inspectable models based on established connections. Primeward's current analytic prime generator is still slower than its sieve baselines. These examples do not change that performance result.

- [Dueñas and Svaiter, thermodynamics of a randomized Riemann gas](https://arxiv.org/html/1401.8190v3): the logarithmic prime-energy gas and its convergence domain.
- [Hansen, Lupo and Tantalo, spectral densities from lattice correlators](https://arxiv.org/html/1903.06476v2): the difficulties of recovering spectra from Euclidean/thermal data.
- [Cassettari, Mussardo and Trombettoni, quantum potentials with prime-number spectra](https://arxiv.org/abs/2202.03446): prior inverse-potential work.
- [Torquato, Zhang and de Courcy-Ireland, prime-number spatial correlations](https://arxiv.org/html/1802.10498v1): structure factors and spatial statistics.
- [Berry and Keating, the Riemann zeros and eigenvalue asymptotics](https://michaelberryphysics.wordpress.com/wp-content/uploads/2013/06/berry307.pdf): prime-orbit and spectral analogies.
- [Hartnoll and Yang](https://arxiv.org/html/2502.02661v2), section 6.1: charged primon-gas factors.
- [SciPy eigh_tridiagonal documentation](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.linalg.eigh_tridiagonal.html): the numerical eigensolver used by the inverse example.

The prime-successor construction uses the Riemann zeta function. It does not assume the Riemann Hypothesis. None of these finite physics models supplies a proof of that hypothesis.
