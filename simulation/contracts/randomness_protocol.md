# Randomness and convergence protocol

The formal experiment uses the five immutable seeds `2026071901` through `2026071905`. Each seed identifies a complete replication. Within a named ordered-family comparison, cell construction reuses the same seed so marginal innovations are held as closely as the sampler permits; uncertainty is still assessed across all five replications. Cross-family comparisons are sensitivity analyses, not dependence-order proofs.

The primary scenario count is 10,000. Convergence is separately assessed at 1,000, 2,500, 5,000, 10,000, and 25,000 scenarios with ten replications spawned from root `2026071950`. A cell passes only if at least 80% of replications satisfy all of: allocation L1 difference at most 0.01, CVaR relative difference at most 0.02, objective relative difference at most 0.01, and reversal-probability interval width at most 0.10. Failure falsifies the cell for headline use; it does not authorize more favorable seeds or an unversioned scenario-count change.

The three 64-scenario files in `simulation/dry_run/` exercise serialization, all copula dispatch paths, LP/KKT diagnostics, and optimal-face code only. They are not part of the formal seed stream and are manuscript-inadmissible.
