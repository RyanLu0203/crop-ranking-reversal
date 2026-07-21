# Computational theory checks

`test_theory_audit.py` contains deterministic synthetic tests only. They are mathematical witnesses, not empirical or Monte Carlo findings. The checks cover:

- wrong-tail CVaR sign;
- multiple optima and reversal selection dependence;
- CVaR slack, binding, and infeasible limits;
- same Gaussian tail coefficient with different portfolio CVaR;
- repeated parametric-LP basis/ranking changes;
- low-correlation exclusion and high-dependence inclusion edges;
- zero information value under a common policy.

Run from the repository root:

```bash
pytest -q theory/proofs/computational_checks/test_theory_audit.py
```

All arrays and constants are deliberately small and declared in the test file. Passing tests establish the counterexamples and implementation conventions only; they do not validate the teacher draft's numerical sections.

`test_stage_ii_theory.py` adds deterministic GOAL-14 witnesses for the restricted top-rank anchor, exact KKT pressure accounting, all-subset Shapley efficiency, risk-limit value contraction, non-equivalent diversification criteria, information garbling and the flexibility-substitution boundary. Its helper is `stage_ii_mechanism_checks.py`.

Run the full theory check set from the repository root:

```bash
uv run --python 3.11 pytest -q tests theory/proofs/computational_checks
```

These remain `SYNTHETIC_CHECK_ONLY`; they do not estimate a crop parameter, establish an empirical mechanism or execute the confirmatory simulation.
