# Interfaces

## Core
`prime_successor.fast_analytic.FastAnalyticSuccessor` and the existing engine APIs retain their previous contracts. Prime-successor input/output limits and certificates are documented in the root README and core tests. This change adds consumers rather than replacing core algorithms.

## Inbound Contracts
`python -m applications` and `primeward-applications` accept `list`, `verify`, `run-all` or one of eight application slugs. Shared options are `--count`, `--start`, `--prime-method`, `--beta`, `--seed`, `--output`, `--output-dir`, `--plot` and `--summary`. Count is bounded to 1..4096; the default inverse example requires at least five inputs. Detailed applicability is enforced by the parser and documented in `applications/README.md`.

Exit status 0 means the invoked checks passed, 1 means a scientific check failed, and 2 means invalid input or a required dependency/error prevented the calculation. `verify` writes no product artifacts. `run-all` writes only when an output directory or plotting option requests it.

## Data Ownership
Schema 1.0 includes application, model, parameters, data, checks, passed, schema_version and prime_source. Prime-source metadata contains method, start, count and actual prime labels. Strict JSON excludes non-finite numbers. Log quantities preserve scale when direct exponentiation is unavailable.

Spectral Observation values are Arb intervals tagged with either finite_levels or boson_residual. Recovery results distinguish complete, unresolved and inconsistent. Bounds are conditional on the supplied level count, positive-weight model and any gap bound. Precision/noise semantics are documented beside the implementation.

## Outbound Dependencies

The core calls python-flint. The inverse solver calls NumPy and SciPy; plots call Matplotlib and its installed dependencies. These are local library calls, with no remote service contract. The governed proof entry point can read an explicitly declared dependency archive and derive its runtime files in owned scratch; normal installations use installed packages.

## Failure Semantics

Failed scientific checks return status 1 with their diagnostics preserved. Argument/dependency/model errors return status 2. Spectral recovery reports unresolved input uncertainty separately from inconsistent observations. JSON never substitutes a finite-looking value for overflow; logs and explicit flags carry that condition.

## Record Experiment Interface

`python -m experiments.record_successor target|calibrate` accepts an exponent, timeout, memory bound and output path. The record target defaults to exponent 136279841. Results distinguish certified, blocked_max_seed, blocked_precision, timeout and process_failed. Workflow completion is distinct from `successor_certified`. The worker never serializes the enormous starting integer; its expression and bit length identify it.

## Bounded Modular and Orbital Experiments

The record-gap command takes --exponent, --span, --trial-limit,
--preview and --out. Values are capped before allocation.
Its JSON schema primeward.mersenne_gap.v1 has statuses
certified_successor, partial_screen and all_screened_candidates_composite.
Only certified_successor carries a numerical successor.
The first_unexcluded_candidate expression is an unproven candidate,
and lower_bound_distance_to_next_prime is a bound from witnessed
proper factors, not an exact gap.

The orbital-trace command takes --gamma, --width, --center,
--tolerance, --max-modes and --out. Its output is numerical and
includes the Fourier-tail truncation bound; it is not an exact
interval-arithmetic or prime-certification result.

<!-- decapod:codebase-attestation:start -->

## Codebase Attestation

- Repository signal fingerprint: `52562308a97b5c481078238af8c56bcb900e33b025636d59584043066cde24ea`
- Significant implementation surfaces: `.github/` (2 files), `README.md/` (1 files), `applications/` (17 files), `experiments/` (7 files), `prime_successor/` (6 files), `pyproject.toml/` (1 files), `requirements.txt/` (1 files), `tests/` (11 files)
- Refreshed from the current codebase by `decapod rpc --op specs.refresh`
<!-- decapod:codebase-attestation:end -->
