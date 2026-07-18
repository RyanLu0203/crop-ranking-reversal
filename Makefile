UV ?= uv
PYTHON_VERSION ?= 3.11

.PHONY: install validate test check manifest

install:
	$(UV) sync --locked --extra test --python $(PYTHON_VERSION)

validate:
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_repository.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_theory_repair.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_literature_evidence.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_official_data.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_simulation_design.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_formal_simulation.py
	$(UV) run --python $(PYTHON_VERSION) python scripts/validate_manifest.py

test:
	$(UV) run --python $(PYTHON_VERSION) pytest

check: validate test

manifest:
	$(UV) run --python $(PYTHON_VERSION) python scripts/build_manifest.py
