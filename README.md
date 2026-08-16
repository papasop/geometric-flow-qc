# Intrinsic Shor Task-Fibre Preflight v0.9.3

This repository freezes a prospective numerical audit of response-fibre
optimization at the Shor order-finding task level.

## Frozen scope

- Instance: `N=15`, `a=2`, exact order `r=4`
- Simulator: exact state-vector order-finding distribution, including inverse
  QFT measurement probabilities
- Noise: frozen synthetic coherent and dephasing model
- Declared response: ideal modular-multiplication response
- Fibre dimension: four
- Primary task metric: probability that continued-fraction post-processing
  returns the exact order
- Repetitions: 12 independently seeded meta-experiments
- Comparators: unchanged reference, basis-invariant random search, and SPSA
- Budget: exactly 5,520 objective evaluations for every compared method in
  every meta-experiment

This is not a native-gate hardware experiment, a fault-tolerance result, a
cryptographic-scale factorization, or evidence of asymptotic speedup.

## Frozen primary result

The intrinsic Euclidean fibre flow preserves the ideal multiplier and improves
held-out exact-order recovery relative to:

| Comparison | Mean paired gain | 95% bootstrap CI | Wins | Two-sided sign test |
|---|---:|---:|---:|---:|
| unchanged reference | 0.000663114 | [0.000589428, 0.000730952] | -- | -- |
| basis-invariant random search | 0.000227786 | [0.0000736565, 0.000448007] | 11/12 | 0.00634766 |
| SPSA | 0.000159149 | [0.000120597, 0.000192322] | 11/12 | 0.00634766 |

All preregistered primary checks pass. The additional tangent, hybrid,
exact-fibre, Hessian-preconditioned, and drifted-flow comparisons are
exploratory ablations and are explicitly non-blocking.

## Reproduce

Python 3.10+ and NumPy are sufficient.

```bash
python -m pip install -r requirements.txt
python shor_order_finding_response_fibre_v0_9_3.py \
  --json-out shor_order_finding_v0_9_3_result_reproduced.json
```

The default run uses the frozen protocol. Runtime is normally under a few
minutes on a laptop CPU. Notebook-injected arguments such as `-f` are ignored.

To verify the deposited files:

```bash
sha256sum -c SHA256SUMS
```

## Files

- `shor_order_finding_response_fibre_v0_9_3.py`: frozen executable source
- `frozen_protocol.json`: concise prospective protocol and claim boundary
- `shor_order_finding_v0_9_3_result.json`: machine-readable reference result
- `shor_order_finding_v0_9_3_stdout.txt`: complete reference stdout
- `requirements.txt`: minimal dependency pin
- `CITATION.cff`: citation metadata
- `SHA256SUMS`: integrity manifest

## Scientific claim boundary

The supported statement is restricted to this frozen synthetic model:

> For the specified `N=15, a=2` state-vector order-finding model, intrinsic
> motion along an exact ideal-response fibre improves shifted held-out
> exact-order recovery over equal-budget basis-invariant random search and
> SPSA while preserving the ideal modular multiplier.

No claim is made about full Shor acceleration, computational complexity,
hardware advantage, universal noise robustness, or scalability.
