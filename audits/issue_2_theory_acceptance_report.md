# Issue #2 theory acceptance report

Date: 2026-07-19

Branch: codex/issue-2-theory-repair
Issue: https://github.com/RyanLu0203/crop-ranking-reversal/issues/2

## Deliverable audit

| Contract item | Canonical evidence | Result |
|---|---|---|
| Repaired theorem set | theory/repaired/canonical_theorem_set.md and .tex | PASS |
| Complete proofs and counterexamples | theory/repaired/proofs.md | PASS |
| Assumptions/definitions/notation crosswalk | 50 rows in assumptions_definitions_notation_crosswalk.csv | PASS |
| Every Draft result dispositioned | R01–R31 exactly once in theorem_transition_registry.csv | PASS |
| Bilingual supervisor explanation | supervisor_memo_en.md and supervisor_memo_zh.md | PASS |
| Theory-to-simulation contract | CT1–CT10 exactly once in theory_to_simulation_map.csv | PASS |
| Theory-to-empirical contract | CT1–CT10 exactly once in theory_to_empirical_map.csv | PASS |
| Full-text external method verification | Three THEORY_FOUNDATION_ONLY records; all full_text_verified=YES | PASS |
| Teacher Draft immutability | TeX and PDF SHA-256 checks in repository validator | PASS |
| Multi-crop architecture retained | n-crop profit, X, valid n-copula, loss-CVaR, and full dual system | PASS |

## Invalid general claims removed

- The wrong upper-profit-tail CVaR identity is replaced by loss CVaR.
- No marginal KKT inequality is asserted to be equivalent to acreage-level reversal.
- No scalar lower-tail coefficient is used to order arbitrary copulas.
- No general unique threshold is claimed; reversal regions and crossing sets are used.
- Pseudo-diversification remains a diagnostic rather than an optimizer or welfare theorem.
- Information value and flexibility are weakly monotone under stated admissibility/nesting; strict supermodularity is not a general theorem.
- The CT6 local certificate requires slack risk, a strictly negative derivative at a binding boundary, or a directly verified feasible step. A zero derivative alone is expressly rejected.

## Automated validation

Command:

    uv run --python 3.11 python scripts/validate_theory_repair.py

Result:

    repaired_files=11 canonical_results=10 transitions=31 crosswalk_rows=50 theory_sources=3 failures=0

Targeted mathematical tests:

    uv run --python 3.11 pytest -q tests/test_theory_repair_registry.py theory/proofs/computational_checks/test_theory_audit.py

Result: 14 passed, 0 failed.

Repository-wide tests:

    uv run --python 3.11 pytest -q

Result: 70 passed, 0 failed.

## Independent TeX compile and visual QA

Command:

    python3 /Users/luxinyu/.codex/plugins/cache/openai-bundled/latex/0.2.4/scripts/compile_latex.py /Users/luxinyu/Desktop/论文\ 1/crop-ranking-reversal/theory/repaired/canonical_theorem_set.tex --compiler texlive --output-directory /Users/luxinyu/Desktop/论文\ 1/crop-ranking-reversal/theory/repaired/compiled --json

Result: latexmk/pdflatex exit code 0 after the required rerun; PDF exists at theory/repaired/compiled/canonical_theorem_set.pdf.

Rendered output: 4 US-letter pages, no missing text, clipping, overlap, broken equations, or unresolved references across the four inspected page images. The log contains one visually immaterial overfull box of 0.48692 pt.

## Supervisor confirmations carried forward

The English and Chinese memos recommend confirmation of:

1. solution-set-aware reversal definitions;
2. crossing sets rather than a presumed unique threshold;
3. family/domain-conditional dependence claims;
4. pseudo-diversification as a diagnostic label; and
5. actionability plus weak flexibility monotonicity as the main information results.

These decisions affect emphasis and permitted wording; they do not leave a mathematical proof gap in the canonical package.
