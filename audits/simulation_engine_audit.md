# Simulation and optimization engine audit

| Theory item | Implementation | Independent or boundary check | Status |
|---|---|---|---|
| CT1 finite CVaR LP | `cvar_optimizer.py` | direct atom-safe evaluator and enumerated RU oracle | verified on synthetic cases |
| CT2 ordinal insufficiency | ranking-proportional benchmark plus cardinal alternatives | multiple-optimum optimal-face test | mechanism-ready |
| CT3 forced reversal | rotation caps, bounds, contract rows | universal face-range test | verified |
| CT4 risk slack | CVaR dual/slack diagnostics | EO and slack-CVaR allocation identity test | verified |
| CT5 full KKT | named constraints, bounds, duals, atom-safe tail weights | residual and cap/sum tests | verified |
| CT6 feasible displacement | face-range finite LPs | no derivative-only certificate is emitted | boundary preserved |
| CT7 restricted dependence | Gaussian, t, Clayton with validated correlation | metadata says within named family only | boundary preserved |
| CT8 crossing sets | all grid transitions and disjoint regions | multi-crossing regression test | verified |
| CT9 pseudo-diversification | thresholded descriptive diagnostic | output says not welfare/exclusion | boundary preserved |
| CT10 information/flexibility | exact finite-state VOI and nested action sets | ignore-signal and weak-monotonicity assertions | verified |

The LP records land, budget, CVaR, per-scenario tail, rotation, contract, and variable-bound constraints. HiGHS marginals are sign-converted into nonnegative KKT multipliers. When the risk multiplier is positive, scenario tail weights are normalized by it and checked for nonnegativity, unit sum, and the `1/((1-alpha)S)` cap. When it is zero, tail weights are reported as unidentified rather than fabricated.

The optimal-face audit independently rebuilds the finite CVaR feasible system, adds the frozen objective-equivalence floor, and minimizes/maximizes each ranked pair's allocation difference. This prevents a solver-selected vertex from being mislabeled as a universal property.

The small grid oracle is deliberately limited to two crops and test instances. It is not used for formal computation; it checks the LP against exhaustive feasible enumeration. Invalid correlation matrices, nonfinite scenarios, invalid alpha/df/bounds, unknown crops, and infeasible contracts fail explicitly.
