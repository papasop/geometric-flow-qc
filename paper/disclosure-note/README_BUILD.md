# Paper Build

This directory contains the repository paper source snapshot for the Shor
task-fibre audit.

Build with a standard LaTeX distribution:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The manuscript source intentionally uses concrete tag, commit, date, and rule
values rather than bracketed placeholders.
