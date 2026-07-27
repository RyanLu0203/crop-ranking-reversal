# GOAL-12 execution deviation log

## Scope

This log records execution defects and remediations after the design was frozen.
No entry changes a scientific parameter, seed, estimand, contrast, stopping
schedule, confidence rule, precision target, resource ceiling, or evidence
boundary. The accepted outputs retain design SHA-256
`21c5b970e734ed79636df2f3882d4d85460c5efa40b88e59b9b9a3f34a25c0ff`.

## 2026-07-22 pre-run smoke rejection

The first all-family one-replication smoke execution stopped in E3 because
`allocation_evaluation` treated the already aggregated CVaR subgradient as
scenario weights and attempted a second matrix product. No official output was
accepted. The implementation was corrected to use crop-level Euler tail
contributions, and two regression tests were added: contribution closure to
portfolio CVaR and fail-closed handling of a missing binary contrast.

## 2026-07-22 first full execution rejection

The first full execution completed the frozen design but exited its hard gate.
It reported 14 nonregistered failed solves and maximum pairwise pressure residual
`16625.404638975073`. The output directory from that execution was rejected and
is not canonical.

Diagnosis established two implementation/accounting issues:

1. The pressure ledger recomputed one valid empirical CVaR subgradient from
   portfolio losses. At finite-sample quantile atoms—most visibly at
   `alpha=0.99`—that subgradient need not equal the LP solver's dual-optimal tail
   weights. Pairwise KKT accounting must use the solver-derived dual weights.
2. The 14 failed E4/E5 solves were not numerical crashes. For each failure, an
   independent minimum-CVaR solve showed that the minimum feasible CVaR exceeded
   the frozen `-60` limit. Treating those rows as unexplained failures discarded
   an adverse feasibility outcome.

The remediation exposed the LP-derived crop CVaR subgradient in optimizer
diagnostics, consumed it in the pressure ledger, and added fail-closed
minimum-CVaR certificates for any E4/E5 failed solve. Failed cells continue to
produce missing contrasts and therefore continue to fail precision. No result
was imputed, dropped, or made feasible.

## Accepted rerun

The identical frozen design was rerun after those code-only corrections. The
accepted run has maximum pressure residual `1.8189894035458565e-11`, zero
unexplained primary solver failures, and 206 registered infeasible rows: 192
designed E3 anchors plus the same 14 certified E4/E5 sample-level
infeasibilities. Its prospective precision decisions remain E2/E6 passed and
E1/E3/E4/E5 failed. The exact accepted command and environment are recorded in
`outputs/run_log.json`.
