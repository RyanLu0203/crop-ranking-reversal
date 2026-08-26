# Selection-aware M0--M4 counterfactual attribution

## Estimand boundary

KKT pressure explains a local first-order balance. Acreage attribution instead
compares complete model solutions. These are different estimands and must be
stored in different output fields.

## Nested ladder

Each replication uses one frozen exogenous input bundle wherever mathematically
coherent.

| Stage | Model content | Required fallback and boundary |
|---|---|---|
| M0 | ordinal recommendation mapping | preserve the original recommendation and report any feasibility repair separately |
| M1 | cardinal expected-margin optimization with land and minimal domain bounds | margin vector and score-order relationship frozen before results |
| M2 | M1 plus budget, rotation, contracts and crop bounds | each operational block can be toggled individually and jointly |
| M3 | M2 plus loss-CVaR constraint | alpha, kappa, loss sign and direct/epigraph CVaR frozen |
| M4 | M3 under named assumed and true dependence laws | fixed marginals; paired evaluation draws; cross-family comparisons labelled sensitivity |

M0 is not an optimizer by definition. Its raw and feasibility-repaired outputs
must be distinguished. M1--M4 use the same deterministic optimizer-selection
rule plus an optimal-face audit.

## Primary path accounting

The primary order is M0 → M1 → M2 → M3 → M4 because it follows the scientific
argument from ordinal recommendation to cardinal objective, operations, risk
and dependence. For outcome vector \(Y\), report

\[
\Delta_k^{\text{path}}=Y(M_k)-Y(M_{k-1}).
\]

The sum telescopes to \(Y(M_4)-Y(M_0)\), but the increments are path dependent.
Report allocations, expected profit, direct true-law CVaR, risk violation,
reversal class and optimal-face contrast ranges—not acreage alone.

## Symmetric block attribution

For the four toggleable optimization blocks

\[
\mathcal B=\{\text{margins},\text{operations},\text{risk},\text{dependence}\},
\]

define a coherent value \(F(S)\) for all 16 subsets before inspecting outcomes.
Every absent block has a preregistered fallback. Apply the vector Shapley formula
in equation (S2.2) of `canonical_theory_extension.md` to the deterministic
selected outcomes.

Required validation:

- all 16 subsets exist and solve or are explicitly infeasible;
- the same selection, seed stream and tolerance contract is used;
- each block's Shapley vector is invariant to enumeration order;
- the block vectors sum to the full-minus-baseline selected change;
- infeasible subsets are not silently repaired; the attribution is undefined
  for that cell unless a predeclared common feasibility domain applies.

## Multiplicity and order uncertainty

For every subset and pairwise contrast, audit the objective-equivalent face.
Primary output uses the frozen deterministic selection. Sensitivity output must
include:

- minimum and maximum pairwise acreage gap on each face;
- possible/universal/selected reversal;
- alternative prespecified paths or all 24 block orders;
- minimum/maximum attribution over jointly generated alternative selections,
  or a clear statement that separate envelope endpoints are not jointly
  attainable.

An attribution interval crossing zero is mechanism uncertainty, not a positive
effect. A selected nonzero effect with a wide optimal face cannot be promoted as
selection-robust.

## Output contract for GOAL-12

Each tidy row must contain:

- experiment, cell, replication and subset/path identifiers;
- design/configuration/scenario checksums;
- selection rule and optimal-face status;
- block present/absent indicators and fallback identifiers;
- allocation by crop and pairwise gaps;
- expected profit, loss VaR/CVaR, risk violation and concentration;
- path increment or Shapley block vector;
- order/selection sensitivity bounds;
- evidence status and falsification status.

No Stage II theory artifact contains a calibrated output or claimed block size.
