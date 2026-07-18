# Convexity and regularity audit

The reconstructed problem is convex: scenario loss is affine in acreage; the RU CVaR functional is convex; and all physical constraints are linear. With finite scenarios it is an LP. This validates global optimality certificates but does not validate the teacher's acreage-ordering theorem.

## What is sufficient

- Nonempty compact $X$ plus integrable profits gives existence.
- A convex constraint qualification gives KKT necessity and sufficiency. In the finite LP, feasibility and boundedness support primal-dual optimality through LP strong duality.
- Differentiability of CVaR requires more: locally unique tail membership/no mass at VaR. Scenario models commonly violate it, so subgradients are the default.

## What is not guaranteed

- Strict convexity: the objective and finite-scenario formulation are linear, so multiple optima are ordinary.
- Unique $v$: atoms can create a VaR interval.
- A continuous allocation path as a copula parameter changes: LP optimizers can jump when the optimal basis changes.
- A unique reversal threshold: even a continuous value function need not give a continuous, single-valued optimizer.
- Full land use: CVaR, budget, rotation, upper bounds, or negative expected margins can make idling optimal.

## Required diagnostics

Each numerical solve must report feasibility, primal residual, objective, empirical and epigraph CVaR, active constraints, duals, lower/upper-bound status, and a multiple-optimum audit. Threshold analysis must retain all optimizers (or document a deterministic secondary objective), locate active-set changes, and distinguish no crossing, point crossing, interval crossing, and multiple crossings.
