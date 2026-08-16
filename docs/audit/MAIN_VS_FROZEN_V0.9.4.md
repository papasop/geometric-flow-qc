# Main vs Frozen v0.9.4 Artifact Audit

Date: 2026-08-17

Branch audited: `docs/shor-v0.9.4-restore-and-disclose`, created from latest
`origin/main`.

Frozen tag: `shor-multinstance-fibre-v0.9.4`

Frozen commit: `24da8d7ea9dddb702eb07de4b567bf5637f01e51`

## Resolution Status

Resolved on `main` by commit
`41a1411608463bfaa0a4efc94a3d8b49176da11e`.

The four canonical v0.9.4 computational artifacts now match the frozen tag
exactly. The remainder of this document records the pre-restoration state.

## Summary

Before restoration, the `main` branch contained four files still named and
presented as v0.9.4 frozen computational artifacts, but their bytes differed
from the frozen tag. The deviation was introduced by commit
`848025bea840eac993ad15989a31a095cc02beb8`
(`Address Shor audit release and ledger fixes`).

The changes were later disclosure/schema edits and regenerated output occupying
the original v0.9.4 artifact filenames. They were not a separately named later
experiment, did not introduce new optimizer logic intended to be retained as an
independent computation version, and should not have continued to occupy the
v0.9.4 frozen artifact paths.

Restoring the four files from `shor-multinstance-fibre-v0.9.4` did not discard
independent versioned work: the useful disclosure content is represented in
README/docs/tools on this branch, while the v0.9.4 frozen artifact paths returned
to their archived tag bytes.

## File-Level Differences

| File | Diff size vs tag | Classification | Introduced by |
|---|---:|---|---|
| `shor_order_finding_multinstance_fibre_v0_9_4.py` | 9 insertions, 3 deletions | Driver disclosure/schema text and record-field additions; changes frozen driver bytes and output schema, but not intended as a new versioned experiment | `848025b` |
| `frozen_protocol.json` | 2 insertions, 2 deletions | Protocol wording/key rename from budget to composite ledger; changes frozen protocol bytes | `848025b` |
| `shor_multinstance_fibre_v0_9_4_result.json` | 1120 insertions, 689 deletions | Regenerated result JSON with added ledger fields/key renames and formatting/derived output changes; changes frozen result bytes | `848025b` |
| `shor_multinstance_fibre_v0_9_4_stdout.txt` | 1192 insertions, 762 deletions | Regenerated stdout reflecting the modified schema/text output; changes archived output bytes | `848025b` |

## Line-Level Notes

### `shor_order_finding_multinstance_fibre_v0_9_4.py`

- Header docstring line near 7 changed from `equal objective budget` to
  `equal composite charged ledger`.
- Header docstring line near 21 changed from `preregistered primary gate` to
  `prospectively frozen primary gate`.
- Record construction near line 412 added:
  `intrinsic_task_calls`, `intrinsic_response_calls`, `random_task_calls`,
  `random_response_calls`, `spsa_task_calls`, and `spsa_response_calls`.
- Protocol serialization near line 530 renamed
  `equal_budget_per_method_per_meta` to
  `equal_composite_charged_ledger_per_method_per_meta`.

Classification: disclosure/schema modification to the frozen driver path. The
ledger disclosure is legitimate as post-run analysis, but not inside the frozen
v0.9.4 driver filename.

### `frozen_protocol.json`

- Protocol key near line 16 changed from `equal_budget_per_method_per_meta` to
  `equal_composite_charged_ledger_per_method_per_meta`.
- Primary gate text near line 25 changed from `three-way charged budget gap is
  zero` to `three-way composite charged ledger gap is zero`.

Classification: protocol wording/key modification. It changes the frozen
protocol bytes and must be restored.

### `shor_multinstance_fibre_v0_9_4_result.json`

- Result JSON changed because the modified driver added per-method task and
  response ledger fields to each record and renamed the protocol budget key.
- The file was regenerated after driver modification, so many line numbers
  shifted even where numerical conclusions remain the same.

Classification: regenerated result/schema output occupying the frozen result
path. It is not safe to keep under the v0.9.4 frozen filename.

### `shor_multinstance_fibre_v0_9_4_stdout.txt`

- Stdout changed to reflect the modified JSON emitted by the altered driver.
- Many line numbers shifted due to added record fields and renamed protocol
  keys.

Classification: regenerated archived output occupying the frozen stdout path.
It is not safe to keep under the v0.9.4 frozen filename.

## SHA-256 Before Restoration

Current `main` bytes:

```text
9f1b58440f8538eb143858261acd25e714ccd6e4fbe3d17b3f2dc259e6300f9b  shor_order_finding_multinstance_fibre_v0_9_4.py
17133863497b775da3a00256117a57753c053932ef31977f5692bf443017a06b  frozen_protocol.json
1d1d9557388f390be58ff727865bcf28d54eb7381036c9fd4ec83bc99009e64b  shor_multinstance_fibre_v0_9_4_result.json
c5776adb130adbc2b2d19b0802d70133cb9b2055f3ad28348e3cbd3f8d510329  shor_multinstance_fibre_v0_9_4_stdout.txt
```

Frozen tag bytes:

```text
b005753cb4780f1d1aee2da463abb2f61785ba5d27bf0ddc6d9db3e97bd43aac  shor_order_finding_multinstance_fibre_v0_9_4.py
962128c7fb0097ce76a5555dbc0bb38ab5c35fdef5999fd1fea0e2304bef4af6  frozen_protocol.json
1a65f46d09b3a64823a96f1beca929850db9020dbdd750415225eb1b6962ed10  shor_multinstance_fibre_v0_9_4_result.json
e6b723e2b28e34100110a585e7c8ae7fc3bb257af621f29b6e65d616f83b8670  shor_multinstance_fibre_v0_9_4_stdout.txt
```

## Restoration Decision

Because these files are still the canonical v0.9.4 frozen artifact paths, the
branch restores them exactly from `shor-multinstance-fibre-v0.9.4`. Later
disclosure functionality must live in separate README, docs, and read-only tool
outputs rather than modifying the frozen artifact bytes.
