UV ?= uv
PYTHON_VERSION ?= 3.11

.PHONY: install figures manuscript paper validate test check manifest

install:
	$(UV) sync --locked --extra test --python $(PYTHON_VERSION)

figures:
	$(UV) run --python $(PYTHON_VERSION) python scripts/generate_nature_figures.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_nature_visualization.py

manuscript:
	$(UV) run --python $(PYTHON_VERSION) python scripts/generate_manuscript_inputs.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_manuscript.py

paper:
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_paper.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/render_pdf_qa.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_release_manifest.py
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
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_manifest.py

test:
	$(UV) run --python $(PYTHON_VERSION) pytest

check: validate test

manifest:
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_manifest.py
