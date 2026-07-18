# Issue #6 acceptance report

## Outcome

PASS for execution, reproducibility, numerical integrity, adverse-result retention, and claim governance. FAIL for headline simulation use under the frozen convergence rule. This mixed outcome is the required scientific conclusion, not an implementation failure.

## Acceptance evidence

- Frozen design/protocol hashes: `4b5897f5...055b27` and `ca4f0b86...370048`.
- 90 cells, 450 primary replications, 4.5 million scenario rows, four benchmark policies, and 50 convergence solves completed by one command.
- 450/450 primary solves optimal; 450/450 independent reverse-order replays pass; 9/9 solver-method comparisons pass.
- Maximum KKT primal/stationarity residuals `6.08e-11`/`4.15e-12`; maximum direct CVaR violation `3.87e-12`.
- Representative peak memory 0.2405 GB under the frozen 0.5 GB cap; full formal/replay wall time about 281 seconds.
- Null, slack, nonmonotone, mixed-factor, and convergence-failure results retained.
- 47/47 formal-result audit checks pass and the complete repository test suite passes 105 tests.

## Result boundary

Thirty cells (150 replications) exhibited universal reversal and 60 cells did not, but zero of five convergence-grid rows passed. These results are versioned formal simulation outputs but are not admissible as headline evidence. They must not be called empirical evidence and must not be used to claim a unique dependence threshold.

## Reproduction

```bash
python scripts/run_formal_simulation.py --validation-only
python scripts/run_formal_simulation.py --workers 4
python scripts/audit_simulation_resources.py
python scripts/validate_formal_simulation.py
```
