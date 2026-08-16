# Manuscript v0.9.4-m4 Blockers And Resolutions

The code and archive layer for computational protocol `v0.9.4-r1` can be
prepared from the supplied r1 driver and result JSON. The original editable
source for manuscript revision `v0.9.4-m3` is permanently unavailable, so the
local `v0.9.4-m4` source in
`docs/manuscript/reconstructed-v0.9.4-m4/` is reconstructed source, not
recovered original source.

## Missing Inputs

- The formal Shor manuscript LaTeX source or source ZIP is not present and has
  been confirmed unavailable.
- The current repository contains the m3 PDF, but the complete m3 manuscript
  source is not included.
- Section VI's complete generation chain is not present: no verified code,
  inputs, outputs, and hashes were found for the Hessian, 256-sample
  diagnostic, infidelity proxy, or preconditioning ablation numbers.

## Manuscript Handling

All m4 primary tables and text are recalculated from
`shor_multinstance_fibre_v0_9_4_r1_result.json`.

Because Section VI lacks a complete generation chain, its quantitative claims
are removed in the reconstructed source and replaced by a non-numeric
future-work/provenance discussion. The revision must not claim that Section VI
has been fully reproduced unless the generation chain is deposited and
verified.

The m4 manuscript should state that `v0.9.4-r1` is a reproducibility
correction. It must not describe the corrective run as a new preregistered
experiment or as evidence for native-circuit, hardware, fault-tolerance,
cryptographic-scale, asymptotic, or practical computational advantage.

## Remaining Local Blocker

The handoff audit reports that clean PDF compilation and page-render QA were
completed externally. The remaining blocker is scope: the archived m3 PDF has
9 pages and 14 references, while the reconstructed m4 has 5 pages and
8 references. This m4 artifact is suitable for corrective review, but it is
not a complete source-equivalent reconstruction of m3 and must not be marked as
a final submission replacement without later authorization.
