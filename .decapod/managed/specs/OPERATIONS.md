# Operations

## Installation and execution
Core installation follows the root README. Application users install `.[applications]` or `requirements-applications.txt` with Python 3.11 or newer. Direct application dependencies are pinned for repeatable experiments. No credentials or external services are needed to run the models.

Use `python -m applications list` to discover commands and `run-all --output-dir PATH --plot` to produce JSON and figures. The default residual source prioritizes demonstrating certified extraction; explicitly select the bytearray baseline for larger model populations. Input prime generation can dominate runtime and remains part of the work.

## Diagnostics
Inspect the result's checks and aggregate passed field. Preserve log partition functions/log transmission when exponentials underflow. Inspect inverse-fit optimizer termination and grid/box errors. Treat unresolved and inconsistent spectral statuses as meaningful output, rather than increasing precision without examining the observation uncertainty.

## Development
Decapod 0.156.1 initializes and governs the repository. The selected backend is local with an isolated worktree and a single writer. Use supported task, plan, workspace, trajectory, specification-refresh, checkpoint and validation commands. Runtime stores and sessions are CLI-owned and never manually edited.

The configured required proof commands run the full unit suite and all default application checks. The local measured runtime contract is reviewed separately from hosted CI. GitHub Actions installs dependencies and executes the Python checks explicitly, in addition to Decapod's CI governance validation.

## Artifacts
`applications/examples/` records finite-model outputs and generation provenance. `MANIFEST.json` covers product files while excluding itself and Decapod-owned governance material to avoid circular attestations. Product runs write only requested outputs; there are no migrations or long-running services.

## Monitoring

There is no persistent service to monitor. Inspect command exit status, result checks, spectral status, optimizer termination and flux/refinement errors. Captured Decapod receipts and CI logs record required validation; saved example provenance records the scientific runtime and settings.

## Service Level Objectives

Service availability and latency objectives do not apply to this local research package. Runtime varies with requested primes, precision, matrix sizes and hardware. Benchmarks report measured costs rather than an operational SLA.

## Incident Response

For a failed scientific check, retain the input parameters and JSON/log output, isolate the independent comparison that failed, repair the model or its stated input contract, and rerun the required checks. For governance failure, use the reported supported repair path, preserve evidence and obtain a fresh exact-candidate receipt. Do not edit Decapod runtime stores or suppress required checks.

## Measured Runtime Packaging

The local readiness contract uses a canonical native Python executable, a standard-library ZIP, native extension modules and system libraries, plus a compressed archive of scientific dependencies and package data. The source-controlled proof entry point extracts the measured archive into owned scratch and passes its package path to child Python commands. Python runs with site processing disabled and bytecode writes disabled. This is repository-authored runtime packaging, not a Decapod built-in capsule. Its absolute paths describe the reviewed validation host; another host must provision and review its own equivalent contract through Decapod. Ordinary package commands and CI do not require these host paths.

## Reprovisioning on Another Host

The trusted Linux CPython 3.14 venv can run `applications/tools/prepare_runtime.py` to create a new runtime directory, closure hashes and a suggested two-command TOML fragment. It refuses nonempty destinations and does not alter governance. Review the generated closure and current imports before reconciling the supported Decapod contract; an accepted policy transition still requires its normal authority. See `applications/tools/README.md`.

## GitHub Record Runs

Historical run 44870723187 at source commit 0893e80426b5f32fc898acc46fc8b8f3dcf6f614 used two standard Linux jobs with five-minute caps. Each numerical subprocess had a 60-second wall limit and 1 GiB address-space cap; uploaded artifacts have 30-day retention. Original reports are committed under research/record_successor_runs. The CLI can repeat target or calibration cases. This candidate preserves the accepted CI workflow/configuration; a permanent added workflow requires a separately authorized policy transition. Inspect the scientific outcome, not only workflow completion. Hosted execution is checked separately from local Decapod proof.

<!-- decapod:codebase-attestation:start -->

## Codebase Attestation

- Repository signal fingerprint: `52562308a97b5c481078238af8c56bcb900e33b025636d59584043066cde24ea`
- Significant implementation surfaces: `.github/` (2 files), `README.md/` (1 files), `applications/` (17 files), `experiments/` (7 files), `prime_successor/` (6 files), `pyproject.toml/` (1 files), `requirements.txt/` (1 files), `tests/` (11 files)
- Refreshed from the current codebase by `decapod rpc --op specs.refresh`
<!-- decapod:codebase-attestation:end -->
