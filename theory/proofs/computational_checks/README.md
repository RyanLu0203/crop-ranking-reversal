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
