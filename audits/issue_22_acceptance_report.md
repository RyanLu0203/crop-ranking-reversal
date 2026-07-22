# Issue #22 / GOAL-12 acceptance report

## Decision

GOAL-12 is **implementation-complete with adverse precision results retained**.
This report does not authorize figure generation, empirical interpretation,
manuscript reconstruction, or promotion of any simulation result. Supervisor
review is required before GOAL-13.

The confirmatory run used frozen design
`CRR-STAGEII-CONFIRM-2026-07-22` with SHA-256
`21c5b970e734ed79636df2f3882d4d85460c5efa40b88e59b9b9a3f34a25c0ff`.
It completed in 133.62 seconds with 178,831,360 bytes peak parent RSS against a
750,000,000-byte ceiling.

## Prospective precision decision

| Experiment | Final replications | Decision | Interpretation boundary |
|---|---:|---|---|
| E1 cardinal margins | 64 | `PRECISION_FAILED` | The four reversal-probability contrasts passed, but all four allocation-L1 intervals missed the frozen target. |
| E2 operational constraints | 16 | `PRECISION_PASSED` | All 24 registered contrasts passed; direct forcing, inactive, and marginal-pressure cells are all present. |
| E3 CVaR frontier | 64 | `PRECISION_FAILED` | Nineteen of 27 contrasts passed; eight allocation/CVaR contrasts in stronger tail regimes did not. |
| E4 dependence | 64 | `PRECISION_FAILED` | Three of 18 contrasts passed; 15 failed, including rows made incomplete by certified sample infeasibility. |
| E5 true-law diversification | 64 | `PRECISION_FAILED` | All 24 cross-law contrasts missed at least one frozen precision requirement. |
| E6 information × flexibility | 16 | `PRECISION_PASSED` | Positive, zero, and substitution interaction archetypes all passed. |

No seed, parameter, tolerance, estimand, interval rule, or stopping rule was
changed in response to these outcomes. E1, E3, E4, and E5 therefore remain
adverse results, not candidates for selective numerical promotion.

## Rejected execution disclosure

A pre-run smoke execution and the first full execution were rejected for
implementation/accounting defects. The full execution used the same frozen
design but incorrectly recomputed a CVaR subgradient for its pairwise KKT ledger
and treated 14 sample-level infeasibilities as unexplained solver failures.
After code-only remediation, all 14 were independently certified by minimum-CVaR
solves and the LP's own dual tail weights closed the ledger. The accepted rerun
did not alter scientific settings or rescue any precision failure. The complete
record is `simulation/stage_ii/execution_deviation_log.md`.

## Mechanism results that survived their declared gates

- E2 identifies the predeclared operational boundary trichotomy. Across its
  144 pressure rows, the registry contains 32 direct-forcing, 32 inactive, and
  80 marginal-pressure cases. Every treated face has selected, possible, and
  universal Corn–Soybean reversal; the base face has none.
- E6 preserves the exact ignore-signal lower bound and the constructive
  Blackwell garbling check. Its stochastic interaction estimates are positive
  for `specialization_unlocks`, exactly null for `dominated_option_null`, and
  negative for `robust_option_substitutes`. Thus strict complementarity is
  parameter-dependent rather than general.
- The counterfactual package evaluates all 16 coherent subsets and all 24 block
  orders for each of 16 attribution seeds. Shapley efficiency closes to
  `1.4210854715202004e-14`.
- The pressure ledger closes to a maximum absolute stationarity residual of
  `1.8189894035458565e-11`. These are local KKT pressures, not acreage-causal
  shares.

## Infeasibility and model-risk boundary

There are 206 registered infeasible rows: 192 deliberately sub-minimum E3
anchors and 14 E4/E5 sample-level failures independently certified by a
minimum-CVaR solve. The latter comprise ten E4 and four E5 rows. Their positive
infeasibility margins are retained in `raw_replications.csv`; they are not
converted into optimal policies or omitted from precision accounting.

E5 evaluates assumed-law policies on independent true-law draws and records
true-law risk violation before feasible regret. Its precision gate failed, so
the observed cross-family patterns remain model-sensitivity diagnostics. No
Gaussian/Student-t/Clayton/empirical global loss ordering is claimed.

## Numerical and lineage acceptance

- 12 of 12 reverse-experiment-order replay signatures match.
- 9 of 9 `highs`, `highs-ds`, and `highs-ipm` sensitivity rows pass.
- Zero nonregistered solver failures remain.
- Scenario streams, seeds, hashes, generator family, marginal family, purpose,
  and dependence scope are recorded for all 1,632 registry rows.
- Every governed output is covered by `SHA256SUMS.txt`.
- The teacher TeX, teacher PDF, canonical panel, and manuscript-tree hashes are
  unchanged. No figure or manuscript file was generated or rewritten.

## Claim classification

The controlled package classifies all 15 theory results. Nine are `SUPPORTED`,
one is `PARAMETER_DEPENDENT`, one is `NOT_IDENTIFIED`, and four are
`PRECISION_FAILED` (`S2-H01`, `S2-P04`, `S2-H02`, and `S2-P08`). “Supported”
here means supported within the declared synthetic simulation scope; it is not
empirical or causal evidence.

## Reproduction and gate

Run from the repository root:

```bash
uv run --python 3.11 python scripts/run_stage_ii_confirmatory.py
uv run --python 3.11 python scripts/validate_stage_ii_confirmatory.py
uv run --python 3.11 pytest -q tests/test_stage_ii_confirmatory_engine.py
```

The next action is supervisor review of Issue #22. GOAL-13 must remain stopped
until explicit approval defines which precision-passing or exact-boundary
source-data rows, if any, may be promoted into figures.
