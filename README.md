# Multi-Instance Shor Task-Fibre Audit v0.9.4

This repository contains frozen computational artifacts for a synthetic
six-instance Shor order-finding study. Within the declared ansatz, the
optimizing methods remain on a four-dimensional exact-response fibre that
preserves the ideal modular multiplier, while finite-noise exact-order recovery
remains implementation-dependent through the stipulated synthetic noise map.

The study tests whether this stipulated task dependence is navigable and
transfers to shifted held-out noise seeds. It does not test whether the same
separation arises in native circuits or hardware.

## Frozen scope

- Instances: `(15,2)`, `(15,7)`, `(21,2)`, `(21,5)`, `(33,2)`, `(35,2)`
- Exact orders: `4`, `4`, `6`, `6`, `10`, `12`
- Simulator: exact phase-estimation distributions with continued-fraction
  exact-order recovery
- Implementation: shared synthetic nine-parameter ansatz
- Declared response: rank five; exact fibre dimension four
- Noise: frozen synthetic coherent/dephasing laws with a shifted held-out law
- Optimization: discrete intrinsic finite-difference ascent, not a continuous
  certified ODE
- Repetitions: 12 meta-seeds per instance, 72 records in total
- Training/held-out split: 5 training and 8 shifted held-out seeds per record
- Comparators: unchanged reference, basis-invariant random search, and SPSA
- Budget: exactly 5,520 charged units per method per record
- Inference: equal-instance-weight hierarchical paired bootstrap

This is not a native compiled circuit study, a hardware experiment, a
fault-tolerance result, a cryptographic-scale result, a universal optimizer
claim, or evidence of asymptotic Shor advantage.

## Frozen status

The v0.9.4 computational protocol, driver, records, and numerical outputs are
frozen and unchanged. Subsequent manuscript revisions affect exposition,
disclosure, tables, and literature positioning only.

## Reproducibility Correction

Computational protocol `v0.9.4-r1` is a reproducibility correction for the
SPSA coordinate basis. The original v0.9.4 tangent subspace was correct, but
the concrete orthonormal basis inside the four-dimensional degenerate
eigenspace was not deposited. SPSA uses coordinate Rademacher perturbations, so
that coordinate basis is part of the reproducible protocol.

The r1 corrective driver pins the analytic tangent basis archived in
`T_BASIS_v0.9.4-r1.json`, preserves the v0.9.4 instance family, seed hierarchy,
objective, budget, bootstrap rule, and primary gates, and deposits a full
72-record corrective result in
`shor_multinstance_fibre_v0_9_4_r1_result.json`.

Intrinsic finite-difference ascent is equivariant under orthogonal rotations
of the tangent basis used to represent the same fibre. The random comparator
uses the tangent projection operator and is therefore basis-invariant. SPSA is
different: its Rademacher coordinate perturbations depend on the concrete
orthonormal coordinate basis, so that basis is part of the reproducible SPSA
protocol.

The r1 SPSA values are corrective-run values under the explicitly pinned
analytic basis. They are not a bitwise reproduction of the original v0.9.4
SPSA values, because the original tangent coordinate basis was not deposited.
All primary gates continue to pass and the main conclusion direction is
unchanged.

## Manuscript

The accompanying manuscript is:

**Navigating Exact-Response Fibres in Shor Order Finding**

The current manuscript-only revision is `v0.9.4-m3`:

- `paper/manuscript/shor-exact-response-fibre-v0.9.4-manuscript-m3.pdf`

PDF SHA-256:

```text
a258dc5f0ad8b7103794d7af5b8c98d8c56f5e7131eccf1dddc6aad51273913f
```

The computational protocol remains `v0.9.4`. Revision `m3` changes exposition,
methodological disclosure, statistical interpretation, literature positioning,
and presentation only. It does not modify or rerun the frozen computation.

Frozen computational tag: `shor-multinstance-fibre-v0.9.4`

The editable m3 source is unavailable. A reconstructed manuscript source for
`v0.9.4-m4` is deposited at
`docs/manuscript/reconstructed-v0.9.4-m4/`. It was reconstructed from the m3
PDF and then revised against the v0.9.4-r1 corrective result; it is not the
recovered original m3 source. See `MANUSCRIPT_PROVENANCE.md` and
`MANUSCRIPT_M4_BLOCKERS.md`.

The externally compiled reconstructed m4 PDF is:

- `paper/manuscript/shor-exact-response-fibre-v0.9.4-manuscript-m4-reconstructed.pdf`

PDF SHA-256:

```text
d44dcd4f7ad858d3447fd8d9af2d2e21b4bde8f941c3c2a1f1d4f387773c7ef4
```

The external handoff audit reports a clean 5-page build and visual inspection.
This artifact is a reconstructed corrective/review manuscript, not a complete
source-equivalent reproduction of the 9-page m3 PDF, and must not be marked as
the final submission replacement without later authorization.

```text
RECONSTRUCTED SOURCE
NOT RECOVERED ORIGINAL M3 SOURCE
NOT A COMPLETE SOURCE-EQUIVALENT REPRODUCTION OF M3
NOT THE CURRENT SUBMISSION MANUSCRIPT
```

## Response Matrix

The declared response matrix has rank five and a four-dimensional kernel. Its
sixth row is the sum of rows 1, 2, 3, and 5 and is retained as an explicit
consistency/audit coordinate:

```text
r_6 = r_1 + r_2 + r_3 + r_5
```

## Frozen primary result

| Comparison | Equal-instance mean gain | Hierarchical 95% CI | Record wins | Positive instances |
|---|---:|---:|---:|---:|
| intrinsic vs reference | 0.000493796 | [0.000290298, 0.000682212] | 72/72 | 6/6 |
| intrinsic vs random | 0.000341155 | [0.000235212, 0.000455025] | 68/72 | 6/6 |
| intrinsic vs SPSA | 0.000122796 | [0.0000599637, 0.000200926] | 72/72 | 6/6 |

All prospectively frozen primary checks pass. The maximum three-way charged
budget gap is zero, the maximum intrinsic response residual is
`5.30e-17`, and the maximum ideal-multiplier change is `7.85e-17` in the r1
corrective archive.

The protocol and driver were frozen locally before the full run and archived
publicly together with the resulting records. This was not a registry-based
preregistration.

## Reproduce

Python 3.10+ and NumPy are sufficient.

```bash
python -m pip install -r requirements.txt
python shor_order_finding_multinstance_fibre_v0_9_4.py \
  --json-out shor_multinstance_fibre_v0_9_4_result_reproduced.json
```

The default arguments are the frozen formal protocol. Notebook-injected
arguments such as `-f` are ignored.

Verify deposited files with:

```bash
sha256sum -c SHA256SUMS
sha256sum -c SHA256SUMS_MANUSCRIPT_v0.9.4-m3.txt
python tools/verify_frozen_v0_9_4.py
python tools/verify_r1_reproducibility.py
python tools/verify_m4_manuscript_numbers.py
```

### Clean external one-click audit

From any macOS or Linux directory with Python 3.10+ and Git installed, run:

```bash
python3 <(curl -fsSL https://raw.githubusercontent.com/papasop/geometric-flow-qc/main/tools/external_one_click_test.py)
```

The script clones the frozen `shor-multinstance-fibre-v0.9.4-r1` tag into a
temporary directory, creates an isolated virtual environment, installs the
pinned NumPy dependency, and runs the frozen, r1, manuscript-number, checksum,
syntax, and disclosure checks. It is read-only and does not rerun the 72-record
optimization. A successful run ends with
`PASS: clean external audit completed` and prints the verified commit.

For the more conservative two-command form, inspect the script first:

```bash
curl -fsSLo external_one_click_test.py \
  https://raw.githubusercontent.com/papasop/geometric-flow-qc/main/tools/external_one_click_test.py
python3 external_one_click_test.py
```

## Files

- `shor_order_finding_multinstance_fibre_v0_9_4.py`: frozen executable source
- `frozen_protocol.json`: machine-readable prospective protocol and boundaries
- `shor_multinstance_fibre_v0_9_4_result.json`: complete formal result
- `shor_multinstance_fibre_v0_9_4_stdout.txt`: complete formal stdout
- `requirements.txt`: minimal dependency pin
- `tools/external_one_click_test.py`: clean-checkout external audit entry point
- `CITATION.cff`: citation metadata
- `SHA256SUMS`: integrity manifest
- `docs/manuscript/reconstructed-v0.9.4-m4/`: reconstructed m4 manuscript
  source, not recovered original m3 source

## Supported statement

Within the declared shared synthetic model family, intrinsic Euclidean ascent
along a four-dimensional exact ideal-response fibre has positive mean advantage
over the unchanged reference, basis-invariant random search and SPSA under the
same 5,520-unit composite ledger on every frozen instance. All methods are
compared under an equal composite response-call ledger of 5,520 calls per
record. The intrinsic method uses 5,500 task calls plus 20 padding calls,
whereas the random and SPSA baselines use 5,520 task calls. All three
equal-instance-weight hierarchical bootstrap intervals are strictly positive.

No claim is made about native compiled circuits, hardware advantage,
fault-tolerant resources, factoring complexity, or scalability.

## Availability statement

Code, the frozen protocol, complete per-meta records, reference stdout, and
integrity hashes are available in the geometric-flow-qc repository at commit
`24da8d7ea9dddb702eb07de4b567bf5637f01e51`, archived under tag
`shor-multinstance-fibre-v0.9.4`. The protocol and driver were frozen locally
before execution of the full run and archived publicly afterward; this was not
a registry-based preregistration.

The formal audit history in this repository starts at commit
`b3d38ba73376c14639618d8fb7f73eedd4c2c55b`, archived under tag
`shor-task-fibre-v0.9.3`. Earlier repository history belongs to predecessor
material and is not part of the formal Shor task-fibre audit.
