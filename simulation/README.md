# Simulation

The formal numerical design is frozen in `configs/experiment_design.yaml` before Issue #6. `experiment_design.py` expands exactly 72 balanced LHS cells and 18 preregistered anchors. All formal seed streams, scenario counts, tolerances, convergence criteria, resource limits, and falsification rules are versioned there.

`base_config.yaml` is only a 64-scenario engine smoke test. Its panel moments and costs are traceable to Issue #4; its operational and risk constraints are illustrative and manuscript-inadmissible. The imported result-driven functions in `stress_calibration.py` are disabled: formal ranges or regimes may not be selected after outcomes are observed.

Issue #6 operationalization is frozen in `configs/formal_run_protocol.yaml`. Run the two-cell non-admissible validation with `python scripts/run_formal_simulation.py --validation-only`, then reproduce the formal outputs with `python scripts/run_formal_simulation.py --workers 4`. `outputs/SHA256SUMS.txt` covers every generated result/log artifact.

The run completed and independently replayed all 450 primary replications, but the preregistered convergence gate failed at every scenario count. Therefore `outputs/summary.json` records `headline_admissible=false`; the outputs are governed sensitivity evidence, not empirical evidence or headline simulation support.
