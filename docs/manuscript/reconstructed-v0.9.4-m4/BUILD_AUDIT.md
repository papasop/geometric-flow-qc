# Build and audit report

Artifact: reconstructed manuscript revision `v0.9.4-m4`

## Passed checks

- `verify_m4_manuscript_numbers.py`: PASS against the deposited r1 result JSON.
- LaTeX compilation: PASS with `latexmk`/`pdflatex`.
- PDF pages: 5.
- PDF metadata title and author: correct.
- Compilation errors: 0.
- Undefined references/citations: 0.
- Overfull boxes: 0.
- Unsupported Section VI literals `219.8`, `0.484996`, `0.485031`, and
  `0.485070`: absent from source and compiled PDF.
- Visual inspection: all five rendered pages inspected; no clipping,
  overlap, broken tables, or visible hyperlink borders.

Two harmless float-placement warnings remain (`h` changed to `ht`).

## Scope limitation

This is a compilable reconstructed revision, not recovered original source.
The archived m3 PDF has 9 pages and 14 references; this reconstructed m4 has
5 pages and 8 references. It therefore must not be represented as a complete
source-equivalent reproduction of m3. A submission intended to preserve every
m3 argument, appendix, table, and citation still requires a full page-by-page
reconstruction or the original m3 source.

## Archive limitation

The supplied review bundle omits three legacy files required by
`tools/verify_r1_reproducibility.py`: `frozen_protocol.json`,
`shor_multinstance_fibre_v0_9_4_result.json`, and
`shor_multinstance_fibre_v0_9_4_stdout.txt`. Consequently that verifier cannot
run from the review bundle alone. The manuscript-number verifier is
self-contained within the supplied inputs and passes.
