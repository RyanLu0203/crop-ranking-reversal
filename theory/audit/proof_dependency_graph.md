# Proof dependency graph

```mermaid
flowchart TD
  P["Integrable profit scenarios"] --> L["Loss L = -profit"]
  X["Nonempty compact linear feasible set"] --> E["Existence"]
  L --> RU["RU CVaR representation"]
  RU --> C["Convexity / finite-scenario LP"]
  X --> C
  C --> K["Full KKT or LP primal-dual certificate"]
  Q["Constraint qualification / LP duality"] --> K
  K --> S["Risk-adjusted stationarity"]
  U["Unique optimizer or selection rule"] --> A["Single-valued allocation comparison"]
  S --> A
  B["All budget, rotation, and bound normals"] --> S
  F["Fixed marginals + named copula family"] --> O["Verified distributional ordering"]
  O --> M["Conditional dependence comparative static"]
  A --> T["Threshold statement"]
  M --> T
  N["Continuity + endpoint crossing + strict monotonicity"] --> T
  D["Signal timing + posterior expectations"] --> V["Coherent information value"]
  CP["Common signal-contingent optimal policy"] --> Z["Zero operational information value"]
  V --> Z
  LAT["Lattice + increasing differences + monotone selection"] --> IF["Information-flexibility complementarity"]
  V --> IF
```

The teacher draft reaches allocation ordering from `S`, threshold uniqueness without `U`, `O`, or `N`, and complementarity without `LAT`. Those missing branches are substantive proof gaps, not stylistic omissions.
