# Issue #21 acceptance report

## Outcome

GOAL-11 produces a complete Stage II scientific reconstruction blueprint from
the frozen Stage I baseline `4d6c14d`. It does not rewrite the manuscript or
execute later phases. The package diagnoses the current scientific evidence,
defines positive theory targets, redesigns confirmatory simulation and empirical
validation, specifies six evidence-gated figure groups, and maps the final
manuscript argument.

## Acceptance evidence

- Five canonical research questions have end-to-end theory, simulation,
  empirical, figure and manuscript mappings.
- Twelve theory gaps distinguish positive research targets from repaired Draft
  boundaries.
- Seven controlled confirmatory simulation families replace reliance on the
  mixed-factor Stage I pilot.
- Seven empirical estimand families prioritize longer time support, transitions,
  decision timing, holdouts, aggregation and explicit observability layers.
- Six main figure contracts remain blocked until their theory/simulation/
  empirical source-data gates pass.
- Nine target manuscript sections have individual evidence gates and a final
  no-rewrite-before-evidence rule.
- Fourteen GOAL-11 requirements are recorded in a fail-closed acceptance matrix.

## Preserved boundaries

No historical Draft number is restored. Stage I simulation outputs remain
nonheadline; Stage I empirical acreage remains descriptive rather than an
optimizer; cross-family copula comparisons remain model sensitivity; KKT terms
remain local optimality pressures rather than causal acreage contributions; and
observational model consistency remains distinct from causal identification.

## Reproduction

```bash
uv run --python 3.11 python scripts/validate_stage_ii_blueprint.py
make check
```

## Stop decision

STOP after Issue #21. GOAL-14 / Issue #24 is the next permitted phase, but it
must not begin until the supervisor validates this reconstruction blueprint.
