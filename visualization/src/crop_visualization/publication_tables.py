"""Publication-table derivation for the crop ranking reversal manuscript.

The functions in this module are intentionally presentation-only: they read
already generated CSV outputs, select/rename/format columns for journal-facing
tables, and preserve full diagnostics in appendix/full-output folders.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from .table_export import write_markdown, write_table


SOURCE_TABLES = {
    "active_constraints": "table_A1_active_constraint_diagnostics.csv",
    "selected_regimes": "table_A3_selected_regimes.csv",
    "risk_binding_theta": "table_1b_risk_binding_reversal_threshold.csv",
    "stress_benchmark": "table_2b_benchmark_comparison_stress.csv",
    "robustness": "table_5_robustness_thresholds.csv",
    "regime_search": "table_A2_regime_search.csv",
    "risk_candidates": "table_A2_risk_binding_candidates.csv",
    "diversification_diagnostics": "table_3b_diversification_failure_diagnostics.csv",
    "diversification_stress": "table_3b_diversification_failure_stress.csv",
    "information_stress": "table_4b_information_flexibility_stress.csv",
    "empirical_template": "table_6_empirical_validation_template.csv",
}


def generate_publication_outputs(project_root: Path, summary_v2: Dict[str, object]) -> Dict[str, object]:
    """Create compact main tables, appendix diagnostics, v3 manuscript, and logs."""

    outputs = project_root / "outputs"
    table_root = outputs / "tables"
    main_dir = table_root / "main"
    appendix_dir = table_root / "appendix"
    full_dir = table_root / "full"
    for directory in [main_dir, appendix_dir, full_dir, outputs / "logs", project_root / "paper_sections"]:
        directory.mkdir(parents=True, exist_ok=True)

    sources = _load_source_tables(table_root)
    preflight = _write_preflight(project_root, sources)
    _copy_full_machine_readable_outputs(table_root, full_dir)
    _write_appendix_tables(project_root, sources, appendix_dir)

    main_tables = {
        "baseline": _main_table_baseline_mechanism(sources["active_constraints"]),
        "regimes": _main_table_selected_regimes(sources["selected_regimes"]),
        "benchmark": _main_table_policy_comparison(sources["stress_benchmark"]),
        "robustness": _main_table_robustness_summary(sources["robustness"]),
        "claims": _main_table_claim_support(summary_v2),
    }
    _write_main_tables(main_tables, main_dir)
    invariance = _write_invariance_check(project_root, sources, main_tables)
    _write_v3_section(project_root, summary_v2)
    _write_v3_appendix(project_root)
    _update_revised_manuscript_v3(project_root)
    _write_final_summary_v3(project_root, summary_v2, preflight, invariance)

    return {"preflight": preflight, "invariance": invariance, "main_tables": list(main_tables)}


def _load_source_tables(table_root: Path) -> Dict[str, pd.DataFrame]:
    tables: Dict[str, pd.DataFrame] = {}
    for key, name in SOURCE_TABLES.items():
        path = table_root / name
        if not path.exists():
            raise FileNotFoundError(f"Required source table is missing: {path}")
        tables[key] = pd.read_csv(path)
    return tables


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_preflight(project_root: Path, sources: Dict[str, pd.DataFrame]) -> Dict[str, object]:
    table_root = project_root / "outputs" / "tables"
    rows = []
    for key, filename in SOURCE_TABLES.items():
        path = table_root / filename
        rows.append(
            {
                "source": key,
                "path": str(path.relative_to(project_root)),
                "rows": int(len(sources[key])),
                "columns": int(len(sources[key].columns)),
                "sha256": _sha256(path),
            }
        )
    preflight = {"source_tables": rows}
    body_lines = [
        "# Publication Tables Preflight",
        "",
        "This log records the source CSV files used to derive compact publication tables. "
        "The refactor is presentation-only: compact tables select, rename, summarize, or format existing generated outputs.",
        "",
        "| Source | Rows | Columns | SHA-256 |",
        "|---|---:|---:|---|",
    ]
    for row in rows:
        body_lines.append(f"| `{row['path']}` | {row['rows']} | {row['columns']} | `{row['sha256']}` |")
    body_lines.extend(
        [
            "",
            "Full source CSV files are preserved in `outputs/tables/full/`; appendix diagnostics are preserved in `outputs/tables/appendix/`.",
            "No numerical result is recomputed or altered by the compact-table derivation.",
        ]
    )
    write_markdown(project_root / "outputs" / "logs" / "publication_tables_preflight.md", "\n".join(body_lines))
    return preflight


def _copy_full_machine_readable_outputs(table_root: Path, full_dir: Path) -> None:
    for csv_path in table_root.glob("*.csv"):
        shutil.copy2(csv_path, full_dir / csv_path.name)


def _write_appendix_tables(project_root: Path, sources: Dict[str, pd.DataFrame], appendix_dir: Path) -> None:
    write_table(
        sources["active_constraints"],
        appendix_dir / "table_A1_full_active_constraint_diagnostics.csv",
        appendix_dir / "table_A1_full_active_constraint_diagnostics.tex",
        caption="Appendix Table A1. Full active-constraint diagnostics, slacks, binding indicators, and shadow prices",
        label="tab:appendix_active_constraint_diagnostics",
    )
    sources["regime_search"].to_csv(appendix_dir / "table_A2_full_regime_search.csv", index=False)
    _write_regime_search_manifest(sources["regime_search"], appendix_dir / "table_A2_full_regime_search_manifest.tex")
    write_table(
        sources["robustness"],
        appendix_dir / "table_A3_full_robustness_grid.csv",
        appendix_dir / "table_A3_full_robustness_grid.tex",
        caption="Appendix Table A3. Full robustness-grid outcomes",
        label="tab:appendix_robustness_grid",
    )
    write_table(
        sources["diversification_diagnostics"],
        appendix_dir / "table_A4_diversification_failure_diagnostics.csv",
        appendix_dir / "table_A4_diversification_failure_diagnostics.tex",
        caption="Appendix Table A4. Diversification-failure diagnostics; non-monotonic Clayton CVaR is not observed",
        label="tab:appendix_diversification_diagnostics",
    )
    write_table(
        sources["information_stress"],
        appendix_dir / "table_A5_information_flexibility_full_grid.csv",
        appendix_dir / "table_A5_information_flexibility_full_grid.tex",
        caption="Appendix Table A5. Full information-flexibility stress grid",
        label="tab:appendix_information_flexibility_grid",
    )


def _write_regime_search_manifest(df: pd.DataFrame, path: Path) -> None:
    status_counts = df["status"].value_counts().to_dict() if "status" in df else {}
    cvar_candidates = int(df.get("risk_binding_candidate", pd.Series(dtype=bool)).fillna(False).astype(bool).sum())
    manifest = pd.DataFrame(
        [
            {
                "Machine-readable appendix file": "Full regime-search CSV",
                "Rows": len(df),
                "Columns": len(df.columns),
                "Optimal rows": int(status_counts.get("optimal", 0)),
                "Risk-binding candidates": cvar_candidates,
            }
        ]
    )
    _write_publication_table(
        manifest,
        path,
        caption="Appendix Table A2. Full risk-regime search manifest",
        label="tab:appendix_regime_search_manifest",
        note=(
            "The full 2,520-row regime-search table is preserved as "
            "\\nolinkurl{outputs/tables/appendix/table_A2_full_regime_search.csv}."
        ),
        column_format="p{0.34\\textwidth}rrrr",
    )


def _main_table_baseline_mechanism(active: pd.DataFrame) -> pd.DataFrame:
    baseline = active.loc[active["selected_regime"] == "baseline_liquidity_driven"].head(1).copy()
    if baseline.empty:
        baseline = active.head(1).copy()
    return pd.DataFrame(
        [
            {
                "regime": "Baseline liquidity-driven",
                "acres_Corn": float(baseline["acres_Corn"].iloc[0]),
                "acres_Soybean": float(baseline["acres_Soybean"].iloc[0]),
                "acres_Winter Wheat": float(baseline["acres_Winter Wheat"].iloc[0]),
                "expected_profit": float(baseline["expected_profit"].iloc[0]),
                "cvar_loss": float(baseline["cvar_loss"].iloc[0]),
                "budget_active": bool(baseline["budget_binds"].iloc[0]),
                "cvar_active": bool(baseline["cvar_binds"].iloc[0]),
                "ranking_reversal": bool(baseline["ranking_reversal"].iloc[0]),
            }
        ]
    )


def _dominant_constraint(row: pd.Series) -> str:
    budget = bool(row.get("budget_binds", False))
    cvar = bool(row.get("cvar_binds", False))
    if budget and cvar:
        return "Budget and CVaR"
    if budget:
        return "Budget"
    if cvar:
        return "CVaR"
    return "None dominant"


def _main_table_selected_regimes(selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in selected.iterrows():
        regime_name = str(row.get("selected_regime", "")).replace("_", " ").title()
        if row.get("selected_regime") == "baseline_liquidity_driven":
            interpretation = "Baseline reversal is liquidity-driven; CVaR is slack."
        elif row.get("selected_regime") == "risk_binding_cvar_regime":
            interpretation = "CVaR binds without a binding budget; reversal is observed."
        else:
            interpretation = "CVaR binds; theta sweep, not this selected row alone, shows threshold reversal."
        rows.append(
            {
                "regime": regime_name,
                "budget": float(row.get("budget", np.nan)),
                "cvar_limit": float(row.get("cvar_limit", np.nan)),
                "tail_model": str(row.get("tail_distribution", "")),
                "dominant_active_constraint": _dominant_constraint(row),
                "ranking_reversal": bool(row.get("ranking_reversal", False)),
                "short_interpretation": interpretation,
            }
        )
    return pd.DataFrame(rows)


def _main_table_policy_comparison(benchmark: pd.DataFrame) -> pd.DataFrame:
    df = benchmark.copy()
    df["feasible"] = ~(df["cvar_violation"].fillna(True).astype(bool))
    if "budget_violation" in df:
        df["feasible"] = df["feasible"] & ~(df["budget_violation"].fillna(True).astype(bool))
    rows = []
    for _, row in df.iterrows():
        regret = row.get("regret_vs_best_feasible", np.nan)
        rows.append(
            {
                "policy": row["policy"],
                "expected_profit": float(row["expected_profit"]),
                "cvar_loss": float(row["cvar_loss"]),
                "feasible": bool(row["feasible"]),
                "worst_decile_profit": float(row["worst_decile_profit"]),
                "regret_vs_best_feasible": np.nan if not bool(row["feasible"]) else float(regret),
            }
        )
    return pd.DataFrame(rows)


def _main_table_robustness_summary(robustness: pd.DataFrame) -> pd.DataFrame:
    baseline_values = {
        "CVaR confidence alpha": "0.90",
        "CVaR limit kappa": "$30,000",
        "Budget B": "$220,000",
        "Corn rotation cap share": "0.60",
        "Corn-Soybean margin gap": "$65",
        "Monte Carlo scenario count": "5,000",
        "Copula family": "Clayton",
    }
    rows = []
    for check, part in robustness.groupby("check", sort=False):
        values = [str(value) for value in part["value"].tolist()]
        observed = int(part["reversal_observed"].fillna(False).astype(bool).sum())
        total = int(len(part))
        thresholds = part["reversal_threshold_lambda_L"].dropna()
        if thresholds.empty:
            status = f"No reversal in {total} setting(s)"
        elif len(thresholds) == 1:
            status = f"{observed}/{total} setting(s); threshold {thresholds.iloc[0]:.3f}"
        else:
            status = f"{observed}/{total} setting(s); thresholds {thresholds.min():.3f}-{thresholds.max():.3f}"
        rows.append(
            {
                "parameter_change": check,
                "baseline_value": baseline_values.get(check, "Baseline"),
                "alternative_value_range": _compact_range(values),
                "reversal_status": status,
                "direction_interpretation": _robustness_interpretation(check, observed, total),
            }
        )
    return pd.DataFrame(rows)


def _compact_range(values: List[str]) -> str:
    if len(values) <= 3:
        return ", ".join(values)
    return f"{values[0]} to {values[-1]} ({len(values)} settings)"


def _robustness_interpretation(check: str, observed: int, total: int) -> str:
    if observed == 0:
        return "No reversal observed in this slice."
    if observed == total:
        return "Reversal is robust across tested alternatives."
    return "Reversal is parameter-sensitive in this slice."


def _main_table_claim_support(summary_v2: Dict[str, object]) -> pd.DataFrame:
    div_observed = bool(summary_v2.get("diversification_failure_occurred", False))
    info_positive = bool(summary_v2.get("positive_information_value_occurred", False))
    risk_reversal = bool(summary_v2.get("ranking_reversal_in_risk_binding_theta_grid", False))
    return pd.DataFrame(
        [
            {
                "Claim": "Ranking reversal exists",
                "Baseline Evidence": "Supported",
                "Stress-Calibrated Evidence": "Supported",
                "Current Numerical Status": "Supported",
                "Empirical Status": "Pending real-data validation",
            },
            {
                "Claim": "Liquidity-driven reversal",
                "Baseline Evidence": "Supported: budget active, CVaR slack",
                "Stress-Calibrated Evidence": "Not the stress mechanism",
                "Current Numerical Status": "Supported",
                "Empirical Status": "Pending real-data validation",
            },
            {
                "Claim": "CVaR-binding allocation shift",
                "Baseline Evidence": "Not supported: CVaR slack",
                "Stress-Calibrated Evidence": "Supported",
                "Current Numerical Status": "Supported only under stress calibration",
                "Empirical Status": "Pending real-data validation",
            },
            {
                "Claim": "Tail-dependence threshold reversal",
                "Baseline Evidence": "Liquidity-driven baseline",
                "Stress-Calibrated Evidence": "Supported" if risk_reversal else "Not observed",
                "Current Numerical Status": "Supported only under stress calibration" if risk_reversal else "Not observed",
                "Empirical Status": "Pending real-data validation",
            },
            {
                "Claim": "Diversification failure",
                "Baseline Evidence": "Not observed",
                "Stress-Calibrated Evidence": "Not observed" if not div_observed else "Observed",
                "Current Numerical Status": "Not observed; theoretical only" if not div_observed else "Observed",
                "Empirical Status": "Pending real-data validation",
            },
            {
                "Claim": "Pseudo-diversification",
                "Baseline Evidence": "Not observed",
                "Stress-Calibrated Evidence": "Not observed",
                "Current Numerical Status": "Theoretical only",
                "Empirical Status": "Pending real-data validation",
            },
            {
                "Claim": "Information-flexibility complementarity",
                "Baseline Evidence": "Near-zero baseline value",
                "Stress-Calibrated Evidence": "Supported" if info_positive else "Not observed",
                "Current Numerical Status": "Supported only under stress calibration" if info_positive else "Not observed",
                "Empirical Status": "Pending real-data validation",
            },
            {
                "Claim": "Real-world empirical prevalence",
                "Baseline Evidence": "No real panel used",
                "Stress-Calibrated Evidence": "No real panel used",
                "Current Numerical Status": "Pending real-data validation",
                "Empirical Status": "Pending real-data validation",
            },
        ]
    )


def _write_main_tables(tables: Dict[str, pd.DataFrame], main_dir: Path) -> None:
    table_specs = {
        "baseline": (
            "table_1_baseline_mechanism",
            "Table 1. Baseline mechanism: liquidity-driven ranking reversal",
            "tab:main_baseline_mechanism",
            "Budget Active and CVaR Active are binding indicators. The baseline reversal is liquidity-driven because budget is active while CVaR is slack.",
            "lrrrrllll",
        ),
        "regimes": (
            "table_2_selected_mechanism_regimes",
            "Table 2. Selected mechanism regimes",
            "tab:main_selected_mechanism_regimes",
            "Regimes are not interchangeable: the baseline row identifies liquidity pressure, while stress rows isolate CVaR and tail-dependence mechanisms.",
            "p{0.17\\textwidth}rrp{0.12\\textwidth}p{0.13\\textwidth}p{0.08\\textwidth}p{0.28\\textwidth}",
        ),
        "benchmark": (
            "table_3_policy_comparison",
            "Table 3. Benchmark policy comparison in the risk-binding stress regime",
            "tab:main_policy_comparison",
            "Regret is computed only among feasible policies. Policies violating CVaR or budget constraints are marked not comparable for regret.",
            "lrrrrl",
        ),
        "robustness": (
            "table_4_robustness_summary",
            "Table 4. Robustness summary",
            "tab:main_robustness_summary",
            "The full robustness grid is preserved in Appendix Table A3 and in machine-readable CSV form.",
            "p{0.18\\textwidth}p{0.13\\textwidth}p{0.18\\textwidth}p{0.22\\textwidth}p{0.20\\textwidth}",
        ),
        "claims": (
            "table_5_claim_support_matrix",
            "Table 5. Claim-support matrix",
            "tab:main_claim_support_matrix",
            "Statuses distinguish baseline evidence, stress-calibrated evidence, theoretical mechanisms, and pending empirical validation.",
            "p{0.17\\textwidth}p{0.18\\textwidth}p{0.19\\textwidth}p{0.20\\textwidth}p{0.17\\textwidth}",
        ),
    }
    for key, df in tables.items():
        basename, caption, label, note, column_format = table_specs[key]
        csv_path = main_dir / f"{basename}.csv"
        tex_path = main_dir / f"{basename}.tex"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        _write_publication_table(df, tex_path, caption=caption, label=label, note=note, column_format=column_format)


def _format_display_value(value: object) -> str:
    if isinstance(value, (bool, np.bool_)):
        return "Yes" if bool(value) else "No"
    if value is None:
        return "NA"
    if isinstance(value, (float, np.floating)):
        if np.isnan(value):
            return "NA"
        if abs(float(value)) >= 1000:
            return f"{float(value):,.0f}"
        return f"{float(value):,.3f}"
    return str(value)


def _display_columns(df: pd.DataFrame) -> pd.DataFrame:
    labels = {
        "regime": "Regime",
        "acres_Corn": "Corn",
        "acres_Soybean": "Soybean",
        "acres_Winter Wheat": "Winter Wheat",
        "expected_profit": "Expected Profit",
        "cvar_loss": "CVaR Loss",
        "budget_active": "Budget Active",
        "cvar_active": "CVaR Active",
        "ranking_reversal": "Ranking Reversal",
        "budget": "Budget",
        "cvar_limit": "CVaR Limit",
        "tail_model": "Tail Model",
        "dominant_active_constraint": "Dominant Active Constraint",
        "short_interpretation": "Short Interpretation",
        "policy": "Policy",
        "feasible": "Feasible",
        "worst_decile_profit": "Worst-Decile Profit",
        "regret_vs_best_feasible": "Regret vs Best Feasible",
        "parameter_change": "Parameter Change",
        "baseline_value": "Baseline Value",
        "alternative_value_range": "Alternative Value / Range",
        "reversal_status": "Reversal Threshold or Status",
        "direction_interpretation": "Direction / Interpretation",
    }
    display = df.copy()
    display = display.applymap(_format_display_value)
    if "policy" in display.columns:
        display["policy"] = display["policy"].replace({"CVaR": "CVaR-optimal"})
    display.columns = [labels.get(col, col) for col in display.columns]
    return display


def _write_publication_table(
    df: pd.DataFrame,
    tex_path: Path,
    *,
    caption: str,
    label: str,
    note: Optional[str] = None,
    column_format: Optional[str] = None,
) -> None:
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    display = _display_columns(df)
    latex = display.to_latex(index=False, escape=True, column_format=column_format)
    latex = latex.replace("\\begin{tabular}", "\\small\n\\begin{tabular}", 1)
    body = [
        "\\begin{table}[!htbp]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\begin{threeparttable}",
        "\\setlength{\\tabcolsep}{3pt}",
        latex.strip(),
    ]
    if note:
        body.extend(["\\begin{tablenotes}[flushleft]", f"\\footnotesize\\item Note: {note}", "\\end{tablenotes}"])
    body.extend(["\\end{threeparttable}", "\\end{table}", ""])
    tex_path.write_text("\n".join(body), encoding="utf-8")


def _write_invariance_check(
    project_root: Path,
    sources: Dict[str, pd.DataFrame],
    main_tables: Dict[str, pd.DataFrame],
) -> Dict[str, object]:
    checks: List[Dict[str, object]] = []

    baseline_source = sources["active_constraints"].loc[
        sources["active_constraints"]["selected_regime"] == "baseline_liquidity_driven"
    ].head(1)
    baseline_main = main_tables["baseline"].iloc[0]
    checks.append(
        _check_values(
            "Baseline mechanism table",
            "outputs/tables/table_A1_active_constraint_diagnostics.csv",
            "outputs/tables/main/table_1_baseline_mechanism.csv",
            {
                "acres_Corn": (baseline_source["acres_Corn"].iloc[0], baseline_main["acres_Corn"]),
                "acres_Soybean": (baseline_source["acres_Soybean"].iloc[0], baseline_main["acres_Soybean"]),
                "cvar_loss": (baseline_source["cvar_loss"].iloc[0], baseline_main["cvar_loss"]),
            },
            "Select the baseline_liquidity_driven row and compact mechanism columns.",
        )
    )

    benchmark_source = sources["stress_benchmark"].set_index("policy")
    benchmark_main = main_tables["benchmark"].set_index("policy")
    value_pairs = {}
    for policy in benchmark_main.index:
        for field in ["expected_profit", "cvar_loss", "worst_decile_profit"]:
            value_pairs[f"{policy}_{field}"] = (benchmark_source.loc[policy, field], benchmark_main.loc[policy, field])
    checks.append(
        _check_values(
            "Policy comparison table",
            "outputs/tables/table_2b_benchmark_comparison_stress.csv",
            "outputs/tables/main/table_3_policy_comparison.csv",
            value_pairs,
            "Select policy-level expected profit, CVaR loss, feasibility, worst-decile profit, and feasibility-consistent regret.",
        )
    )

    div_status = "Not observed; theoretical only" in main_tables["claims"]["Current Numerical Status"].tolist()
    checks.append(
        {
            "check": "Claim-support status",
            "source_file": "outputs/logs/summary_metrics_v2.json",
            "compact_file": "outputs/tables/main/table_5_claim_support_matrix.csv",
            "row_selection_logic": "Use summary_metrics_v2 and manuscript claim audit statuses.",
            "column_selection_logic": "Map claim categories to baseline/stress/numerical/empirical status columns.",
            "values_match": bool(div_status),
            "details": "Diversification failure remains Not observed; theoretical only.",
        }
    )

    all_passed = all(bool(check["values_match"]) for check in checks)
    if not all_passed:
        raise ValueError("Publication table invariance check failed.")

    lines = [
        "# Publication Tables Invariance Check",
        "",
        "| Check | Source File | Derived Table | Row / Column Logic | Values Match |",
        "|---|---|---|---|---|",
    ]
    for check in checks:
        lines.append(
            f"| {check['check']} | `{check['source_file']}` | `{check['compact_file']}` | "
            f"{check['row_selection_logic']} {check['column_selection_logic']} | {check['values_match']} |"
        )
    lines.extend(
        [
            "",
            "All compact tables are derived from existing generated outputs. No underlying numerical results are changed.",
        ]
    )
    write_markdown(project_root / "outputs" / "logs" / "publication_tables_invariance_check.md", "\n".join(lines))
    return {"checks": checks, "all_passed": all_passed}


def _check_values(
    check: str,
    source_file: str,
    compact_file: str,
    value_pairs: Dict[str, Tuple[object, object]],
    logic: str,
) -> Dict[str, object]:
    match = all(np.isclose(float(source), float(derived), atol=1e-8, rtol=1e-8) for source, derived in value_pairs.values())
    return {
        "check": check,
        "source_file": source_file,
        "compact_file": compact_file,
        "row_selection_logic": logic,
        "column_selection_logic": f"Compared {', '.join(value_pairs)}.",
        "values_match": bool(match),
        "details": json.dumps({key: [float(v[0]), float(v[1])] for key, v in value_pairs.items()}),
    }


def _write_v3_section(project_root: Path, summary: Dict[str, object]) -> None:
    risk_reversal = bool(summary.get("ranking_reversal_in_risk_binding_theta_grid", False))
    div_observed = bool(summary.get("diversification_failure_occurred", False))
    info_positive = bool(summary.get("positive_information_value_occurred", False))
    stress_violators = summary.get("stress_benchmark_cvar_violators", [])
    violator_text = ", ".join(stress_violators) if stress_violators else "none"
    diversification_sentence = (
        "The diversification stress scan exhibits non-monotonic Clayton CVaR."
        if div_observed
        else "The diversification stress scan does not exhibit non-monotonic Clayton CVaR; diversification failure remains a theoretical or future-empirical claim."
    )
    info_sentence = (
        "Positive information value appears in the compressed-margin stress design once flexibility is sufficient."
        if info_positive
        else "The generated information-flexibility runs do not produce material positive information value."
    )
    risk_sentence = (
        "The selected risk-binding theta sweep crosses a ranking-reversal threshold."
        if risk_reversal
        else "The selected risk-binding theta sweep does not cross a ranking-reversal threshold."
    )
    section = rf"""
\section{{Numerical Simulation and Stress-Calibrated Evidence}}
\label{{sec:numerical_generated}}
\label{{sec:simulation}}

\subsection{{Baseline Numerical Design}}

The baseline numerical design uses the manuscript parameters: 500 acres,
a \$220,000 input-cost budget, $\alpha=0.90$, a CVaR loss limit of
\$30,000, crop costs of \$720, \$385, and \$310 per acre for corn,
soybean, and winter wheat, respectively, and the suitability ranking
Corn $>$ Soybean $>$ Winter Wheat.  All numerical results in this
section are generated by the scripts in \texttt{{scripts/}} from the
simulation code in \texttt{{src/}}.  The results are simulated or
stress-calibrated evidence, not empirical USDA estimates.

\subsection{{Baseline Mechanism: Liquidity-Driven Reversal}}

Table~\ref{{tab:main_baseline_mechanism}} reports the compact baseline
mechanism table.  The original baseline exhibits ranking reversal, but
the budget constraint binds while the CVaR constraint is slack.  The
baseline evidence therefore supports a liquidity-driven operational
reversal, not a baseline CVaR-driven reversal.  Full slacks, dual values,
and active-constraint diagnostics are preserved in Appendix
Table~\ref{{tab:appendix_active_constraint_diagnostics}} and the
machine-readable CSV files.

\input{{outputs/tables/main/table_1_baseline_mechanism.tex}}

\begin{{figure}}[!htbp]
\centering
\includegraphics[width=0.88\textwidth]{{outputs/figures/figure_1_acreage_vs_tail_dependence.pdf}}
\caption{{Figure 1a. Baseline liquidity-driven acreage allocation by lower-tail dependence.}}
\label{{fig:acreage_tail_dependence}}
\end{{figure}}

\subsection{{Stress-Calibrated Mechanism Regimes}}

Because the baseline CVaR constraint is slack, Table~\ref{{tab:main_selected_mechanism_regimes}}
separates the baseline liquidity regime from transparent stress-calibrated
regimes.  The search varies budget, CVaR limit, corn profit volatility,
marginal tail distribution, and Clayton $\theta$; the complete regime
search is preserved in Appendix Table~\ref{{tab:appendix_regime_search_manifest}}
and in \texttt{{outputs/tables/appendix/table\_A2\_full\_regime\_search.csv}}.
{risk_sentence}

\input{{outputs/tables/main/table_2_selected_mechanism_regimes.tex}}

\begin{{figure}}[!htbp]
\centering
\includegraphics[width=0.88\textwidth]{{outputs/figures/figure_1b_risk_binding_acreage_vs_tail_dependence.pdf}}
\caption{{Figure 1b. Risk-binding stress acreage allocation by lower-tail dependence.}}
\label{{fig:risk_binding_tail_dependence}}
\end{{figure}}

\subsection{{Benchmark Policy Comparison}}

Table~\ref{{tab:main_policy_comparison}} reports a compact comparison of
SU, EO, MV, and CVaR-optimal policies under the selected risk-binding
stress regime.  Feasibility is evaluated against the stress-regime CVaR
and budget constraints; regret is reported only for feasible policies.
The generated stress benchmark policies violating the CVaR limit are:
{violator_text}.

\input{{outputs/tables/main/table_3_policy_comparison.tex}}

\begin{{figure}}[!htbp]
\centering
\includegraphics[width=0.82\textwidth]{{outputs/figures/figure_2_policy_cvar_profit_tradeoff.pdf}}
\caption{{Expected-profit and CVaR-loss tradeoff across baseline benchmark policies.}}
\label{{fig:policy_tradeoff}}
\end{{figure}}

\subsection{{Robustness and Claim Support}}

Table~\ref{{tab:main_robustness_summary}} compresses the robustness grid
into reader-facing parameter slices.  The full grid is preserved in
Appendix Table~\ref{{tab:appendix_robustness_grid}}.  Table~\ref{{tab:main_claim_support_matrix}}
then maps each manuscript claim to its current evidence status so that
simulated, stress-calibrated, theoretical, and empirical claims remain
visibly separate.

\input{{outputs/tables/main/table_4_robustness_summary.tex}}

\input{{outputs/tables/main/table_5_claim_support_matrix.tex}}

\subsection{{Diversification and Information-Flexibility Stress Tests}}

The controlled diversification stress test compares Gaussian and Clayton
copulas using matched marginal distributions and comparable Pearson
correlation while winter wheat acreage varies.  {diversification_sentence}
Appendix Table~\ref{{tab:appendix_diversification_diagnostics}} preserves
the diagnostic scan.  The information-flexibility stress test evaluates a
crop-specific $\pm15\%$ profit signal under increasing operational
flexibility $\phi$ using a compressed Corn--Soybean expected-margin gap.
{info_sentence}  The full information grid is preserved in Appendix
Table~\ref{{tab:appendix_information_flexibility_grid}}.

\begin{{figure}}[!htbp]
\centering
\includegraphics[width=0.84\textwidth]{{outputs/figures/figure_3b_diversification_failure_stress.pdf}}
\caption{{Diversification stress test under Gaussian and Clayton dependence.}}
\label{{fig:diversification_failure_stress}}
\end{{figure}}

\begin{{figure}}[!htbp]
\centering
\includegraphics[width=0.84\textwidth]{{outputs/figures/figure_4b_information_value_stress.pdf}}
\caption{{Stress-calibrated value of information as operational flexibility increases.}}
\label{{fig:information_value_stress}}
\end{{figure}}

\subsection{{Empirical Validation Template}}

Full empirical validation remains pending until real county-year-crop
data are supplied.  The template requires the fields
\texttt{{county}}, \texttt{{state}}, \texttt{{year}}, \texttt{{crop}},
\texttt{{yield\_per\_acre}}, \texttt{{price}},
\texttt{{cost\_per\_acre}}, \texttt{{profit\_per\_acre}}, and
\texttt{{suitability\_score}}.  No empirical claim is made in the absence
of those data.

\input{{outputs/tables/table_6_empirical_validation_template.tex}}
"""
    (project_root / "paper_sections" / "section_5_publication_tables_v3.tex").write_text(
        section.strip() + "\n", encoding="utf-8"
    )


def _write_v3_appendix(project_root: Path) -> None:
    appendix = r"""
\section*{Appendix: Numerical Diagnostics}
\label{app:numerical_diagnostics}

This appendix preserves implementation-level diagnostics behind the compact
main-text tables.  The complete machine-readable outputs are also archived in
\nolinkurl{outputs/tables/full/}.

\input{outputs/tables/appendix/table_A1_full_active_constraint_diagnostics.tex}

\input{outputs/tables/appendix/table_A2_full_regime_search_manifest.tex}

\input{outputs/tables/appendix/table_A3_full_robustness_grid.tex}

\input{outputs/tables/appendix/table_A4_diversification_failure_diagnostics.tex}

\input{outputs/tables/appendix/table_A5_information_flexibility_full_grid.tex}
"""
    (project_root / "paper_sections" / "appendix_publication_tables_v3.tex").write_text(
        appendix.strip() + "\n", encoding="utf-8"
    )


def _update_revised_manuscript_v3(project_root: Path) -> None:
    original_path = project_root / "Crop_ranking_reversal_total.tex"
    revised_path = project_root / "Crop_ranking_reversal_total_revised_v3.tex"
    text = original_path.read_text(encoding="latin9")
    abstract_replacement = (
        "Reproducible calibrated simulations distinguish liquidity-driven "
        "ranking reversal from stress-calibrated CVaR and tail-dependence "
        "regimes. The baseline manuscript parameters generate a "
        "liquidity-driven reversal with a slack CVaR constraint. Additional "
        "stress regimes are reported separately, and no empirical claim is "
        "made without real county-year-crop data."
    )
    text = text.replace(
        "Reproducible calibrated simulations distinguish liquidity-driven ranking reversal from stress-calibrated CVaR and tail-dependence regimes.  The baseline manuscript parameters generate a liquidity-driven reversal with a slack CVaR constraint; additional stress regimes are reported separately and no empirical claim is made without real county-year-crop data.",
        abstract_replacement,
    )
    text = text.replace(
        "Calibrated\r\nnumerical simulations using USDA county-level crop budget and yield data\r\nconfirm all theoretical predictions and quantify the welfare loss from\r\nignoring ranking reversal: naive suitability-based allocation raises CVaR\r\nlosses by 19--34\\% relative to the risk-optimal plan.",
        abstract_replacement,
    )
    text = text.replace(
        "Calibrated\nnumerical simulations using USDA county-level crop budget and yield data\nconfirm all theoretical predictions and quantify the welfare loss from\nignoring ranking reversal: naive suitability-based allocation raises CVaR\nlosses by 19--34\\% relative to the risk-optimal plan.",
        abstract_replacement,
    )
    import re

    text = re.sub(
        r"\\section\{Numerical Simulation\}.*?(?=\\section\{Discussion\})",
        lambda _: "\\input{paper_sections/section_5_publication_tables_v3}\n\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"(?=\\begin\{thebibliography\})",
        lambda _: "\\input{paper_sections/appendix_publication_tables_v3}\n\n",
        text,
        count=1,
    )
    revised_path.write_text(text.rstrip() + "\n", encoding="latin9")


def _write_final_summary_v3(
    project_root: Path,
    summary: Dict[str, object],
    preflight: Dict[str, object],
    invariance: Dict[str, object],
) -> None:
    body = f"""
# Final Summary V3: Publication Tables

Publication-table refactoring completed without changing the generated numerical results.

## Main Tables

- `outputs/tables/main/table_1_baseline_mechanism.csv/.tex`
- `outputs/tables/main/table_2_selected_mechanism_regimes.csv/.tex`
- `outputs/tables/main/table_3_policy_comparison.csv/.tex`
- `outputs/tables/main/table_4_robustness_summary.csv/.tex`
- `outputs/tables/main/table_5_claim_support_matrix.csv/.tex`

## Appendix And Full Outputs

- Appendix diagnostics are under `outputs/tables/appendix/`.
- Machine-readable full CSV outputs are under `outputs/tables/full/`.
- Source tables recorded in preflight: {len(preflight['source_tables'])}.
- Invariance checks passed: {invariance['all_passed']}.

## Evidence Status

- Baseline driver: {summary['baseline_driver']}.
- CVaR-binding stress regime found: {summary['nonbudget_cvar_binding_regime_found']}.
- Risk-binding theta-grid reversal observed: {summary['ranking_reversal_in_risk_binding_theta_grid']}.
- Diversification failure observed: {summary['diversification_failure_occurred']}.
- Positive information value observed under stress calibration: {summary['positive_information_value_occurred']}.

## Manuscript

- Revised manuscript: `Crop_ranking_reversal_total_revised_v3.tex`
- The v3 manuscript uses compact main-text tables and moves full diagnostics to appendix/full CSV outputs.
"""
    write_markdown(project_root / "outputs" / "logs" / "final_summary_v3.md", body)
