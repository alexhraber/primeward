# Validation

## Proof Surfaces
The repository's required commands are the full unittest discovery suite and `python -m applications verify`. Decapod owns execution and receipts for the exact candidate under the configured local readiness profile. Hosted CI executes the Python checks explicitly and runs the separate Decapod CI governance checks. Passing one environment is not a claim that another environment has run.

## Regression Guardrails
Existing tests compare immediate prime successors and sequences against independent baselines, check numeric limits and verify the analytic invariants/certificates. Existing benchmark conclusions remain separate from correctness: an exact result does not imply a speed advantage.

## Application coverage
`test_app_thermal.py` compares boson/fermion observables with occupation sums, checks derivatives of log Z, checks a direct thermal trace, a paired-charge occupation sum and a single prime-orbit term. It covers small arguments and explicit exponentiation underflow.

`test_app_recovery.py` checks lowest-level bounds, hidden-spectrum interval coverage, whole-interval subtraction, bosonic bounds, unresolved measurement noise and contradictory observations. Arithmetic precision changes must not erase input uncertainty.

`test_app_waves.py` checks a two-point structure factor, symmetry, seeded matched controls, a single delta barrier, an independently assembled boundary-condition linear system, long opaque chains, free-box discretization convergence and an inverse fit assessed on a finer grid and larger box.

`test_app_cli.py` checks command discovery, source metadata, strict JSON, a written plot and invalid input. Default demos carry additional model-specific checks and explicit failure statuses.

## Interpretation and limitations
Scientific tolerances are declared in code and recorded data. The inverse potential is validated only for its finite targets and stated refinement; no unique or infinite-spectrum claim follows. Static scattering plots do not prove asymptotic statistics. Synthetic bounded noise is not a statistical confidence interval. Example figures are diagnostic views, not independent evidence.

## Evidence Artifacts

Required command receipts bind the evaluated candidate and declared runtime. Unit-test output names independent comparisons; application JSON records parameters, source primes and checks. Recorded JSON, SVG figures and provenance are reviewed examples rather than substitutes for execution. The product manifest hashes shipped files; Decapod owns its separate governance and specification attestations.

## Promotion Gates

Before publishing, review the bounded task scope, refresh authored specifications and generated attestations, checkpoint material changes, and run Decapod validation. Repair actual failures on the claimed branch and rerun affected required proof. Compare the published commit/tree with the validated candidate. Hosted CI status is reported only after observing that run.

## Record Experiment Checks

`tests/test_record_successor.py` checks record-scale symbolic magnitudes without allocating history, verifies that the seed refusal precedes the sieve, distinguishes precision and composite-input errors, validates exact smaller successors independently, and checks worker/CLI output. The separate GitHub run supplies actual record-input rejection and calibration evidence. It cannot be inferred from local test success alone.

<!-- decapod:codebase-attestation:start -->

## Codebase Attestation

- Repository signal fingerprint: `b3ea6fc7d61c9f2b597a04cc2a70abe27a08a5143f47b717086beac5716f8449`
- Significant implementation surfaces: `.github/` (1 files), `README.md/` (1 files), `applications/` (17 files), `experiments/` (5 files), `prime_successor/` (6 files), `pyproject.toml/` (1 files), `requirements.txt/` (1 files), `tests/` (9 files)
- Refreshed from the current codebase by `decapod rpc --op specs.refresh`
<!-- decapod:codebase-attestation:end -->
