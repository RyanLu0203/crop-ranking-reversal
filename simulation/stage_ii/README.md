# Stage II confirmatory simulation package

This directory is the versioned GOAL-12 / Issue #22 package. It supersedes the
scientific role of the Stage I mixed-factor pilot without modifying or deleting
`simulation/outputs/`, `simulation/validation/` or their adverse convergence
record.

## Control state

- Approved theory parent: `0979025b5b45725ab286d81edb1f29331ea97e84`.
- Active branch: `codex/issue-22-confirmatory-simulation`.
- Active issue: #22.
- Supervisor authorization: PR #27 comment `5040606456`.
- Frozen design: `simulation/configs/stage_ii_confirmatory_design.yaml`.
- Stop: hand off GOAL-12 for validation; GOAL-13 figure generation and
  manuscript reconstruction do not begin in this phase.

## Scientific design

The package isolates rather than jointly varies the six required mechanisms:

1. E1 holds score order fixed and varies cardinal Corn–Soybean margins.
2. E2 uses one-at-a-time and complete 2³ budget–rotation–contract contrasts,
   plus a separate crop-bound anchor.
3. E3 locates each replication's minimum-CVaR and expected-profit endpoints,
   then applies predeclared slack, binding and infeasible risk-limit rules.
4. E4 uses within-family dependence sweeps and explicitly labels matched
   cross-family comparisons as sensitivity.
5. E5 evaluates assumed-law policies on independent draws from each declared
   true law and separates feasibility violation from feasible regret.
6. E6 crosses Blackwell-ordered binary signals with nested finite action sets
   and retains positive, null and substitution archetypes.

The M0–M4 path and all-subset attribution are separate estimands. The latter
evaluates all 16 subsets and all 24 block orders on a predeclared common domain.
KKT pressure rows are marginal-profit balance diagnostics, never additive
acreage causes.

## Precision and admissibility

Replication checks occur at 16, 32, 48 and 64 independent seeds. An experiment
stops only at the first scheduled check where every registered primary
continuous interval and reversal interval passes. Reaching 64 without precision
creates `PRECISION_FAILED`; it never changes seeds, tolerances or outcomes.

The generated CSVs are source data for later GOAL-13 panels, not figures.
Simulation evidence is not empirical evidence. Only rows passing numerical,
replay, solver, face, precision, lineage and claim-boundary gates can be marked
eligible for later promotion.

## Confirmatory result state

The frozen run completed on 2026-07-22. E2 and E6 passed every registered
prospective precision gate at 16 replications. E1, E3, E4 and E5 reached the
64-replication ceiling without passing every gate; those failures are retained
and prohibit selective numerical promotion. All 206 infeasible rows are
designed or independently minimum-CVaR certified, and no unexplained primary
solver failure remains. See `audits/issue_22_acceptance_report.md` for the full
claim and admissibility decision. The rejected executions and code-only
remediations are disclosed in `execution_deviation_log.md`.

Run from the repository root:

```bash
uv run --python 3.11 python scripts/run_stage_ii_confirmatory.py
uv run --python 3.11 python scripts/validate_stage_ii_confirmatory.py
```
