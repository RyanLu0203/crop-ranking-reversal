# Teacher draft model audit summary

## Baseline integrity

Audited immutable assets:

- `baselines/teacher_draft/Crop_ranking_reversal_total.tex`
- `baselines/teacher_draft/Crop_ranking_reversal_total.pdf`

Pre-audit SHA-256:

- TeX: `e8885aa89be6a6010f0d3e6f8e40b4b8192a91fc90f6ca4fb16ae9b0aa9dd26c`
- PDF: `52ac1b4ef21c8d406fd6d722c877935a24d2cc6ea68520a6f35470ba8b334b44`

Post-audit hashes must match and are checked during validation.

## Audit outcome

The teacher model's finite-scenario optimization core is salvageable as a convex LP. The continuous CVaR definition uses the wrong profit tail, and the marginal formula uses the wrong quantile cutoff and lacks atom/subgradient qualifications. The KKT display is incomplete because it omits budget and rotation/shared constraints.

The ranking-reversal iff theorem, global tail-dependence monotonicity proposition, unique-threshold theorem, pseudo-diversification optimizer proposition, and strict information-flexibility complementarity theorem are false in general. Each has a minimal restricted replacement in the audit package. No teacher numerical result is admitted.

## Deliverables

- Canonical specifications and registries: `theory/specifications/`
- Per-result taxonomy and proof gaps: `theory/audit/`
- Proofs and deterministic witnesses: `theory/proofs/`
- Change boundary: `THEORY_CHANGE_LOG.md`
- Method sources: `evidence_registry/literature_registry.csv`

## Evidence boundary

The audit uses source material only to establish the CVaR optimization foundation and the need for explicit copula ordering. It does not promote agricultural parameters, empirical estimates, allocations, thresholds, or welfare claims.
