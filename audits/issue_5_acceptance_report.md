# Issue #5 acceptance report

## Outcome

PASS. The experiment design is frozen before formal execution, inherited result-driven calibration is disabled, the stochastic/optimization engine implements the repaired theory contract, the smoke outputs are deterministic and explicitly inadmissible as results, and the repository-wide gate passes.

## Acceptance evidence

- Exactly 90 frozen design cells: 72 balanced LHS cells and 18 anchors.
- Five formal seeds, a 10,000-scenario primary count, a five-count convergence grid, ten convergence replications, and hard pass/falsification rules.
- All empirical moments/costs link to the Issue #4 panel; all risk/operational choices retain `ILLUSTRATIVE_ONLY` labels.
- Gaussian, Student-t, Clayton, Gaussian/t/empirical marginals, normalized land, budget, bounds, rotation, contracts, and four benchmarks implemented.
- Named active constraints, duals, KKT residuals, atom-safe tail weights, optimal-face reversal classes, crossing sets, pseudo-diversification, and information/flexibility metrics implemented.
- Independent RU and two-crop enumeration oracles plus risk-slack, binding-risk, multiple-optimum, infeasible-contract, multiple-crossing, and exact-repeat tests.
- Three smoke cells are finite, byte-repeatable, solver-optimal, and marked `manuscript_admissible=NO`.
- Formal resource budget: 450 primary solves, 50 convergence solves, 4.5 million scenario rows, at most four workers.
- Canonical manifest validation passed with 167 assets and 168 checksum entries; the full suite passed 101 tests.

## Formal-run boundary

No formal experiment or results section was produced. Issue #6 must execute the frozen design without silent adaptation, record observed resource usage, quantify Monte Carlo/bootstrap uncertainty, and quarantine every failed convergence or falsification cell.
