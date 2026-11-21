"""Decapod proof entry point: provision measured dependencies in owned scratch.

Normal installations use their installed dependencies. The reviewed local proof
contract supplies an archive, whose bytes Decapod measures before and after the
run. Extraction uses Python's data filter and never downloads or installs code.
"""
from __future__ import annotations
import argparse
import contextlib
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

@contextlib.contextmanager
def dependencies():
    archive = os.environ.get("PRIMEWARD_DEPENDENCY_ARCHIVE")
    if not archive:
        yield
        return
    archive_path = Path(archive)
    if not archive_path.is_absolute() or not archive_path.is_file():
        raise ValueError("the declared dependency archive must be an absolute regular file")
    old_path = list(sys.path)
    old_environment = os.environ.get("PYTHONPATH")
    with tempfile.TemporaryDirectory(prefix="primeward-proof-") as scratch:
        with tarfile.open(archive_path, "r:gz") as bundle:
            members = bundle.getmembers()
            if len(members) > 20000 or sum(m.size for m in members) > 1024**3:
                raise ValueError("dependency archive exceeds its reviewed size bound")
            for member in members:
                parts = Path(member.name).parts
                if not parts or parts[0] != "site-packages" or ".." in parts or not (member.isfile() or member.isdir()):
                    raise ValueError("dependency archive contains an unexpected member")
            bundle.extractall(scratch, members=members, filter="data")
        site = str(Path(scratch) / "site-packages")
        if not Path(site).is_dir():
            raise ValueError("dependency archive is missing site-packages")
        sys.path.insert(0, site)
        os.environ["PYTHONPATH"] = site
        try:
            yield
        finally:
            sys.path[:] = old_path
            if old_environment is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = old_environment

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["unit-tests", "examples"])
    args = parser.parse_args(argv)
    with dependencies():
        if args.phase == "unit-tests":
            suite = unittest.defaultTestLoader.discover("tests")
            if suite.countTestCases() == 0:
                raise RuntimeError("unit-test discovery found no tests")
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            return 0 if result.wasSuccessful() else 1
        from .__main__ import main as application_main
        return application_main(["verify"])

if __name__ == "__main__":
    raise SystemExit(main())
