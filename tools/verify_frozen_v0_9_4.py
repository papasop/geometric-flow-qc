#!/usr/bin/env python3
"""Fail-closed checks for frozen Shor v0.9.4 artifacts."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "shor_order_finding_multinstance_fibre_v0_9_4.py"
RESULT = ROOT / "shor_multinstance_fibre_v0_9_4_result.json"
README = ROOT / "README.md"

EXPECTED_DRIVER_SHA256 = (
    "b005753cb4780f1d1aee2da463abb2f61785ba5d27bf0ddc6d9db3e97bd43aac"
)
EXPECTED_RESULT_SHA256 = (
    "1a65f46d09b3a64823a96f1beca929850db9020dbdd750415225eb1b6962ed10"
)
EXPECTED_INSTANCES = {
    ("N15_a2_r4", 15, 2, 4),
    ("N15_a7_r4", 15, 7, 4),
    ("N21_a2_r6", 21, 2, 6),
    ("N21_a5_r6", 21, 5, 6),
    ("N33_a2_r10", 33, 2, 10),
    ("N35_a2_r12", 35, 2, 12),
}
EXPECTED_AGGREGATE = {
    ("intrinsic_vs_reference", "equal_instance_weight_mean"):
        0.0004937962211042846,
    ("intrinsic_vs_reference", "hierarchical_bootstrap_95ci"):
        [0.0002902978897022316, 0.0006822119290334775],
    ("intrinsic_vs_random", "equal_instance_weight_mean"):
        0.00034115452936630945,
    ("intrinsic_vs_random", "hierarchical_bootstrap_95ci"):
        [0.00023521176375248254, 0.0004550249397351596],
    ("intrinsic_vs_spsa", "equal_instance_weight_mean"):
        0.00012007139006733852,
    ("intrinsic_vs_spsa", "hierarchical_bootstrap_95ci"):
        [5.992916554212649e-05, 0.0001933194498231495],
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


def load_driver():
    spec = importlib.util.spec_from_file_location("shor_v094_driver", DRIVER)
    if spec is None or spec.loader is None:
        fail(f"cannot load driver module from {DRIVER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assert_close(actual, expected, label: str) -> None:
    if isinstance(expected, list):
        if len(actual) != len(expected):
            fail(f"{label}: length mismatch")
        for i, (a, e) in enumerate(zip(actual, expected)):
            assert_close(a, e, f"{label}[{i}]")
        return
    if abs(float(actual) - float(expected)) > 1e-15:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> int:
    if sha256(DRIVER) != EXPECTED_DRIVER_SHA256:
        fail("frozen driver SHA-256 mismatch")
    if sha256(RESULT) != EXPECTED_RESULT_SHA256:
        fail("frozen result SHA-256 mismatch")

    driver = load_driver()
    matrix = np.asarray(driver.RESPONSE_MATRIX, dtype=float)
    rank = int(np.linalg.matrix_rank(matrix))
    if rank != 5:
        fail(f"response rank expected 5, got {rank}")
    kernel_dim = int(matrix.shape[1] - rank)
    if kernel_dim != 4:
        fail(f"kernel dimension expected 4, got {kernel_dim}")
    if not np.array_equal(matrix[5], matrix[0] + matrix[1] + matrix[2] + matrix[4]):
        fail("row six is not rows 1, 2, 3, and 5")
    if np.array_equal(matrix[5], matrix[:5].sum(axis=0)):
        fail("row six unexpectedly equals the first-five row sum")

    with RESULT.open(encoding="utf-8") as f:
        result = json.load(f)
    instances = {
        (row["instance"], row["N"], row["a"], row["exact_order"])
        for row in result["instances"]
    }
    if instances != EXPECTED_INSTANCES:
        fail(f"frozen instance set mismatch: {instances!r}")
    if len(result["records"]) != 72:
        fail(f"expected 72 records, got {len(result['records'])}")
    for i, row in enumerate(result["records"]):
        if not (
            row["intrinsic_budget"] == row["random_budget"] == row["spsa_budget"]
        ):
            fail(f"budget mismatch in record {i}")

    for (section, field), expected in EXPECTED_AGGREGATE.items():
        assert_close(result["aggregate"][section][field], expected, f"{section}.{field}")

    audit = result["audit"]
    if audit["maximum_intrinsic_response_residual"] > 1e-10:
        fail("maximum response residual exceeds threshold")
    if audit["maximum_intrinsic_ideal_multiplier_change"] > 1e-10:
        fail("maximum ideal multiplier deviation exceeds threshold")

    readme = README.read_text(encoding="utf-8")
    bad_phrase_a = "sum of the first" + " five"
    bad_phrase_b = "sum of first" + " five"
    if bad_phrase_a in readme or bad_phrase_b in readme:
        fail("README contains incorrect row-six prose")

    print("PASS: frozen v0.9.4 artifacts verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
