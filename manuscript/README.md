# Stage II manuscript

The canonical modular LaTeX manuscript integrates the completed Stage II theory,
confirmatory simulation, the official-data GOAL-16 empirical extension and six
main figures. Run `make manuscript` to regenerate all 49 reported numeric macros from verified
outputs and validate section order, citations, evidence levels, figure paths,
author-owned placeholders and closure of all 44 teacher-Draft content rows.

The entry point is `main.tex`; prose is divided among `sections/`, cover and
declaration material is in `frontmatter/`, generated values are in `generated/`
and manuscript-specific evidence maps are in `registries/`. No unsupported
historical manuscript or teacher-Draft number is canonical. `make paper` builds
the main and supplementary PDFs twice, renders every page and assembles the
deterministic Stage II scientific archive. The centralized six-colour card and
the full-width, 89-mm, grayscale and colour-vision QA are part of the validated
figure contract; the overlap ledger must pass for every figure.
