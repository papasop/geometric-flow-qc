#!/usr/bin/env python3
"""Reproducibility correction for v0.9.4.

This wrapper deliberately leaves the frozen v0.9.4 driver unchanged.  It
replaces the LAPACK-dependent basis returned from a degenerate ``eigh(P_T)``
with an explicit canonical orthonormal basis of ``ker(RESPONSE_MATRIX)`` before
any optimizer is run.  Both this file and the original v0.9.4 driver are needed
to reproduce an r1 run.

The correction is prospective with respect to r1 outputs.  It does not claim
to reproduce the original archive's SPSA column, whose coordinate basis was
not deposited.  It also does not repair or regenerate manuscript Section VI.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
from pathlib import Path
import sys
from contextlib import redirect_stdout

import numpy as np

import shor_order_finding_multinstance_fibre_v0_9_4 as core


CORRECTION_VERSION = "0.9.4-r1"
BASIS_CONVENTION = (
    "Explicit analytic orthonormal basis, fixed column order and signs: "
    "(e0+e3)/sqrt(2), (e1-e5)/sqrt(2), "
    "(e1+e5-2e6)/sqrt(6), (e2-e8)/sqrt(2)."
)


def canonical_tangent_basis() -> np.ndarray:
    """Return a platform-independent 9x4 basis of ker(RESPONSE_MATRIX)."""
    s2 = np.sqrt(2.0)
    s6 = np.sqrt(6.0)
    t = np.zeros((core.N_PARAM, 4), dtype=np.float64)
    t[0, 0], t[3, 0] = 1.0 / s2, 1.0 / s2
    t[1, 1], t[5, 1] = 1.0 / s2, -1.0 / s2
    t[1, 2], t[5, 2], t[6, 2] = 1.0 / s6, 1.0 / s6, -2.0 / s6
    t[2, 3], t[8, 3] = 1.0 / s2, -1.0 / s2
    return t


def array_sha256(x: np.ndarray) -> str:
    """Hash an array with fixed dtype/order plus its shape."""
    a = np.ascontiguousarray(x, dtype="<f8")
    payload = json.dumps(list(a.shape), separators=(",", ":")).encode("ascii")
    payload += b"\0" + a.tobytes(order="C")
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def numpy_configuration() -> str:
    stream = io.StringIO()
    with redirect_stdout(stream):
        np.show_config()
    return stream.getvalue()


def install_and_validate_basis() -> dict[str, object]:
    t = canonical_tangent_basis()
    gram_residual = float(np.linalg.norm(t.T @ t - np.eye(4), ord=np.inf))
    response_residual = float(np.linalg.norm(core.RESPONSE_MATRIX @ t, ord=np.inf))
    projector_residual = float(np.linalg.norm(core.P_T @ t - t, ord=np.inf))
    if t.shape != (9, 4):
        raise RuntimeError(f"unexpected tangent-basis shape: {t.shape}")
    if max(gram_residual, response_residual, projector_residual) > 1e-14:
        raise RuntimeError(
            "canonical tangent basis failed validation: "
            f"gram={gram_residual}, response={response_residual}, "
            f"projector={projector_residual}"
        )
    core.T_BASIS = t
    core.TANGENT_DIM = 4
    core.VERSION = CORRECTION_VERSION
    return {
        "convention": BASIS_CONVENTION,
        "matrix": t.tolist(),
        "array_sha256": array_sha256(t),
        "gram_inf_residual": gram_residual,
        "response_inf_residual": response_residual,
        "projector_inf_residual": projector_residual,
    }


def output_path_from_argv() -> Path:
    if "--json-out" in sys.argv:
        i = sys.argv.index("--json-out")
        if i + 1 >= len(sys.argv):
            raise ValueError("--json-out requires a path")
        return Path(sys.argv[i + 1])
    path = Path("shor_multinstance_fibre_v0_9_4_r1_result.json")
    sys.argv.extend(["--json-out", str(path)])
    return path


def main() -> int:
    basis_audit = install_and_validate_basis()
    output = output_path_from_argv()
    original = Path(core.__file__).resolve()
    wrapper = Path(__file__).resolve()

    print("[r1] reproducibility correction: explicit tangent basis installed")
    print("[r1] T_BASIS sha256:", basis_audit["array_sha256"])
    print("[r1] original driver sha256:", file_sha256(original))
    code = core.main()

    if not output.exists():
        raise RuntimeError(f"core driver did not create expected output: {output}")
    result = json.loads(output.read_text(encoding="utf-8"))
    result["version"] = CORRECTION_VERSION
    result["reproducibility_correction"] = {
        "scope": (
            "Pins the four-dimensional tangent coordinate basis used by SPSA; "
            "does not recreate the undeclared basis of the original archive."
        ),
        "original_driver": original.name,
        "original_driver_sha256": file_sha256(original),
        "wrapper": wrapper.name,
        "wrapper_sha256_before_output_write": file_sha256(wrapper),
        "tangent_basis": basis_audit,
        "environment": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "numpy_configuration": numpy_configuration(),
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
            "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
            "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
        },
    }
    result["interpretation"] += (
        " The r1 SPSA values are new corrective-run values under the explicitly "
        "pinned analytic tangent basis and must not be presented as bitwise "
        "reproduction of the original v0.9.4 SPSA values."
    )
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[r1] annotated result written to", output)
    return code


if __name__ == "__main__":
    status = main()
    if "ipykernel" not in sys.modules and "google.colab" not in sys.modules:
        raise SystemExit(status)
