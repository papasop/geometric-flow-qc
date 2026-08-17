#!/usr/bin/env python3
"""Run the public Shor v0.9.4-r1 audit from a clean GitHub checkout.

This script is intentionally independent of the repository checkout from which
it is launched.  It clones the requested public ref into a temporary directory,
creates a fresh virtual environment, installs the pinned dependency, and runs
all read-only archive checks used by CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


DEFAULT_REPOSITORY = "https://github.com/papasop/geometric-flow-qc.git"
DEFAULT_REF = "shor-multinstance-fibre-v0.9.4-r1"


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def verify_manifest(root: Path, manifest_name: str) -> None:
    manifest = root / manifest_name
    for line_number, raw_line in enumerate(
        manifest.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            expected, relative_name = line.split(maxsplit=1)
        except ValueError as exc:
            raise RuntimeError(
                f"{manifest_name}:{line_number}: malformed checksum line"
            ) from exc
        relative_name = relative_name.lstrip("* ")
        target = root / relative_name
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != expected:
            raise RuntimeError(
                f"{manifest_name}:{line_number}: SHA-256 mismatch for {relative_name}"
            )
        print(f"PASS: {manifest_name}: {relative_name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="retain the clean checkout and virtual environment for inspection",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if shutil.which("git") is None:
        raise RuntimeError("git is required")

    temporary = Path(tempfile.mkdtemp(prefix="geometric-flow-qc-external-"))
    checkout = temporary / "repository"
    print("External Shor v0.9.4-r1 audit")
    print(f"repository: {args.repository}")
    print(f"ref:        {args.ref}")
    print(f"workdir:    {temporary}")

    try:
        run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                args.ref,
                "--single-branch",
                args.repository,
                str(checkout),
            ],
            cwd=temporary,
        )
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=checkout, text=True
        ).strip()
        print(f"commit:     {commit}")

        venv = temporary / "venv"
        run([sys.executable, "-m", "venv", str(venv)], cwd=temporary)
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements.txt"],
            cwd=checkout,
        )

        run([str(python), "tools/verify_frozen_v0_9_4.py"], cwd=checkout)
        run([str(python), "tools/verify_r1_reproducibility.py"], cwd=checkout)
        run([str(python), "tools/verify_m4_manuscript_numbers.py"], cwd=checkout)
        verify_manifest(checkout, "SHA256SUMS")
        verify_manifest(checkout, "SHA256SUMS_MANUSCRIPT_v0.9.4-m3.txt")
        run(
            [
                str(python),
                "-m",
                "py_compile",
                "shor_order_finding_multinstance_fibre_v0_9_4.py",
                "shor_order_finding_multinstance_fibre_v0_9_4_r1.py",
                "tools/report_v0_9_4_disclosure.py",
            ],
            cwd=checkout,
        )
        report = temporary / "v094_disclosure.json"
        with report.open("w", encoding="utf-8") as output:
            subprocess.run(
                [str(python), "tools/report_v0_9_4_disclosure.py"],
                cwd=checkout,
                stdout=output,
                check=True,
            )
        with report.open(encoding="utf-8") as source:
            disclosure = json.load(source)
        if disclosure.get("status") != "POST_RUN_DERIVED_REPORT_ONLY":
            raise RuntimeError("unexpected disclosure report status")
        print("PASS: disclosure report is valid JSON with the expected status")

        print("\nPASS: clean external audit completed")
        print(f"verified commit: {commit}")
        return 0
    finally:
        if args.keep_workdir:
            print(f"retained workdir: {temporary}")
        else:
            shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError, OSError) as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
