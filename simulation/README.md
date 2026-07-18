# Simulation

The formal numerical design is frozen in `configs/experiment_design.yaml` before Issue #6. `experiment_design.py` expands exactly 72 balanced LHS cells and 18 preregistered anchors. All formal seed streams, scenario counts, tolerances, convergence criteria, resource limits, and falsification rules are versioned there.

`base_config.yaml` is only a 64-scenario engine smoke test. Its panel moments and costs are traceable to Issue #4; its operational and risk constraints are illustrative and manuscript-inadmissible. The imported result-driven functions in `stress_calibration.py` are disabled: formal ranges or regimes may not be selected after outcomes are observed.
