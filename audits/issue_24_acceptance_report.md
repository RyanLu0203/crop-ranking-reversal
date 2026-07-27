# Issue #24 / GOAL-14 acceptance report

Date: 2026-07-21
Branch: `codex/issue-24-theory-strengthening`
Parent commit: `55b495045fe7a0539c497f3eda1002812fb86506`
Active issue: #24

## Scope and stop decision

GOAL-14 adds a versioned Stage II theory extension without changing the frozen teacher baseline, the Stage I repaired theorem set or the manuscript. The package formalizes assumptions, classifies each new result, proves conditional mechanisms, retains false-in-general boundaries and preregisters the tests required of later simulation and empirical phases.

This handoff stops before GOAL-12. No confirmatory experiment, figure generation, empirical promotion or manuscript rewrite was performed.

## Acceptance evidence

- `theory/stage_ii/assumption_registry.csv` contains S2-A01--S2-A22 with scope, dependencies, falsification route and failure effect.
- `theory/stage_ii/proposition_audit.csv` classifies 18 definitions, propositions, theorems, counterexample boundaries and hypotheses.
- `theory/stage_ii/canonical_theory_extension.md` and `proofs.md` establish the allocation identified set, exchange certificate, restricted winner anchor, KKT pressure identity, risk-set contraction, selection-aware attribution, diversification distinctions and information-policy results.
- `mechanism_decomposition.md` separates margin, tail-risk, budget, shared and boundary pressures with signs, units and a stationarity residual; it explicitly rejects causal-acreage interpretation of KKT terms.
- `counterfactual_attribution_specification.md` defines the M0--M4 matched path, all 16 block subsets, all 24 block orders, exact Shapley accounting and optimal-face sensitivity.
- `information_flexibility_framework.md` gives the signal/policy timing, garbling and action-nesting theorem, exact conditional lattice gate and a substitution counterexample for the full multi-crop boundary.
- The simulation and empirical maps cover all 15 non-definition theory results with support, falsification, identification and admissibility rules.
- `proof_gap_reconciliation.csv` gives every Stage I gap G01--G20 a disposition, owner, next action and manuscript rule.
- `source_verification.md` records a bounded full-text recheck of already registered methodological sources; no teacher citation, parameter or result was admitted.

The detailed G14-01--G14-16 requirement crosswalk is `theory/stage_ii/acceptance_matrix.csv`.

## Exact validation

Canonical command:

```text
uv run --python 3.11 python scripts/build_manifest.py
make check
```

Observed results:

```text
manifest_rows=377 checksum_rows=378
stage_ii_theory_files=17 assumptions=22 classified_results=18 simulation_links=15 empirical_links=15 reconciled_gaps=20 acceptance_items=16 failures=0
manifest_rows=377 checksum_rows=378 failures=0
121 passed, 11 warnings in 1.02s
```

Every preceding repository, theory-repair, literature, data, simulation, empirical, visual, manuscript, final-package and Stage II blueprint validator also reported zero failures. The warnings are upstream Matplotlib/Pyparsing deprecations and do not alter results.

Targeted deterministic theory command:

```text
uv run --python 3.11 pytest -q tests theory/proofs/computational_checks/test_stage_ii_theory.py
```

Observed result: 108 passed, 11 warnings, zero failures. The checks are synthetic mathematical/software witnesses only.

## Integrity evidence

The fail-closed GOAL-14 validator recomputed these frozen values:

| Asset | SHA-256 |
|---|---|
| Teacher TeX | `e8885aa89be6a6010f0d3e6f8e40b4b8192a91fc90f6ca4fb16ae9b0aa9dd26c` |
| Teacher PDF | `52ac1b4ef21c8d406fd6d722c877935a24d2cc6ea68520a6f35470ba8b334b44` |
| Sorted manuscript-tree listing | `0068bf01eeb3976c4df7ad0639c920c05c0ca60ce11dc323642e9b26a57cd02e` |

There is no tracked diff under `baselines/teacher_draft/`, `manuscript/`, `theory/repaired/` or the canonical Stage I audit files.

## Scientific limitations and next gate

- The exchange certificate and top-rank result are sufficient or restricted results, not a general full-order theorem.
- KKT pressures are exact local accounting terms but do not identify additive acreage causes.
- Dependence ordering remains conditional on a loss order; no scalar copula parameter is promoted to a general crop-allocation theorem.
- Information weakly improves the optimized value under policy inclusion, but information and flexibility need not be complementary without the stated lattice and supermodularity assumptions.
- Diversification diagnostics are comparator- and criterion-specific; no scalar concentration or correlation statistic identifies true-law tail protection.
- Numerical and empirical hypotheses remain unexecuted and cannot enter the manuscript.

Next action: supervisor validation of this GOAL-14 checkpoint. Only after approval may GOAL-12 reconstruct and freeze the confirmatory simulation design.
