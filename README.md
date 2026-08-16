# Multi-Instance Shor Task-Fibre Audit v0.9.4

This repository freezes a prospective multi-instance numerical audit of
intrinsic response-fibre navigation at the Shor order-finding task level.

## Frozen scope

- Instances: `(15,2)`, `(15,7)`, `(21,2)`, `(21,5)`, `(33,2)`, `(35,2)`
- Exact orders: `4`, `4`, `6`, `6`, `10`, `12`
- Simulator: exact phase-estimation distributions with continued-fraction
  exact-order recovery
- Implementation: shared synthetic nine-parameter ansatz
- Declared response: rank five; exact fibre dimension four
- Noise: frozen synthetic coherent/dephasing laws with a shifted held-out law
- Repetitions: 12 meta-seeds per instance, 72 records in total
- Training/held-out split: 5 training and 8 shifted held-out seeds per record
- Comparators: unchanged reference, basis-invariant random search, and SPSA
- Budget: exactly 5,520 charged units per method per record
- Inference: equal-instance-weight hierarchical paired bootstrap

This is not a native-gate hardware experiment, a fault-tolerance result, a
cryptographic-scale factorization, a universal Shor optimizer, or evidence of
asymptotic speedup.

## Frozen primary result

| Comparison | Equal-instance mean gain | Hierarchical 95% CI | Record wins | Positive instances |
|---|---:|---:|---:|---:|
| intrinsic vs reference | 0.000493796 | [0.000290298, 0.000682212] | 72/72 | 6/6 |
| intrinsic vs random | 0.000341155 | [0.000235212, 0.000455025] | 68/72 | 6/6 |
| intrinsic vs SPSA | 0.000120071 | [0.0000599292, 0.000193319] | 72/72 | 6/6 |

All preregistered primary checks pass. The maximum three-way budget gap is
zero, the maximum intrinsic response residual is `2.66e-16`, and the maximum
ideal-multiplier change is `4.79e-16`.

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
over the unchanged reference, equal-budget basis-invariant random search, and
equal-budget SPSA on every frozen instance. All three equal-instance-weight
hierarchical bootstrap intervals are strictly positive.

No claim is made about native compiled circuits, hardware advantage,
fault-tolerant resources, factoring complexity, or scalability.
