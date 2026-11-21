# Intent

## Product Outcome
Primeward investigates exact immediate prime succession from a reusable arithmetic state. Its users are researchers and programmers who need inspectable formulas, independent correctness checks and explicit cost measurements. The implementation extracts a prime from a zeta/Euler-product residual, incorporates that prime and continues. Finite bounds and Arb enclosures certify integer decoding; no assumption about nontrivial zeta zeros is used.

## Scope
The residual engine, earlier analytic variants and sieve baselines remain distinct implementations in `prime_successor/`. Existing experiments charge initialization and subsequent updates separately. The analytic construction has not beaten the sieve baselines or established an efficient general prediction algorithm. `research/fast_analytic_theory.md` gives the invariant and bounds.

## Applications
`applications/` adds eight finite physics experiments: primon thermodynamics, spectral interval recovery, static scattering, delta-barrier transport, inverse quantum spectra, a thermal form factor, smoothed prime-orbit sums and a paired charged gas. Their purpose is to test useful mathematical connections with runnable examples and honest error diagnostics. They do not assert a newly discovered physical law, exact prime-valued infinite Hamiltonian spectrum or Riemann Hypothesis result.

## Acceptance Criteria
The shared CLI must return reproducible JSON, state its prime source and assumptions, and report failed numerical checks. Tests compare models with independent sums, boundary equations, interval coverage and refined discretization. Optional plotting and saved examples help users inspect the calculations. Decapod owns authoring claims and required validation; application results contain their own scientific diagnostics.

## Constraints

Preserve the core prime algorithms and existing benchmark conclusions. Keep application dependencies optional, source selection explicit and every model finite with stated assumptions. Use only supported Decapod operations for machine-owned state. Publish code only after required checks and an exact-candidate review.

<!-- decapod:declared-capabilities:start -->

## Declared Capability Surfaces

These declarations select authoring and proof obligations; they do not attest implemented runtime guarantees.

- `certified_prime_succession`
- `numerical_physics_applications`

<!-- decapod:declared-capabilities:end -->

<!-- decapod:codebase-attestation:start -->

## Codebase Attestation

- Repository signal fingerprint: `77ec1794e03e485a3d8d927049e0a3da108dc579c40541a59790529007b51fab`
- Significant implementation surfaces: `.github/` (1 files), `README.md/` (1 files), `applications/` (17 files), `experiments/` (4 files), `prime_successor/` (6 files), `pyproject.toml/` (1 files), `requirements.txt/` (1 files), `tests/` (8 files)
- Refreshed from the current codebase by `decapod rpc --op specs.refresh`
<!-- decapod:codebase-attestation:end -->
