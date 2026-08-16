#!/usr/bin/env python3
"""Read-only post-run disclosure report for frozen Shor v0.9.4 artifacts."""
from __future__ import annotations

import argparse
from collections import defaultdict
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "shor_multinstance_fibre_v0_9_4_result.json"
DRIVER_PATH = ROOT / "shor_order_finding_multinstance_fibre_v0_9_4.py"
DERIVED_PATH = ROOT / "derived" / "v0.9.4_manuscript_disclosure.json"


def load_driver():
    spec = importlib.util.spec_from_file_location("shor_v094_driver", DRIVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load driver module from {DRIVER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mean(rows: list[dict], field: str) -> float:
    return float(np.mean([float(row[field]) for row in rows]))


def build_report() -> dict:
    with RESULT_PATH.open(encoding="utf-8") as f:
        result = json.load(f)
    driver = load_driver()
    matrix = np.asarray(driver.RESPONSE_MATRIX, dtype=float)
    rank = int(np.linalg.matrix_rank(matrix))
    kernel_dim = int(matrix.shape[1] - rank)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in result["records"]:
        grouped[row["instance"]].append(row)

    instance_rows = []
    report_by_instance = {row["instance"]: row for row in result["instances"]}
    for key in sorted(grouped):
        rows = grouped[key]
        meta = report_by_instance[key]
        instance_rows.append(
            {
                "instance": key,
                "ideal_exact_order_probability": meta[
                    "ideal_exact_order_probability"
                ],
                "reference_heldout_mean": mean(rows, "success_before"),
                "intrinsic_heldout_mean": mean(rows, "success_intrinsic"),
                "random_heldout_mean": mean(
                    rows, "success_basis_invariant_random"
                ),
                "spsa_heldout_mean": mean(rows, "success_spsa"),
                "intrinsic_minus_reference_mean": mean(
                    rows, "intrinsic_minus_before"
                ),
                "intrinsic_minus_random_mean": mean(
                    rows, "intrinsic_minus_random"
                ),
                "intrinsic_minus_spsa_mean": mean(rows, "intrinsic_minus_spsa"),
                "win_fractions": {
                    "intrinsic_vs_reference": meta[
                        "intrinsic_vs_reference"
                    ]["win_fraction"],
                    "intrinsic_vs_random": meta["intrinsic_vs_random"][
                        "win_fraction"
                    ],
                    "intrinsic_vs_spsa": meta["intrinsic_vs_spsa"][
                        "win_fraction"
                    ],
                },
                "bootstrap_95ci": {
                    "intrinsic_vs_reference": meta[
                        "intrinsic_vs_reference"
                    ]["bootstrap_95ci"],
                    "intrinsic_vs_random": meta["intrinsic_vs_random"][
                        "bootstrap_95ci"
                    ],
                    "intrinsic_vs_spsa": meta["intrinsic_vs_spsa"][
                        "bootstrap_95ci"
                    ],
                },
            }
        )

    six_instance_sign_check = {
        name: all(
            row[name]["win_fraction"] > 0.5
            for row in result["instances"]
        )
        for name in (
            "intrinsic_vs_reference",
            "intrinsic_vs_random",
            "intrinsic_vs_spsa",
        )
    }

    return {
        "status": "POST_RUN_DERIVED_REPORT_ONLY",
        "changes_frozen_result": False,
        "source_result": str(RESULT_PATH.relative_to(ROOT)),
        "instances": instance_rows,
        "six_instance_same_direction_check": six_instance_sign_check,
        "response_matrix": {
            "rank": rank,
            "kernel_dimension": kernel_dim,
            "row6_equals_rows_1_2_3_5": bool(
                np.array_equal(matrix[5], matrix[0] + matrix[1] + matrix[2] + matrix[4])
            ),
            "row6_equals_first_five_sum": bool(
                np.array_equal(matrix[5], matrix[:5].sum(axis=0))
            ),
            "correct_row_dependency": "r_6 = r_1 + r_2 + r_3 + r_5",
        },
        "aggregate": result["aggregate"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-derived", action="store_true")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.write_derived:
        DERIVED_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DERIVED_PATH.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
