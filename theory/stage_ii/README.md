# GOAL-14 theory-strengthening control

## Execution control

- Parent Stage II branch: `codex/issue-21-stage-ii-blueprint`.
- Parent commit: `55b495045fe7a0539c497f3eda1002812fb86506`.
- Working branch: `codex/issue-24-theory-strengthening`.
- Active issue: GitHub Issue #24 (`GOAL-14: Deepen theory and mechanism decomposition`).
- Supervisor authorization: Issue #21 comment `5031382769`, posted 2026-07-21.
- Required outputs: formal assumptions; theorem/proposition/hypothesis audit;
  ranking-to-allocation identification; KKT pressure decomposition; operational,
  risk and diversification mechanisms; information--flexibility framework; and
  theory-to-simulation and theory-to-empirical mappings.
- Stop condition: all GOAL-14 acceptance checks pass and the package is handed
  off for review. GOAL-12 implementation does not begin on this branch.

## Versioning boundary

The Stage I files in `theory/specifications/`, `theory/audit/`,
`theory/repaired/`, and `theory/proofs/` remain the evidentiary record of the
teacher-model audit and repair. This directory is a Stage II extension. It
supersedes none of those files and does not edit the immutable teacher TeX/PDF.

## Scientific contribution

The extension adds positive but bounded theory in five layers:

1. an allocation identified set that states exactly what a ranking does and
   does not determine;
2. exchange and restricted winner-take-all certificates for rank preservation;
3. a dimensionally complete KKT pressure identity, separated from selected
   counterfactual acreage attribution;
4. non-equivalent variance, tail, concentration and true-law regret constructs;
5. general information actionability/informativeness results and a conditional
   lattice theorem for information--flexibility complementarity.

The full multi-crop simplex is not automatically a lattice under componentwise
order. Strict information--flexibility complementarity therefore remains
conditional, and any unproved full-model interaction is a preregistered
numerical hypothesis for GOAL-12.

## Canonical artifacts

- `canonical_theory_extension.md`: definitions and classified results.
- `proofs.md`: complete proofs and counterexample boundaries.
- `assumption_registry.csv`: assumptions with verification and failure effects.
- `proposition_audit.csv`: theorem/proposition/definition/hypothesis status.
- `mechanism_decomposition.md`: KKT pressure and operational mechanism ledger.
- `counterfactual_attribution_specification.md`: M0--M4 and symmetric attribution.
- `diversification_framework.md`: variance, tail, concentration and regret objects.
- `information_flexibility_framework.md`: timing, policy space and complementarity gate.
- `theory_to_simulation_mapping.csv`: confirmatory/falsification contracts.
- `theory_to_empirical_mapping.csv`: observable, proxy and identification boundaries.
- `proof_gap_reconciliation.csv`: disposition of every Stage I proof gap.
- `source_verification.md`: bounded current source verification.
- `baseline_integrity.csv`: immutable teacher and manuscript hashes.
- `supervisor_decisions.md`: genuine scientific positioning choices only.
- `theory_change_log.csv`: proposed changes relative to the teacher Draft.
- `acceptance_matrix.csv`: requirement-level completion evidence.

## Prohibited interpretations

- A KKT term is a local optimality pressure, not an additive acreage cause.
- A binding constraint is not proof that it caused an observed acreage pattern.
- A scalar lower-tail coefficient is not a joint-law order.
- Lower concentration, lower variance and lower CVaR are not interchangeable.
- Observed acreage is not a revealed optimizer.
- No historical threshold, percentage, welfare number or empirical result is
  admitted by this package.
