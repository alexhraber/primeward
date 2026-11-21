# Security

## Product boundary
Primeward and its applications are local numerical research programs. They do not accept network requests, load remote models or transmit inputs. Outputs are user-selected JSON and image paths. Users should choose paths appropriate for their own files; the CLI is not a multi-tenant filesystem sandbox.

## Input handling
Prime labels must be strictly increasing validated primes within the existing unsigned-64-bit contract. Numerical functions reject non-finite or physically invalid parameters. The CLI bounds count and rejects incompatible output options. Extremely large mathematical inputs can still require substantial computation; no service-level resource guarantee is provided.

## Supply chain and credentials
Scientific dependencies are installed through normal Python packaging with explicit application versions. The official Decapod release governs workflow; credentials and runtime session state remain outside tracked product files. Source-control and compute credentials are not application inputs. Decapod-generated entrypoints, attestation blocks and machine stores are changed only through supported operations.

## Scientific integrity
A wrong model assumption is a correctness risk even when arithmetic is exact. Documentation states level-count/gap assumptions, finite cutoffs, noise meaning, units and refinement checks. Noisy observations are not converted to falsely precise recovered levels. Floating-point results are not described as certified integer extraction. These boundaries are tested and are part of the public interface.

## Authentication

The numerical product has no account system or authenticated endpoint. Local process and filesystem access are provided by the caller's operating system. Repository publication and Decapod sessions use their respective authenticated tools; their secrets are not product files.

## Authorization

The user explicitly authorized editing and publishing this project. The current task has a bounded application/specification/configuration scope and a single writer. Scientific commands operate under the caller's local permissions. This is not a privileged compute service or a multi-user access-control boundary.

## Data Classification

Source, model parameters, synthetic observations and recorded examples are public research material. Session credentials and runtime proof stores are private operational state and excluded from the repository. No personal dataset is used by the examples.

## Threat Model

Relevant risks include malicious dependency substitution, accidental output overwrite, malformed numeric inputs, resource exhaustion and misleading precision claims. Required proof measures the declared runtime, dependencies are installed from explicit package versions, inputs are validated, and output/model limitations are documented. The package does not claim to safely execute untrusted arbitrary code or protect a host from a hostile local user.

## Bounded Research Compute

The record experiment accepts a bounded integer exponent and fixed seed/precision guards. It never raises those guards to allocate the record-scale history. The historical work-branch workflow parsed its quoted environment input as an integer, used read-only contents permission and persisted no checkout credentials. Each numerical case has process resource limits. The proposed permanent workflow and policy change were removed after the accepted-contract gate rejected the transition; the final candidate preserves that contract and does not claim policy.control approval.

<!-- decapod:codebase-attestation:start -->

## Codebase Attestation

- Repository signal fingerprint: `52562308a97b5c481078238af8c56bcb900e33b025636d59584043066cde24ea`
- Significant implementation surfaces: `.github/` (2 files), `README.md/` (1 files), `applications/` (17 files), `experiments/` (7 files), `prime_successor/` (6 files), `pyproject.toml/` (1 files), `requirements.txt/` (1 files), `tests/` (11 files)
- Refreshed from the current codebase by `decapod rpc --op specs.refresh`
<!-- decapod:codebase-attestation:end -->
