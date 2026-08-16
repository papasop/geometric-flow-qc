#!/usr/bin/env python3
"""Verify that reconstructed m4 manuscript numbers match the r1 result JSON."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "shor_multinstance_fibre_v0_9_4_r1_result.json"
TEX = ROOT / "docs/manuscript/reconstructed-v0.9.4-m4/main.tex"

EXPECTED_RESULT_SHA256 = (
    "3470ede84497391c8a99241db57aead6b0a642ee77a97ff27fed927e41f8aabf"
)
FORBIDDEN_SECTION_VI_NUMBERS = ("219.8", "0.484996", "0.485031", "0.485070")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def literal_float(x: float) -> str:
    return repr(float(x))


def compact_scientific(x: float, digits: int = 16) -> str:
    s = f"{x:.{digits}e}"
    mantissa, exp = s.split("e")
    mantissa = mantissa.rstrip("0").rstrip(".")
    exp = int(exp)
    return rf"{mantissa}\times 10^{{{exp}}}"


def require_contains(tex: str, needle: str) -> None:
    if needle not in tex:
        fail(f"missing manuscript literal: {needle}")


def require_float_present(tex: str, value: float) -> None:
    candidates = {
        literal_float(value),
        f"{value:.17f}".rstrip("0").rstrip("."),
        f"{value:.16f}".rstrip("0").rstrip("."),
        f"{value:.15f}".rstrip("0").rstrip("."),
    }
    if not any(candidate and candidate in tex for candidate in candidates):
        fail(f"missing manuscript value equivalent to: {literal_float(value)}")


def main() -> int:
    if sha256(RESULT) != EXPECTED_RESULT_SHA256:
        fail("r1 result JSON SHA-256 mismatch")

    data = json.loads(RESULT.read_text())
    tex = TEX.read_text()

    if data.get("version") != "0.9.4-r1":
        fail("unexpected r1 result version")
    if len(data.get("records", [])) != 72:
        fail("r1 result does not contain 72 records")
    if data.get("all_primary_checks_pass") is not True:
        fail("r1 primary checks do not all pass")

    agg = data["aggregate"]
    checks = {
        "intrinsic_vs_reference": "72/72",
        "intrinsic_vs_random": "68/72",
        "intrinsic_vs_spsa": "72/72",
    }
    for key, wins in checks.items():
        block = agg[key]
        require_float_present(tex, block["equal_instance_weight_mean"])
        require_float_present(tex, block["hierarchical_bootstrap_95ci"][0])
        require_float_present(tex, block["hierarchical_bootstrap_95ci"][1])
        require_contains(tex, wins)
        if block["instance_positive_mean_fraction"] != 1.0:
            fail(f"{key} instance-positive mean fraction is not 1.0")

    # Abstract uses scientific notation for the same aggregate values.
    for key in checks:
        block = agg[key]
        for value in (
            block["equal_instance_weight_mean"],
            block["hierarchical_bootstrap_95ci"][0],
            block["hierarchical_bootstrap_95ci"][1],
        ):
            variants = {compact_scientific(value, digits) for digits in (14, 15, 16)}
            if not any(variant in tex for variant in variants):
                fail(f"missing manuscript scientific value equivalent to: {value!r}")

    for value in data["audit"].values():
        if value:
            variants = {compact_scientific(value, digits) for digits in (14, 15, 16)}
            if not any(variant in tex for variant in variants):
                fail(f"missing manuscript audit value equivalent to: {value!r}")
        else:
            require_contains(tex, "0")

    for instance in data["instances"]:
        require_contains(tex, str(instance["exact_order"]))
        require_contains(tex, f"{instance['ideal_exact_order_probability']:.15f}")

    forbidden = [x for x in FORBIDDEN_SECTION_VI_NUMBERS if x in tex]
    if forbidden:
        fail(f"forbidden unsupported Section VI numbers present: {forbidden}")

    if re.search(r"frozen deterministic factorization", tex, re.I):
        fail("obsolete deterministic factorization phrase remains")
    if re.search(r"equal task-call budgets?", tex, re.I):
        fail("obsolete equal task-call budget phrase remains")

    print("PASS: reconstructed m4 manuscript numbers match r1 JSON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
