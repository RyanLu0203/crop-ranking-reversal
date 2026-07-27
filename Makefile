UV ?= uv
PYTHON_VERSION ?= 3.11
# Freeze generated PDF metadata so repeated raw-to-archive builds are
# byte-for-byte reproducible.  This is 27 July 2026 00:00:00 Asia/Shanghai.
export SOURCE_DATE_EPOCH ?= 1785081600

.PHONY: install figures manuscript paper validate test check manifest issue34

install:
	$(UV) sync --locked --extra test --python $(PYTHON_VERSION)

figures:
	$(UV) run --python $(PYTHON_VERSION) python scripts/generate_nature_figures.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/generate_stage_ii_figures.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/generate_goal17_visual_candidates.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/generate_goal17_figures.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/refresh_legacy_visual_checksums.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_nature_visualization.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_stage_ii_visualization.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_goal17_visualization.py

manuscript:
	$(UV) run --python $(PYTHON_VERSION) python scripts/generate_manuscript_inputs.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_manuscript.py

paper:
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_paper.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/render_pdf_qa.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_goal17_final_editorial_qa.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_release_manifest.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_stage_ii_final_archive.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_final_package.py

validate:
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_repository.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_theory_repair.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_literature_evidence.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_official_data.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_simulation_design.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_formal_simulation.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_empirical_analysis.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_nature_visualization.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_manuscript.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_final_package.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_stage_ii_blueprint.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_stage_ii_theory.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_stage_ii_confirmatory.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_stage_ii_visualization.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_goal17_visualization.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_stage_ii_empirical.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_manifest.py

test:
	$(UV) run --python $(PYTHON_VERSION) pytest

check: validate test

manifest:
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_manifest.py

issue34:
	$(UV) run --python $(PYTHON_VERSION) python scripts/run_issue34_reconstruction.py
	cd reconstruction/issue34/outputs && shasum -a 256 -c SHA256SUMS.txt
	$(UV) run --python $(PYTHON_VERSION) python scripts/render_issue34_manuscript_numbers.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/make_issue34_figures.py
	$(UV) run --python $(PYTHON_VERSION) pytest -q
	latexmk -norc -pdf -interaction=nonstopmode -halt-on-error main_manuscript.tex
	latexmk -norc -pdf -interaction=nonstopmode -halt-on-error supplementary_information.tex
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_issue34_archive.py
