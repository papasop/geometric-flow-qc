# Correction Notice v0.9.4-r1

This repository keeps the original public computational tag
`shor-multinstance-fibre-v0.9.4` unchanged at commit
`24da8d7ea9dddb702eb07de4b567bf5637f01e51`.

## Issue

The original v0.9.4 response matrix and four-dimensional tangent subspace were
correct, but the concrete orthonormal coordinate basis for that tangent
subspace was not frozen. The original driver constructed the tangent basis by
diagonalizing the tangent projector with:

```python
w, v = np.linalg.eigh(P_T)
T_BASIS = v[:, w > 0.5]
```

The eigenvalue-one subspace has multiplicity four, so the returned basis is
only defined up to an orthogonal rotation. Different LAPACK environments may
choose different valid coordinates.

## Scope Of Effect

The reference, intrinsic method, and basis-invariant random comparator do not
depend on a deposited coordinate-axis convention in the same way. The material
reproducibility issue affects SPSA, because SPSA uses coordinate Rademacher
perturbations in the tangent basis.

## Corrective Run

Version `v0.9.4-r1` pins the tangent coordinates to the explicit analytic
basis archived in `T_BASIS_v0.9.4-r1.json`. It preserves the v0.9.4 frozen
instances, seed hierarchy, objective, budget, bootstrap procedure, success
criterion, and primary gates.

The verifier is intended to run from the complete repository root. Earlier
review bundles omitted legacy frozen files needed by
`tools/verify_r1_reproducibility.py`; the repository copies of
`frozen_protocol.json`, `shor_multinstance_fibre_v0_9_4_result.json`, and
`shor_multinstance_fibre_v0_9_4_stdout.txt` are used after their frozen hashes
are verified. They are not copied, regenerated, or replaced by the r1 archive.

The r1 run is a full corrective rerun:

- six frozen instances;
- 12 meta-repetitions per instance;
- 72 records total;
- 5 training seeds and 8 shifted held-out seeds per record;
- 5,520-unit composite budget per method per record;
- 10,000 hierarchical bootstrap draws.

All primary gates continue to pass. The main scientific conclusion is
unchanged: inside the declared synthetic model family, intrinsic exact-fibre
navigation retains positive held-out advantage over the unchanged reference,
basis-invariant random search, and SPSA under the specified composite ledger.

## SPSA Interpretation

The r1 SPSA values are corrective-run values under an explicitly pinned
analytic tangent basis. They are not a bitwise reproduction of the original
v0.9.4 SPSA values, because the original tangent coordinate basis was not
deposited.

This is a reproducibility correction, not an experimental expansion and not a
new native-gate, hardware, fault-tolerance, cryptographic-scale, or asymptotic
Shor-advantage claim.
