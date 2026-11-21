# Rebuild the local Decapod runtime

Ordinary application commands use your installed Python dependencies. This helper is for contributors who need to reproduce the measured native runtime used by the local Decapod proof contract.

The current contract was evaluated on Linux with CPython 3.14. Its absolute paths describe that host. They are not required by the models or by the explicit Python steps in GitHub Actions.

## Provision from a fresh trusted environment

```bash
python3.14 -m venv /tmp/primeward-proof-env
/tmp/primeward-proof-env/bin/python -m pip install -r requirements-applications.txt
/tmp/primeward-proof-env/bin/python applications/tools/prepare_runtime.py \
  --output /tmp/primeward-runtime
```

Choose a new or empty absolute destination outside the repository and the source Python installation. The helper refuses to replace an existing runtime. It requires the direct dependency versions in `requirements-applications.txt`; use a fresh environment so the archive contains only the intended dependency installation.

The helper copies the real interpreter, packages the standard library in Python's supported ZIP layout, retains native extension modules and data, and creates `scientific-dependencies.tar.gz` with the scientific packages, metadata, wheel libraries and fonts. It records canonical linked system libraries, loader/timezone/locale inputs, versions and SHA-256 hashes in `closure.json`. It invokes the host's `ldd` only on trusted installed native files. It downloads or installs nothing.

Fixed archive metadata makes identical installed input bytes reproducibly packable. Different Python builds, transitive dependency versions and operating systems can produce different runtimes; their paths and bytes need a fresh review.

## Review and validate

Inspect `closure.json` and `suggested-proof.toml`, then verify interpreter startup and imports on the new host. The suggested fragment retains both required phases: the entire unit suite and all default application checks. Merge it into the project configuration through the normal Decapod review process, keeping source coverage and existing requirements intact.

Use `decapod rpc --op agent.init --params '{}'` to inspect the discovered workflow/build inventory and command digest. Review changes before updating the corresponding declarations. An already accepted contract can require a supported policy transition; this helper neither grants that authority nor rewrites governance. Checkpoint the reviewed source and run `decapod validate`.

The proof entry point runs with `-B -S`, extracts the measured dependency archive into Decapod's owned temporary directory, activates that exact package tree, and passes it to child Python commands. It rejects unexpected archive members and zero-test discovery. No download, pip install or recursive validator occurs during required proof.

The entire project configuration must remain below Decapod 0.156.1's 64 KiB input bound. A runtime declaration must also fit its file-count, byte and hashing-time budgets. A successful provisioning command only establishes the runtime files; successful numerical checks and Decapod validation remain separate evidence.
