# Semantics

## Exact succession
The residual analytic state encodes an Euler-product tail after known primes have been removed. A finite mathematical bound and Arb enclosure isolate the immediate next integer prime; an update removes its factor. The retained cost is arithmetic and precision, not a guarantee of beating a sieve. The construction uses zeta but does not require the Riemann Hypothesis.

## Physical models
Primon energies are log p in chosen units, with beta positive and Boltzmann's constant set to one. Infinite-product references require beta greater than one. A finite list of energy levels uses a sum of exponentials; a boson gas uses a product. Their decoders and removal rules are deliberately separate.

Inferred spectral intervals carry complete bounded uncertainty through each removal. More precision narrows arithmetic error but cannot remove input uncertainty. Intersecting contradictory observations returns inconsistent; insufficient resolution returns unresolved. Ground truth appears only in synthetic data construction and coverage assessment.

Scattering uses S(k)=|sum exp(-ikx)|^2/N. Delta transport assumes real barriers and identical lossless external media in units hbar^2/(2m)=1. Inverse spectra are finite-grid approximations checked on a refined grid and larger box. The orbit sum has explicit finite prime/repetition cutoffs and Gaussian smoothing. Twisted-gas phases are arbitrary parameters; no automorphic interpretation is inferred.

## Numerical meaning
Integer certificates and Arb enclosures have stated enclosing guarantees. Other outputs are floating-point approximations with independent diagnostics. A passed demo means its declared checks passed. It does not establish an asymptotic theorem, unique inverse potential or experimental result.

## Invariants

Returned integer successors remain immediate primes under the certified core contract. Removing a recovered spectral level subtracts its full exponential interval. Static scattering has S(0)=N. Real delta transport conserves flux within reported numerical tolerance. Finite thermal form factors satisfy K(0)=1. Inverse-potential coefficients remain fixed during refinement and box checks.

## State Machines

The analytic engine initializes, decodes a successor, removes its factor and repeats, rebuilding precision state when its acceptance condition requires it. Spectral inference intersects observations, then either resolves a level and removes its interval, stops unresolved, or rejects contradictory data. The CLI generates inputs, runs a model, serializes diagnostics and exits according to those diagnostics; it does not retry failed science with changed assumptions.

## Record-Scale Requirements

For p=2^E-1, the current residual engine selects s=2^E+2 and checks the exact pre-logarithm budget (2^E+2)*(E+1)+256 bits. Its seed sieve separately requests 2^E bytes. The analysis uses compact Arb values and interval-checked decimal orders. These are properties of this implementation, not a universal complexity lower bound. Engine-only candidate-test counters remain separate from independent calibration trial division.

<!-- decapod:codebase-attestation:start -->

## Codebase Attestation

- Repository signal fingerprint: `a0e7b140dd1dc81cfc14087a52a8a3e3fc46a278313c71c9de905c516c0f77d0`
- Significant implementation surfaces: `.github/` (1 files), `README.md/` (1 files), `applications/` (17 files), `experiments/` (7 files), `prime_successor/` (6 files), `pyproject.toml/` (1 files), `requirements.txt/` (1 files), `tests/` (11 files)
- Refreshed from the current codebase by `decapod rpc --op specs.refresh`
<!-- decapod:codebase-attestation:end -->
