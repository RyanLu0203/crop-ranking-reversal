# Reproducing the Issue #36 repair of the Issue #34 reconstruction

The reconstruction is deterministic under the registered design and seeds.
Run commands from the repository root.

The complete raw-to-archive workflow is:

```bash
make issue36
```

The equivalent component commands are:

```bash
export SOURCE_DATE_EPOCH=1785081600
uv sync
uv run python scripts/run_issue34_reconstruction.py
(cd reconstruction/issue34/outputs && shasum -a 256 -c SHA256SUMS.txt)
uv run python scripts/render_issue34_manuscript_numbers.py
uv run python scripts/make_issue34_figures.py
uv run pytest -q
```

Then compile `main_manuscript.tex` and `supplementary_information.tex` using
the repository's LaTeX workflow. The canonical PDFs are
`main_manuscript.pdf` and `supplementary_information.pdf`.

The official raw sources and their checksums are in `source_registry.csv`.
Variable definitions and effective sample sizes are in `data_dictionary.md`.
The frozen model is `simulation/configs/issue34_full_model_design.yaml`.
Machine-readable output lineage is recorded in `analysis_manifest.json` and
`reconstruction/issue34/outputs/analysis_manifest.json`.

Key boundaries:

- simulated scenarios are not empirical observations;
- the eight-year Kansas series calibrates a structural stress test;
- copula parameters and shared capacities are not farm-level estimates;
- the 31-state panel is descriptive and non-causal;
- no suppressed agricultural value is imputed.

The deterministic release artifact is
`release/crop-ranking-reversal-issue36-reproducibility.tar.gz`; its adjacent
`.sha256` file is generated only after every preceding gate passes.  The legacy
`make issue34` entry point remains as an alias to `make issue36`.
