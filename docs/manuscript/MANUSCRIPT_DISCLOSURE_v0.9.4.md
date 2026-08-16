# Manuscript Disclosure v0.9.4

## Computational Identity

Computational protocol: v0.9.4

Frozen computational tag: `shor-multinstance-fibre-v0.9.4`

Frozen commit: `24da8d7ea9dddb702eb07de4b567bf5637f01e51`

## Manuscript Identity

Manuscript revision: `v0.9.4-m3`

Canonical manuscript:
`paper/manuscript/shor-exact-response-fibre-v0.9.4-m3.pdf`

This manuscript revision is distinct from computational protocol version
`v0.9.4` and changes exposition and disclosure only.

## Nature Of The Manuscript Revision

Manuscript revisions after the frozen run correct exposition and add
methodological and statistical disclosure. They do not modify or rerun the
frozen computational protocol.

## Corrected Response-Row Statement

The correct row-six relation in the frozen response matrix is:

```text
r_6 = r_1 + r_2 + r_3 + r_5
```

The older manuscript phrase saying that row six is the sum of the first five
rows was a prose error. The frozen code and response matrix are unchanged.

## Algorithm Disclosure Extracted From Frozen Code

- Intrinsic gradient central-difference step: `h_grad = 2e-5`
- Gradient-norm stop: `|g| < 1e-14`
- Trust radius: `rho = 0.10`
- Line-search candidates: `alpha in {1, 1/2}`
- If neither line-search candidate improves the training score, the current
  iterate is retained.
- Intrinsic output: final iterate.
- SPSA output: final iterate.
- Random output: best training-scored candidate or the unchanged reference.
- Random radius: `r_max = 1.6`
- SPSA perturbation: `c = 0.03`
- SPSA learning rate: `eta_k = 0.18 / (1 + 0.02 k)`
- Residual ledger units are response-only padding.

## Statistical Boundary

- The primary inference is the frozen hierarchical bootstrap.
- The top level has only six instances.
- The intervals do not quantify alternative ansatz or noise-family
  uncertainty.
- The three intervals are unadjusted co-primary intervals.
- There is no family-wise guarantee.
- The `6/6` same-sign instance result is directional consistency.
- If a `p = 0.03125` sign check is reported, it is a post hoc descriptive sign
  check, not a frozen primary test.

## Model Boundary

The dependence of the finite-noise task score on fibre coordinates is
stipulated by the synthetic noise map through `(C_xi theta)`. The experiment
tests navigability and held-out transfer given this separation; it does not
establish that the separation occurs in native hardware.

The study uses six small exact state-vector order-finding distributions, a
shared synthetic implementation ansatz, a shared synthetic noise family, and
discrete intrinsic finite-difference ascent. It is not a continuous certified
ODE, a native compiled circuit study, a hardware experiment, a fault-tolerance
result, a cryptographic-scale result, an asymptotic Shor-advantage claim, or a
universal optimizer claim.
