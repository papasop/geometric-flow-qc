#!/usr/bin/env python3
"""Verify Shor v0.9.4-r1 corrective archive without rerunning optimization."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    "original_driver": "b005753cb4780f1d1aee2da463abb2f61785ba5d27bf0ddc6d9db3e97bd43aac",
    "old_protocol": "962128c7fb0097ce76a5555dbc0bb38ab5c35fdef5999fd1fea0e2304bef4af6",
    "old_result": "1a65f46d09b3a64823a96f1beca929850db9020dbdd750415225eb1b6962ed10",
    "old_stdout": "e6b723e2b28e34100110a585e7c8ae7fc3bb257af621f29b6e65d616f83b8670",
    "r1_result": "3470ede84497391c8a99241db57aead6b0a642ee77a97ff27fed927e41f8aabf",
    "t_basis": "03236c148c7dc761344d9bed57d907e1494cd9ce0b4e7c9e6d043d12d257b224",
}

PATHS = {
    "original_driver": ROOT / "shor_order_finding_multinstance_fibre_v0_9_4.py",
    "old_protocol": ROOT / "frozen_protocol.json",
    "old_result": ROOT / "shor_multinstance_fibre_v0_9_4_result.json",
    "old_stdout": ROOT / "shor_multinstance_fibre_v0_9_4_stdout.txt",
    "r1_result": ROOT / "shor_multinstance_fibre_v0_9_4_r1_result.json",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    for key, path in PATHS.items():
        got = sha256(path)
        if got != EXPECTED[key]:
            fail(f"{key} sha256 mismatch: {got}")

    result = json.loads(PATHS["r1_result"].read_text(encoding="utf-8"))
    if result.get("version") != "0.9.4-r1":
        fail("result version is not 0.9.4-r1")
    if len(result.get("records", [])) != 72:
        fail("result does not contain 72 records")
    if result.get("all_primary_checks_pass") is not True:
        fail("all_primary_checks_pass is not true")
    checks = result.get("primary_checks", {})
    if len(checks) != 13 or not all(bool(v) for v in checks.values()):
        fail("expected 13 passing primary checks")

    basis = json.loads((ROOT / "T_BASIS_v0.9.4-r1.json").read_text(encoding="utf-8"))
    if basis["basis_sha256"] != EXPECTED["t_basis"]:
        fail("basis sha256 mismatch in T_BASIS archive")
    matrix = np.asarray(basis["matrix"], dtype=float)
    if matrix.shape != (9, 4):
        fail(f"unexpected basis shape: {matrix.shape}")
    gram = np.linalg.norm(matrix.T @ matrix - np.eye(4), ord=np.inf)
    if gram > 1e-14:
        fail(f"basis gram residual too large: {gram}")
    if basis["checks"]["response_inf_residual"] > 1e-14:
        fail("response residual too large")
    if basis["checks"]["projector_inf_residual"] > 1e-14:
        fail("projector residual too large")

    audit = result["audit"]
    if audit["maximum_three_way_budget_gap"] != 0:
        fail("budget gap is nonzero")
    if audit["maximum_intrinsic_response_residual"] > 1e-10:
        fail("response residual audit exceeds threshold")
    if audit["maximum_intrinsic_ideal_multiplier_change"] > 1e-10:
        fail("ideal multiplier audit exceeds threshold")

    print("PASS: v0.9.4-r1 corrective archive verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
