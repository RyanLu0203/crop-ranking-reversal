# Reproducing the supervisor-review finalization

Run all commands from the repository root with `uv`, Python 3.11 and a TeX
installation that provides `latexmk`.

The stable workflow is:

```bash
make install
make reproduce
make validate
make paper
```

`make reproduce` rebuilds the complete numerical analysis, verifies its
output checksums, renders manuscript numbers, and regenerates Figures 1–6.
`make validate` runs the legacy and finalization-specific analytical checks
and the complete test suite. `make paper` performs deterministic LaTeX builds,
 scans both compiled PDFs for internal workflow language, produces the visual
QA contact sheets, refreshes manifests, and creates the release archive.

The main analytical components can also be run directly:

```bash
export SOURCE_DATE_EPOCH=1785081600
uv run --python 3.11 python scripts/run_issue34_reconstruction.py
(cd reconstruction/issue34/outputs && shasum -a 256 -c SHA256SUMS.txt)
uv run --python 3.11 python scripts/render_issue34_manuscript_numbers.py
uv run --python 3.11 python scripts/make_issue34_figures.py
uv run --python 3.11 pytest -q
```

Canonical documents:

- `main_manuscript.pdf`
- `supplementary_information.pdf`

The public raw-source checksums are in `source_registry.csv`; variable
definitions and effective sample sizes are in `data_dictionary.md`. Model
settings are in `simulation/configs/issue34_full_model_design.yaml`.
Machine-readable output lineage is recorded in `analysis_manifest.json` and
`reconstruction/issue34/outputs/analysis_manifest.json`.

Interpretive boundaries:

- simulated scenarios are not empirical observations;
- the eight-year Kansas series calibrates structural stress experiments;
- copula parameters and shared capacities are not farm-level estimates;
- the 31-state panel is descriptive and non-causal;
- no suppressed agricultural value is imputed.

The deterministic release artifact is
`release/crop-ranking-reversal-issue38-supervisor-review.tar.gz`; its adjacent
`.sha256` file is generated after the preceding gates pass. The historical
`make issue34` and `make issue36` entry points remain aliases to
`make reproduce`.
