# Reconstructed Manuscript Source v0.9.4-m4

This directory contains a reconstructed LaTeX source for manuscript revision
`v0.9.4-m4`.

The editable source of manuscript revision v0.9.4-m3 was unavailable.
The v0.9.4-m4 LaTeX source was reconstructed from the archived m3 PDF
and then revised against the frozen v0.9.4-r1 corrective result.
It must not be interpreted as the recovered original m3 source.

```text
RECONSTRUCTED SOURCE
NOT RECOVERED ORIGINAL M3 SOURCE
NOT A COMPLETE SOURCE-EQUIVALENT REPRODUCTION OF M3
NOT THE CURRENT SUBMISSION MANUSCRIPT
```

## Inputs

- Archived m3 PDF:
  `paper/manuscript/shor-exact-response-fibre-v0.9.4-manuscript-m3.pdf`
- m3 PDF SHA-256:
  `a258dc5f0ad8b7103794d7af5b8c98d8c56f5e7131eccf1dddc6aad51273913f`
- Corrective r1 result JSON:
  `shor_multinstance_fibre_v0_9_4_r1_result.json`
- r1 result JSON SHA-256:
  `3470ede84497391c8a99241db57aead6b0a642ee77a97ff27fed927e41f8aabf`

## Revision Policy

The source preserves the m3 manuscript's title, authorship, abstract-level
claim, main section logic, equations, tables, appendices, references, and
availability statement in reconstructed form. It then applies the r1
reproducibility correction:

- SPSA aggregate mean and confidence interval are updated from the verified r1
  JSON.
- The random comparator is disclosed as 68/72 record wins and 6/6
  instance-positive means.
- The undeclared deterministic tangent-coordinate factorization is replaced by
  the explicit analytic tangent basis archived in `T_BASIS_v0.9.4-r1.json`.
- Unsupported Section VI quantitative claims are removed because the complete
  generation chain is missing.

## Build

The deposited source was externally compiled with `latexmk`/`pdflatex` during
the handoff audit. The resulting PDF is:

```text
paper/manuscript/shor-exact-response-fibre-v0.9.4-manuscript-m4-reconstructed.pdf
```

PDF SHA-256:

```text
d44dcd4f7ad858d3447fd8d9af2d2e21b4bde8f941c3c2a1f1d4f387773c7ef4
```

Build log SHA-256:

```text
4bb3516f69245b3648c77b746ddc63f1af85337aaaf9a6adfc88e3063f537a2b
```

To rebuild in a LaTeX-enabled environment:

```bash
pdflatex -halt-on-error -interaction=nonstopmode main.tex
pdflatex -halt-on-error -interaction=nonstopmode main.tex
```

The external handoff reports: 5 pages, compilation errors 0, undefined
references 0, undefined citations 0, overfull boxes 0, and visual inspection
without clipping, overlap, broken tables, or visible hyperlink borders.

## Submission Limitation

The archived m3 PDF has 9 pages and 14 references. This reconstructed m4 has
5 pages and 8 references. It is a compilable corrective/review manuscript, not
a complete source-equivalent reproduction of m3, and must not be marked as the
final submission replacement without a later full page-by-page reconstruction
or recovery of the original source.
