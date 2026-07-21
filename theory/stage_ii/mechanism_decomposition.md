# KKT pressure and operational mechanism framework

## Purpose

This framework turns the repaired CT5 stationarity equation into a complete,
dimensionally explicit diagnostic for GOAL-12. A KKT term is not an additive acreage cause,
and the framework does not turn dual variables into causal
acreage contributions.

## Pairwise pressure ledger

For an ordered crop pair \((i,j)\), use the canonical minimization-Lagrangian
signs and report:

| Field | Formula | Unit | Directional interpretation |
|---|---|---|---|
| `margin_pressure` | \(M_{ij}=\mu_i-\mu_j\) | currency/acre | objective benefit of replacing one acre of \(j\) by \(i\) |
| `tail_risk_pressure` | \(R_{ij}=\lambda(d_i-d_j)\) | currency/acre | risk shadow cost differential |
| `budget_pressure` | \(B_{ij}=\beta(c_i-c_j)\) | currency/acre | liquidity-resource shadow cost differential |
| `shared_pressure` | \(O_{ij}=(G^\top\eta)_i-(G^\top\eta)_j\) | currency/acre | rotation, contract and other shared-row differential |
| `boundary_pressure` | \(Q_{ij}=-(a_i-a_j)+(b_i-b_j)\) | currency/acre | lower/upper boundary normal differential |
| `stationarity_residual` | \(M_{ij}-R_{ij}-B_{ij}-O_{ij}-Q_{ij}\) | currency/acre | numerical closure error only |

The land multiplier is reported separately for level diagnostics but cancels in
this pairwise ledger because both crops use one unit of land per acre.

## Required inputs

Every pressure record must link to:

- crop names and pair orientation;
- selected allocation and optimal-face pairwise range;
- scenario/configuration/checksum identifiers;
- expected margins and their common monetary base;
- one CVaR subgradient or normalized tail-weight vector;
- risk, land, budget, every shared-row, lower-bound and upper-bound multiplier;
- slacks and active flags for all corresponding constraints;
- primal, dual, stationarity and complementarity residuals;
- solver name/version and frozen tolerances.

If the risk multiplier is zero, `tail_risk_pressure` is zero even when a CVaR
subgradient is nonunique. A binding flag derived only from rounded direct CVaR
does not replace complementary slackness and the solver dual.

## Sign and atom discipline

The tail subgradient uses loss \(L=-\Pi\). In finite scenarios,

\[
d=-\sum_s\xi_s\pi_s,
\quad 0\leq\xi_s\leq\frac{w_s}{1-\alpha},
\quad\sum_s\xi_s=1.
\]

At a VaR atom, multiple admissible \(\xi\) and \(d\) may exist. GOAL-12 must
either report a solver-certified selection and sensitivity interval or report
the pressure as set-valued. It must not convert an arbitrary conditional-tail
average into a unique derivative.

## Operational mechanism labels

Each operational row receives zero or more labels:

1. `DIRECT_FORCING`: a feasibility LP proves coordinate-range separation;
2. `MARGINAL_PRESSURE`: its certified multiplier and crop-column difference
   generate a nonzero pairwise pressure;
3. `BOUNDARY_SELECTION`: a crop bound or optimal face changes possible,
   universal or selected reversal;
4. `INTERACTION_ONLY`: its effect appears only in a controlled block interaction;
5. `INACTIVE_IN_CELL`: slack and zero multiplier within tolerance.

A row may be binding but create zero pairwise pressure when its two crop
coefficients are equal. Conversely, a collection of constraints can directly
force reversal even when a selected degenerate dual assigns one row a zero
multiplier. Report both feasible geometry and dual pressure.

## Non-admissible transformations

- Do not divide terms by their signed sum to create percentage causes.
- Do not infer acres from currency-per-acre pressures.
- Do not compare terms from inconsistent monetary bases or acreage units.
- Do not pool multiplier values across basis changes without reporting the
  active set and face width.
- Do not call a pressure observed farmer preference or causal effect.

Selected acreage attribution is defined separately in
`counterfactual_attribution_specification.md`.
