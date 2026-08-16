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

## Manuscript

The accompanying manuscript is:

**Navigating Exact-Response Fibres in Shor Order Finding**

The current manuscript-only revision is `v0.9.4-m3`:

- `paper/manuscript/shor-exact-response-fibre-v0.9.4-m3.pdf`

The computational protocol remains `v0.9.4`. Revision `m3` changes exposition,
methodological disclosure, statistical interpretation, literature positioning,
and presentation only. It does not modify or rerun the frozen computation.

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
| intrinsic vs SPSA | 0.000120071 | [0.0000599292, 0.000193319] | 72/72 | 6/6 |

All prospectively frozen primary checks pass. The maximum three-way charged
budget gap is zero, the maximum intrinsic response residual is `2.66e-16`, and
the maximum ideal-multiplier change is `4.79e-16`.

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
```

## Files

- `shor_order_finding_multinstance_fibre_v0_9_4.py`: frozen executable source
- `frozen_protocol.json`: machine-readable prospective protocol and boundaries
- `shor_multinstance_fibre_v0_9_4_result.json`: complete formal result
- `shor_multinstance_fibre_v0_9_4_stdout.txt`: complete formal stdout
- `requirements.txt`: minimal dependency pin
- `CITATION.cff`: citation metadata
- `SHA256SUMS`: integrity manifest

## Supported statement

Within the declared shared synthetic model family, intrinsic Euclidean ascent
along a four-dimensional exact ideal-response fibre has positive mean advantage
over the unchanged reference, basis-invariant random search and SPSA under the
same 5,520-unit composite ledger on every frozen instance. All three
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
