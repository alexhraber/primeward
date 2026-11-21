#!/usr/bin/env python3
"""Package an installed, trusted CPython 3.14 Linux venv for local proof.

Run with that venv's Python. This copies files and invokes ldd only on its
installed ELF files and their linked libraries. It installs nothing, edits no
governance, and refuses a nonempty destination. Normal applications do not use it.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import sysconfig
import tarfile
import zipfile


PINS = {"numpy": "2.3.5", "scipy": "1.17.0", "python-flint": "0.9.0", "matplotlib": "3.10.8"}


def files(root: Path, *, scientific: bool = False):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if "__pycache__" in rel.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if not scientific and "site-packages" in rel.parts:
            continue
        if scientific and (rel.parts[0] == "pip" or rel.parts[0].startswith("pip-")):
            continue
        if path.is_symlink() and path.is_dir():
            raise ValueError(f"directory symlink needs explicit packaging review: {path}")
        if path.is_file():
            yield path, rel
        elif not path.is_dir():
            raise ValueError(f"unsupported installed file: {path}")


def elf(path: Path) -> bool:
    with path.open("rb") as stream:
        return stream.read(4) == b"\x7fELF"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


def linked_libraries(ldd: Path, native_inputs: set[Path]) -> set[Path]:
    """Resolve trusted installed ELF dependencies without ambient loader overrides."""
    seen, libraries = set(), set()
    pending = list(native_inputs)
    # Vendored DSOs can rely on the importing extension's private library path.
    # Resolve against the trusted installed native tree, never ambient overrides.
    library_path = ":".join(sorted({str(path.parent) for path in native_inputs}))
    while pending:
        path = pending.pop().resolve(strict=True)
        if path in seen:
            continue
        seen.add(path)
        if not elf(path):
            raise ValueError(f"ldd input is not ELF: {path}")
        run = subprocess.run([str(ldd), str(path)], capture_output=True, text=True,
                             timeout=30, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C",
                                               "LD_LIBRARY_PATH": library_path})
        output = run.stdout + run.stderr
        if "not found" in output:
            raise ValueError(f"unresolved library for {path}: {output.strip()}")
        if run.returncode:
            if "statically linked" in output or "not a dynamic executable" in output:
                continue
            raise ValueError(f"ldd failed for {path}: {output.strip()}")
        for line in output.splitlines():
            item = line.split("=>", 1)[-1].strip().rsplit(" (", 1)[0].strip()
            if not item.startswith("/"):
                continue  # The virtual linux-vdso entry has no file.
            dependency = Path(item).resolve(strict=True)
            if not dependency.is_file():
                raise ValueError(f"linked input is not a regular file: {dependency}")
            libraries.add(dependency)
            if dependency not in seen:
                pending.append(dependency)
    return libraries


def make_archive(destination: Path, members: list[tuple[Path, Path]]) -> None:
    # Fixed metadata makes identical installed file bytes reproducibly packable.
    with destination.open("xb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0,
                                                     filename="", compresslevel=3) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for path, rel in members:
                info = tarfile.TarInfo("site-packages/" + rel.as_posix())
                info.size = path.stat().st_size
                info.mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                info.mtime = 0
                with path.open("rb") as source:
                    archive.addfile(info, source)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/home/ubuntu/primeward-runtime"),
                        help="new or empty directory; never replaces an existing runtime")
    args = parser.parse_args(argv)
    if sys.platform != "linux" or platform.python_implementation() != "CPython" or sys.version_info[:2] != (3, 14):
        parser.error("run this tool with an installed CPython 3.14 Linux venv")
    if sys.prefix == sys.base_prefix:
        parser.error("run this tool with the venv containing the pinned scientific dependencies")
    versions = {name: importlib.metadata.version(name) for name in PINS}
    if versions != PINS:
        parser.error(f"installed dependency versions must match {PINS}; found {versions}")
    ldd_name = shutil.which("ldd")
    if not ldd_name:
        parser.error("the trusted host's ldd is required")
    ldd = Path(ldd_name).resolve(strict=True)
    stdlib = Path(sysconfig.get_path("stdlib")).resolve(strict=True)
    package_roots = sorted({Path(sysconfig.get_path(k)).resolve(strict=True)
                            for k in ("purelib", "platlib")})
    venv = Path(sys.prefix).resolve(strict=True)
    if any(not root.is_relative_to(venv) for root in package_roots):
        parser.error("scientific package roots must belong to this venv")
    venv_config = venv / "pyvenv.cfg"
    if not venv_config.is_file() or any(
        line.partition("=")[0].strip() == "include-system-site-packages"
        and line.partition("=")[2].strip().lower() == "true"
        for line in venv_config.read_text().splitlines()
    ):
        parser.error("use a venv that excludes system site-packages")
    for name in PINS:
        location = Path(importlib.metadata.distribution(name).locate_file("")).resolve()
        if location not in package_roots:
            parser.error(f"{name} must be installed inside this venv, not an ambient package tree")
    output = args.output.expanduser()
    if not output.is_absolute() or output.is_symlink():
        parser.error("--output must be an absolute non-symlink directory")
    output = output.resolve()
    if any(output.is_relative_to(root) for root in [stdlib, venv, *package_roots]):
        parser.error("the output must be outside the source Python installation")
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists() and output.is_relative_to(parent):
            parser.error("the runtime must be outside the source repository")
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            parser.error("output already contains files; choose a different new --output directory")
    else:
        output.mkdir(parents=True, exist_ok=False)
    marker = output / "INCOMPLETE"
    marker.write_text("Provisioning in progress. A failure preserves this directory for inspection.\n")
    binary = output / "bin/python3.14"
    binary.parent.mkdir()
    interpreter = Path(sys.executable).resolve(strict=True)
    if not elf(interpreter):
        raise ValueError("the installed interpreter must be a real ELF binary")
    shutil.copy2(interpreter, binary)
    native = {interpreter}
    relocated = {interpreter: binary}
    stdlib_dir = output / "lib/python3.14"
    stdlib_dir.mkdir(parents=True)
    stdlib_zip = output / "lib/python314.zip"
    with zipfile.ZipFile(stdlib_zip, "x", compression=zipfile.ZIP_STORED) as archive:
        for path, rel in files(stdlib):
            if path.suffix == ".py" and rel.parts[0] != "sysconfig":
                info = zipfile.ZipInfo(rel.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, path.read_bytes())
            else:
                destination = stdlib_dir / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
                relocated[path.resolve(strict=True)] = destination
                if elf(path):
                    native.add(path.resolve(strict=True))
    members, member_names, archived = [], set(), set()
    for root in package_roots:
        for path, rel in files(root, scientific=True):
            if rel.as_posix() in member_names:
                raise ValueError(f"duplicate package path across installation roots: {rel}")
            member_names.add(rel.as_posix())
            members.append((path, rel))
            archived.add(path.resolve(strict=True))
            if elf(path):
                native.add(path.resolve(strict=True))
    scientific_archive = output / "scientific-dependencies.tar.gz"
    make_archive(scientific_archive, sorted(members, key=lambda item: item[1].as_posix()))
    libraries = linked_libraries(ldd, native)
    # Some CPython distributions use a shared libpython; keep it with the copy.
    for library in libraries:
        if library.name.startswith("libpython3.14") and library not in relocated:
            destination = output / "lib" / library.name
            if destination.exists():
                raise ValueError(f"runtime library name collision: {destination}")
            shutil.copy2(library, destination)
            relocated[library] = destination
    runtime_files = {path.resolve() for path in output.rglob("*")
                     if path.is_file() and path != marker}
    runtime_files.update(relocated.get(path, path) for path in libraries if path not in archived)
    for path in [Path("/etc/ld.so.cache"), Path("/etc/localtime")]:
        if path.is_file():
            runtime_files.add(path.resolve())
    for folder in [Path("/usr/lib/locale/C.utf8"), Path("/usr/lib/locale/C.UTF-8")]:
        if folder.is_dir():
            runtime_files.update(path.resolve() for path in folder.rglob("*") if path.is_file())
    runtime_files.discard(binary)
    closure = {f"f{i:04d}": str(path) for i, path in enumerate(sorted(runtime_files))}
    if len(closure) + 1 > 4096:
        raise ValueError(f"runtime still exceeds Decapod's 4096-file receipt bound: {len(closure)}")
    environment = {
        "PATH": "", "PYTHONHOME": str(output), "PYTHONPATH": "",
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PYTHONHASHSEED": "0",
        "PRIMEWARD_DEPENDENCY_ARCHIVE": str(scientific_archive), "MPLBACKEND": "Agg",
        "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "LANG": "C.UTF-8",
    }
    if any(library.name.startswith("libpython3.14") for library in libraries):
        environment["LD_LIBRARY_PATH"] = str(output / "lib")
    record = {
        "schema": "primeward.proof-runtime.v1", "python": sys.version,
        "platform": platform.platform(), "source_venv": str(venv), "packages": versions,
        "installed_packages": dict(sorted(
            (distribution.metadata["Name"], distribution.version)
            for distribution in importlib.metadata.distributions(path=[str(p) for p in package_roots])
            if distribution.metadata["Name"].lower() != "pip")),
        "program": str(binary), "toolchain_files": closure, "environment": environment,
        "archive_package_root": "site-packages",
        "sha256": {str(path): digest(path) for path in sorted(runtime_files | {binary})},
        "scope": "Installed runtime packaging only; no tests, proof execution or governance approval.",
    }
    (output / "closure.json").write_text(json.dumps(record, indent=2) + "\n")
    quoted = json.dumps
    commands = [
        ("application_examples", "examples", "Run all eight default scientific examples"),
        ("unit_tests", "unit-tests", "Run the complete core and application unittest suite"),
    ]
    lines = ["# Suggested fragment only. Review and merge; this tool changes no governance.",
             "# Preserve workflow coverage and obtain fresh review digests before validation."]
    for command_name, phase, description in commands:
        lines.extend(["", "[[proof.commands]]", f"name = {quoted(command_name)}",
                      'command = "python3.14"',
                      "args = " + quoted(["-B", "-S", "-m", "applications.proof", phase]),
                      "description = " + quoted(description), "required = true"])
    for command_name, phase, description in commands:
        name = quoted(command_name)
        lines.extend(["", f"[proof.repository_contract.executions.{name}]",
                      f"program = {quoted(str(binary))}", 'directory = "."',
                      "timeout_seconds = 1200", "",
                      f"[proof.repository_contract.executions.{name}.environment]"])
        lines.extend(f"{key} = {quoted(value)}" for key, value in environment.items())
        lines.extend(["", f"[proof.repository_contract.executions.{name}.toolchain_files]"])
        lines.extend(f"{key} = {quoted(value)}" for key, value in closure.items())
    fragment = "\n".join(lines) + "\n"
    if len(fragment.encode()) >= 65536:
        raise ValueError("the suggested fragment alone exceeds Decapod's 64 KiB full-config bound")
    (output / "suggested-proof.toml").write_text(fragment)
    marker.unlink()
    print(json.dumps({"runtime": str(output), "toolchain_file_count": len(closure),
                      "suggested_fragment_bytes": len(fragment.encode()),
                      "next": "Review closure.json and actual interpreter imports; merge the fragment without weakening existing checks."}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
