# Figure plan and contracts

## Global journal/export contract

- Target: Nature Food-style research article candidate figures.
- Backend: Python/matplotlib exclusively for drawing, previewing, export, grayscale, and visual QA.
- Final width: 183 mm double column; heights 105–150 mm by figure.
- Exports: editable-text SVG, TrueType-text PDF, 600-dpi TIFF, and 300-dpi PNG preview.
- Source data: generated CSVs copied or derived only from verified Issue 6/7 tidy outputs, with SHA-256 lineage.
- Statistics: descriptive rates and empirical replication ranges only; no independence-based p-values. Simulation uncertainty is five-seed MCSE/range and carries the failed-convergence boundary.
- Image integrity: no photographs or microscopy; no crop/contrast/gamma adjustments. Grayscale copies are QA derivatives only.

## Figure 1 — From rank to allocation

Core conclusion: ordinal crop rankings do not uniquely determine constrained allocations, and observed acreage cannot identify the intervening mechanism.

- Archetype: schematic-led composite.
- Panel a: recommendation → cardinalization → operational/risk feasible set → optimal face → selected allocation.
- Panel b: selected, possible, and universal reversal definitions on the optimal-face difference interval.
- Panel c: theory, simulation, and empirical evidence paths with explicit admissibility boundaries.
- Evidence hierarchy: repaired theory is primary; simulation/empirical boxes define validation limits.
- Reviewer risk: conceptual arrows must not imply causal identification; every transition is labeled as a model step or evidence boundary.

## Figure 2 — Empirical discordance is common but definition-sensitive

Core conclusion: state-level score–acreage discordance is frequent in the selected sample but varies materially by ranking definition, while national rankings show a retained null.

- Archetype: asymmetric quantitative grid.
- Panel a (hero): state × ranking-definition heatmap of three-year top-rank discordance rates; cell text gives rate and years.
- Panel b: top and strong discordance rates by four preregistered definitions, `n=77` state-years; exact-permutation top benchmark shown as a combinatorial reference.
- Panel c: operating-margin top discordance by year with visible state counts; national null shown separately as `0/9` crop-years.
- Statistics: descriptive rates only; no p-values or confidence intervals because state-years are clustered and the permutation benchmark is not a sampling null.
- Reviewer risk: complete-case state selection, national-input accounting, and observed-acreage-not-optimum qualifications must remain in caption/source notes.

## Supplementary Figure S1 — Formal simulation landscape and mechanisms

Core conclusion: the frozen mixed-factor simulation contains both reversal and no-reversal cells, with risk and operational constraints alternating between binding and slack.

- Archetype: quantitative grid.
- Panels a–c: Kendall-tau/risk-quantile phase scatter within Gaussian, Student-t, and Clayton families; marker shape distinguishes marginal family and fill distinguishes universal reversal.
- Panel d: binding frequency for land, budget, CVaR, rotation, contract, and bounds across 450 replications.
- Statistics: five-seed cell classifications and replication frequencies.
- Reviewer risk: mixed factors prevent causal threshold interpretation; panel title and caption must say `not a threshold` and `non-headline`.

## Supplementary Figure S2 — Reproducible but non-converged

Core conclusion: the formal run is computationally reproducible and numerically precise but fails every preregistered convergence row.

- Archetype: quantitative grid.
- Panel a: numeric convergence-pass fraction vs scenario count with required 0.80 line.
- Panel b: reversal-probability Wilson width vs required 0.10 line; unanimous-state width 0.2775 remains visible.
- Panel c: log-scale numerical audit residuals against frozen tolerances plus replay/solver pass counts.
- Reviewer risk: reproducibility must not be visually conflated with scientific convergence.

## Supplementary Figure S3 — Empirical temporal and definition robustness

Core conclusion: qualitative definition sensitivity persists across leave-one-year-out summaries, while the low-powered leakage-free 2024 check remains explicitly limited.

- Archetype: quantitative grid.
- Panel a: leave-one-year-out top-discordance rate by definition.
- Panel b: distribution of pairwise inversions in the 25-state leakage-free 2024 check.
- Panel c: exact national margin/acreage rank alignment for 2022–2024.
- Reviewer risk: only two training years support panel b; national and state scales must not be pooled.

## Candidate tables

- Main Table 1: sample flow and four ranking-definition summaries.
- Supplementary Table S1: simulation completion, residual, binding/slack, and convergence gates.
- Supplementary Table S2: identified, accounting-only, not-identified, and not-applicable empirical claims.

