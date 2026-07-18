"""Stress-calibrated regimes and diagnostics for the crop paper."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from crop_optimization.benchmark_policies import run_policy_comparison
from crop_optimization.cvar_optimizer import solve_cvar_allocation, solve_expected_profit_allocation
from crop_optimization.evaluation import allocation_metrics, ranking_reversal_flags
from crop_optimization.robustness import array_by_crop
from .scenario_generation import generate_profit_scenarios


RISK_BUDGET_GRID = [220000, 260000, 300000, 350000, 400000]
RISK_KAPPA_GRID = [10000, 15000, 20000, 25000, 30000, 40000]
RISK_CORN_VOL_GRID = [1.0, 1.25, 1.5, 2.0]
RISK_TAIL_GRID = ["normal", "student_t_df5", "student_t_df3"]
RISK_THETA_GRID = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
LEGACY_RESULT_DRIVEN_SEARCH_DISABLED = True


def tail_model_from_label(label: str) -> Dict[str, object]:
    label = str(label)
    if label == "normal":
        return {"type": "normal"}
    if label == "student_t_df5":
        return {"type": "student_t", "df": 5}
    if label == "student_t_df3":
        return {"type": "student_t", "df": 3}
    raise ValueError(f"Unknown tail distribution label: {label}")


def stress_config_from_row(base_config: Dict[str, object], row: Dict[str, object]) -> Dict[str, object]:
    cfg = deepcopy(base_config)
    crop_names = list(cfg["crop_names"])
    cfg["budget"] = float(row.get("budget", cfg["budget"]))
    cfg["cvar_limit"] = float(row.get("cvar_limit", row.get("kappa", cfg["cvar_limit"])))
    cfg["marginal_model"] = tail_model_from_label(str(row.get("tail_distribution", "normal")))
    stds = dict(cfg["stds"])
    stds["Corn"] = float(stds["Corn"]) * float(row.get("corn_volatility_multiplier", 1.0))
    if "wheat_volatility_multiplier" in row:
        stds["Winter Wheat"] = float(stds["Winter Wheat"]) * float(row["wheat_volatility_multiplier"])
    cfg["stds"] = stds
    if "wheat_mean_adjustment" in row:
        means = dict(cfg["means"])
        means["Winter Wheat"] = float(means["Winter Wheat"]) + float(row["wheat_mean_adjustment"])
        cfg["means"] = means
    return cfg


def _result_row(
    result,
    config: Dict[str, object],
    metadata: Dict[str, object],
    *,
    mechanism_regime: str,
    scenario_label: str,
    extra: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    crop_names = list(config["crop_names"])
    row: Dict[str, object] = {
        "mechanism_regime": mechanism_regime,
        "scenario_label": scenario_label,
        "status": result.status,
        "solver_status": result.solver_status,
        "budget": float(config["budget"]),
        "cvar_limit": float(config["cvar_limit"]),
        "alpha": float(config["alpha"]),
        "copula_type": metadata.get("copula_type"),
        "theta": metadata.get("copula_param"),
        "lambda_L": metadata.get("lower_tail_dependence"),
        "tail_distribution": _tail_label(config.get("marginal_model")),
        "n_scenarios": metadata.get("n_scenarios"),
        "expected_profit": result.expected_profit,
        "cvar_loss": result.cvar_loss,
        "var_loss": result.var_loss,
    }
    if result.allocation is not None:
        reversal, strong = ranking_reversal_flags(result.allocation, crop_names)
        row["ranking_reversal"] = reversal
        row["strong_reversal"] = strong
        for idx, crop in enumerate(crop_names):
            row[f"acres_{crop}"] = float(result.allocation[idx])
    else:
        row["ranking_reversal"] = False
        row["strong_reversal"] = False
    row.update({k: v for k, v in result.diagnostics.items() if _safe_scalar(v)})
    row["budget_binds"] = bool(row.get("budget_binds", False))
    row["cvar_binds"] = bool(row.get("cvar_binds", False))
    row["land_binds"] = bool(row.get("land_binds", False))
    row["rotation_binds"] = bool(row.get("rotation_binds", False))
    row["budget_slack"] = row.get("budget_slack")
    row["land_slack"] = row.get("acreage_slack")
    row["cvar_slack"] = row.get("optimizer_cvar_slack", row.get("cvar_slack"))
    if extra:
        row.update(extra)
    return row


def _safe_scalar(value: object) -> bool:
    return isinstance(value, (int, float, bool, str, np.integer, np.floating, np.bool_))


def _tail_label(marginal_model: object) -> str:
    model = marginal_model or {"type": "skewed_mixture"}
    if not isinstance(model, dict):
        return str(model)
    model_type = str(model.get("type", "skewed_mixture"))
    if model_type in {"student_t", "student-t", "t"}:
        return f"student_t_df{int(model.get('df', 5))}"
    return model_type


def solve_stress_regime(
    config: Dict[str, object],
    *,
    theta: float,
    n_scenarios: int,
    seed: int,
    mechanism_regime: str,
    scenario_label: str,
    copula_type: str = "Clayton",
    copula_param: Optional[object] = None,
    extra: Optional[Dict[str, object]] = None,
) -> Tuple[Dict[str, object], np.ndarray, Dict[str, object]]:
    crop_names = list(config["crop_names"])
    means = array_by_crop(config["means"], crop_names)
    stds = array_by_crop(config["stds"], crop_names)
    if copula_param is None:
        copula_param = float(theta)
    scenarios, metadata = generate_profit_scenarios(
        means,
        stds,
        int(n_scenarios),
        copula_type,
        copula_param,
        int(seed),
        crop_names=crop_names,
        marginal_model=config.get("marginal_model"),
    )
    result = solve_cvar_allocation(
        scenarios,
        array_by_crop(config["costs"], crop_names),
        float(config["total_acres"]),
        float(config["budget"]),
        float(config["alpha"]),
        float(config["cvar_limit"]),
        array_by_crop(config["lower_bounds"], crop_names),
        array_by_crop(config["upper_bounds"], crop_names),
        dict(config.get("rotation_caps") or {}),
        crop_names,
        dict(config.get("contract_minimums") or {}),
    )
    row = _result_row(
        result,
        config,
        metadata,
        mechanism_regime=mechanism_regime,
        scenario_label=scenario_label,
        extra=extra,
    )
    if result.allocation is not None:
        eo = solve_expected_profit_allocation(
            scenarios.mean(axis=0),
            array_by_crop(config["costs"], crop_names),
            float(config["total_acres"]),
            float(config["budget"]),
            array_by_crop(config["lower_bounds"], crop_names),
            array_by_crop(config["upper_bounds"], crop_names),
            dict(config.get("rotation_caps") or {}),
            crop_names,
            dict(config.get("contract_minimums") or {}),
        )
        if eo.allocation is not None:
            row["allocation_l1_shift_from_eo"] = float(np.abs(result.allocation - eo.allocation).sum())
            row["cvar_materially_changes_allocation"] = bool(row["allocation_l1_shift_from_eo"] >= 25.0)
    return row, scenarios, metadata


def active_constraint_diagnostics(config: Dict[str, object]) -> pd.DataFrame:
    row, _, _ = solve_stress_regime(
        config,
        theta=float(config.get("baseline_clayton_theta", 2.0)),
        n_scenarios=int(config["n_scenarios"]),
        seed=int(config["random_seed"]) + 901,
        mechanism_regime="baseline_liquidity_driven",
        scenario_label="original_baseline",
    )
    row["interpretation"] = (
        "Baseline is liquidity-driven if budget_binds is true while cvar_binds is false."
    )
    return pd.DataFrame([row])


def run_regime_search(config: Dict[str, object]) -> pd.DataFrame:
    if LEGACY_RESULT_DRIVEN_SEARCH_DISABLED:
        raise RuntimeError(
            "Result-driven regime search was disabled by the Issue #5 design freeze; "
            "use experiment_design.expand_design before any formal run."
        )
    stress_cfg = dict(config.get("stress_calibration") or {})
    n_scenarios = int(stress_cfg.get("search_n_scenarios", 300))
    rows: List[Dict[str, object]] = []
    combo_idx = 0
    for budget in RISK_BUDGET_GRID:
        for kappa in RISK_KAPPA_GRID:
            for corn_vol in RISK_CORN_VOL_GRID:
                for tail_distribution in RISK_TAIL_GRID:
                    for theta in RISK_THETA_GRID:
                        combo_idx += 1
                        cfg = stress_config_from_row(
                            config,
                            {
                                "budget": budget,
                                "cvar_limit": kappa,
                                "corn_volatility_multiplier": corn_vol,
                                "tail_distribution": tail_distribution,
                            },
                        )
                        row, _, _ = solve_stress_regime(
                            cfg,
                            theta=theta,
                            n_scenarios=n_scenarios,
                            seed=int(config["random_seed"]) + 10000 + combo_idx,
                            mechanism_regime="risk_binding_stress",
                            scenario_label="risk_binding_grid_search",
                            extra={
                                "corn_volatility_multiplier": corn_vol,
                                "tail_distribution": tail_distribution,
                                "grid_index": combo_idx,
                            },
                        )
                        row["risk_binding_candidate"] = bool(
                            row.get("status") == "optimal"
                            and (bool(row.get("cvar_binds")) or float(row.get("cvar_slack") or np.inf) <= 500.0)
                            and not bool(row.get("budget_binds"))
                            and (
                                bool(row.get("ranking_reversal"))
                                or bool(row.get("cvar_materially_changes_allocation", False))
                            )
                        )
                        rows.append(row)
    return pd.DataFrame(rows)


def select_regimes(config: Dict[str, object], active_df: pd.DataFrame, search_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, object]]:
    if LEGACY_RESULT_DRIVEN_SEARCH_DISABLED:
        raise RuntimeError(
            "Post-result regime selection is prohibited by the frozen Issue #5 design."
        )
    selected: List[Dict[str, object]] = []
    baseline = active_df.iloc[0].to_dict()
    baseline["selected_regime"] = "baseline_liquidity_driven"
    baseline["interpretation"] = "Original manuscript parameters: budget binds and CVaR is slack."
    selected.append(baseline)

    validated = validate_risk_candidates(config, search_df)
    if not validated.empty:
        validated["sort_slack"] = validated["cvar_slack"].abs()
        validated["sort_shift"] = -validated.get("allocation_l1_shift_from_eo", 0.0)
        risk = validated.sort_values(["ranking_reversal", "sort_shift", "sort_slack"], ascending=[False, True, True]).iloc[0].to_dict()
        risk["selected_regime"] = "risk_binding_cvar_regime"
        risk["interpretation"] = "Stress-calibrated regime where the CVaR constraint is active and the budget is not the primary binding constraint."
        selected.append(risk)
    else:
        risk = {}

    tail_group = _select_tail_dependence_group(search_df)
    if tail_group:
        tail_cfg = stress_config_from_row(config, tail_group)
        tail_row, _, _ = solve_stress_regime(
            tail_cfg,
            theta=float(tail_group["theta"]),
            n_scenarios=int(config["n_scenarios"]),
            seed=int(config["random_seed"]) + 33333,
            mechanism_regime="tail_dependence_stress",
            scenario_label="selected_tail_dependence_regime",
            extra={
                "corn_volatility_multiplier": tail_group["corn_volatility_multiplier"],
                "tail_distribution": tail_group["tail_distribution"],
            },
        )
        tail_row["selected_regime"] = "tail_dependence_reversal_regime"
        tail_row["interpretation"] = str(tail_group["interpretation"])
        selected.append(tail_row)

    selected_df = pd.DataFrame(selected)
    selected_params = {
        "risk": risk if risk else None,
        "tail": tail_group if tail_group else risk if risk else None,
    }
    return selected_df, selected_params


def validate_risk_candidates(config: Dict[str, object], search_df: pd.DataFrame) -> pd.DataFrame:
    candidates = risk_binding_candidates(search_df)
    if candidates.empty:
        candidates = search_df.loc[
            (search_df["status"] == "optimal")
            & (search_df["cvar_binds"].astype(bool))
            & (~search_df["budget_binds"].astype(bool))
        ].copy()
    if candidates.empty:
        return pd.DataFrame()
    if "allocation_l1_shift_from_eo" in candidates:
        candidates = candidates.sort_values(["ranking_reversal", "allocation_l1_shift_from_eo"], ascending=[False, False])
    rows = []
    for idx, candidate in candidates.head(80).reset_index(drop=True).iterrows():
        candidate_dict = candidate.to_dict()
        cfg = stress_config_from_row(config, candidate_dict)
        row, _, _ = solve_stress_regime(
            cfg,
            theta=float(candidate_dict.get("theta", 2.0)),
            n_scenarios=int(config["n_scenarios"]),
            seed=int(config["random_seed"]) + 90000 + idx,
            mechanism_regime="risk_binding_stress",
            scenario_label="validated_risk_binding_candidate",
            extra={
                "corn_volatility_multiplier": candidate_dict.get("corn_volatility_multiplier", 1.0),
                "tail_distribution": candidate_dict.get("tail_distribution", _tail_label(cfg.get("marginal_model"))),
                "screen_grid_index": candidate_dict.get("grid_index"),
            },
        )
        if row.get("status") == "optimal" and bool(row.get("cvar_binds")) and not bool(row.get("budget_binds")):
            rows.append(row)
    return pd.DataFrame(rows)


def _select_tail_dependence_group(search_df: pd.DataFrame) -> Optional[Dict[str, object]]:
    group_cols = ["budget", "cvar_limit", "corn_volatility_multiplier", "tail_distribution"]
    best: Optional[Dict[str, object]] = None
    best_score = -np.inf
    for values, part in search_df.loc[search_df["status"] == "optimal"].groupby(group_cols):
        ordered = part.sort_values("lambda_L")
        reversal_values = set(ordered["ranking_reversal"].astype(bool).tolist())
        allocation_span = float(ordered["acres_Corn"].max() - ordered["acres_Corn"].min())
        cvar_active_count = int(ordered["cvar_binds"].astype(bool).sum())
        has_threshold = len(reversal_values) > 1
        score = allocation_span + 1000.0 * int(has_threshold) + 100.0 * cvar_active_count
        if score > best_score:
            best_score = score
            selected_theta = float(ordered.loc[ordered["cvar_binds"].astype(bool), "theta"].max()) if cvar_active_count else float(ordered.iloc[-1]["theta"])
            best = dict(zip(group_cols, values))
            best["theta"] = selected_theta
            best["has_reversal_threshold"] = bool(has_threshold)
            best["tail_allocation_span"] = allocation_span
            best["interpretation"] = (
                "Increasing Clayton theta changes the allocation and crosses a reversal threshold."
                if has_threshold
                else "Increasing Clayton theta changes allocation, but a reversal threshold is not observed in this group."
            )
    return best


def risk_binding_candidates(search_df: pd.DataFrame) -> pd.DataFrame:
    candidates = search_df.loc[search_df["risk_binding_candidate"] == True].copy()  # noqa: E712
    if candidates.empty:
        candidates = search_df.loc[
            (search_df["status"] == "optimal")
            & (search_df["cvar_binds"].astype(bool))
            & (~search_df["budget_binds"].astype(bool))
        ].copy()
    if candidates.empty:
        return pd.DataFrame(columns=search_df.columns)
    return candidates.sort_values(
        ["ranking_reversal", "allocation_l1_shift_from_eo", "cvar_slack"],
        ascending=[False, False, True],
    ).head(50)


def rerun_theta_grid(config: Dict[str, object], selected_row: Dict[str, object]) -> pd.DataFrame:
    cfg = stress_config_from_row(config, selected_row)
    rows = []
    for idx, theta in enumerate(RISK_THETA_GRID):
        row, _, _ = solve_stress_regime(
            cfg,
            theta=theta,
            n_scenarios=int(config["n_scenarios"]),
            seed=int(config["random_seed"]) + 42000 + idx,
            mechanism_regime="risk_binding_stress",
            scenario_label="risk_binding_theta_grid",
            extra={
                "corn_volatility_multiplier": selected_row.get("corn_volatility_multiplier", 1.0),
                "tail_distribution": selected_row.get("tail_distribution", _tail_label(cfg.get("marginal_model"))),
            },
        )
        rows.append(row)
    return pd.DataFrame(rows)


def controlled_wheat_allocation(config: Dict[str, object], wheat_acres: float) -> np.ndarray:
    crop_names = list(config["crop_names"])
    scores = array_by_crop(config["suitability_scores"], crop_names)
    costs = array_by_crop(config["costs"], crop_names)
    total_acres = float(config["total_acres"])
    budget = float(config["budget"])
    corn_cap = float((config.get("rotation_caps") or {}).get("Corn", total_acres))
    wheat_acres = float(wheat_acres)
    remaining = max(total_acres - wheat_acres, 0.0)
    corn_target = remaining * scores[crop_names.index("Corn")] / (
        scores[crop_names.index("Corn")] + scores[crop_names.index("Soybean")]
    )
    min_soy = float(config["lower_bounds"]["Soybean"])
    max_corn_by_soy = max(0.0, remaining - min_soy)
    if costs[crop_names.index("Corn")] > costs[crop_names.index("Soybean")]:
        max_corn_by_budget = (
            budget
            - costs[crop_names.index("Soybean")] * remaining
            - costs[crop_names.index("Winter Wheat")] * wheat_acres
        ) / (costs[crop_names.index("Corn")] - costs[crop_names.index("Soybean")])
    else:
        max_corn_by_budget = total_acres
    corn = max(0.0, min(corn_target, max_corn_by_soy, max_corn_by_budget, corn_cap))
    soybean = remaining - corn
    allocation = np.zeros(len(crop_names))
    allocation[crop_names.index("Corn")] = corn
    allocation[crop_names.index("Soybean")] = soybean
    allocation[crop_names.index("Winter Wheat")] = wheat_acres
    return allocation


def diversification_failure_stress(config: Dict[str, object], selected_row: Optional[Dict[str, object]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    crop_names = list(config["crop_names"])
    stress_candidates = []
    base = selected_row or {
        "budget": 350000,
        "cvar_limit": 20000,
        "corn_volatility_multiplier": 1.5,
        "tail_distribution": "student_t_df3",
        "theta": 3.0,
    }
    for wheat_mean_adjustment in [0.0, -35.0, -70.0, -110.0]:
        for wheat_volatility_multiplier in [1.0, 1.5, 2.0, 2.5]:
            candidate = dict(base)
            candidate["wheat_mean_adjustment"] = wheat_mean_adjustment
            candidate["wheat_volatility_multiplier"] = wheat_volatility_multiplier
            candidate["theta"] = float(candidate.get("theta", 3.0))
            stress_candidates.append(candidate)

    diagnostics = []
    best_result: Optional[pd.DataFrame] = None
    best_score = -np.inf
    for scan_idx, candidate in enumerate(stress_candidates):
        cfg = stress_config_from_row(config, candidate)
        rows = []
        for copula, param, seed_offset in [
            ("Gaussian", np.asarray(config["gaussian_correlation"], dtype=float), 70000 + scan_idx * 10),
            ("Clayton", float(candidate.get("theta", 3.0)), 71000 + scan_idx * 10),
        ]:
            scenarios, metadata = generate_profit_scenarios(
                array_by_crop(cfg["means"], crop_names),
                array_by_crop(cfg["stds"], crop_names),
                int(config["n_scenarios"]),
                copula,
                param,
                int(config["random_seed"]) + seed_offset,
                crop_names=crop_names,
                marginal_model=cfg.get("marginal_model"),
            )
            pearson = np.corrcoef(scenarios, rowvar=False)
            for wheat in np.arange(0, 181, 15):
                allocation = controlled_wheat_allocation(cfg, wheat)
                metrics = allocation_metrics(
                    allocation,
                    scenarios,
                    array_by_crop(cfg["costs"], crop_names),
                    float(cfg["total_acres"]),
                    float(cfg["budget"]),
                    float(cfg["alpha"]),
                    float(cfg["cvar_limit"]),
                    crop_names,
                )
                rows.append(
                    {
                        "mechanism_regime": "diversification_failure_stress",
                        "scan_index": scan_idx,
                        "copula": copula,
                        "theta": candidate.get("theta"),
                        "lambda_L": metadata["lower_tail_dependence"],
                        "tail_distribution": candidate.get("tail_distribution", _tail_label(cfg.get("marginal_model"))),
                        "wheat_mean_adjustment": candidate["wheat_mean_adjustment"],
                        "wheat_volatility_multiplier": candidate["wheat_volatility_multiplier"],
                        "wheat_acres": float(wheat),
                        "corn_acres": allocation[crop_names.index("Corn")],
                        "soybean_acres": allocation[crop_names.index("Soybean")],
                        "cvar_loss": metrics["cvar_loss"],
                        "expected_profit": metrics["expected_profit"],
                        "pearson_corr_mean": float(np.mean(pearson[np.triu_indices_from(pearson, k=1)])),
                    }
                )
        df = pd.DataFrame(rows)
        clayton = df.loc[df["copula"] == "Clayton"].sort_values("wheat_acres")
        diffs = clayton["cvar_loss"].diff()
        nonmonotonic = bool((diffs > 0).any() and (diffs < 0).any())
        positive_steps = int((diffs > 0).sum())
        score = positive_steps * 1000 + float(diffs.max(skipna=True) or 0.0)
        diagnostics.append(
            {
                "mechanism_regime": "diversification_failure_stress",
                "scan_index": scan_idx,
                "theta": candidate.get("theta"),
                "tail_distribution": candidate.get("tail_distribution"),
                "wheat_mean_adjustment": candidate["wheat_mean_adjustment"],
                "wheat_volatility_multiplier": candidate["wheat_volatility_multiplier"],
                "nonmonotonic_clayton_cvar": nonmonotonic,
                "positive_cvar_steps": positive_steps,
                "max_step_increase": float(diffs.max(skipna=True) or 0.0),
            }
        )
        if score > best_score:
            best_score = score
            best_result = df.copy()
        if nonmonotonic:
            return df, pd.DataFrame(diagnostics)
    return best_result if best_result is not None else pd.DataFrame(), pd.DataFrame(diagnostics)


def information_flexibility_stress(config: Dict[str, object], selected_row: Optional[Dict[str, object]]) -> pd.DataFrame:
    crop_names = list(config["crop_names"])
    base_row = {
        "budget": 220000,
        "cvar_limit": 50000,
        "corn_volatility_multiplier": 1.0,
        "tail_distribution": "normal",
        "theta": 1.5,
    }
    cfg = stress_config_from_row(config, base_row)
    cfg["means"] = dict(cfg["means"])
    cfg["means"]["Corn"] = 210.0
    cfg["means"]["Soybean"] = 200.0
    means = array_by_crop(cfg["means"], crop_names)
    stds = array_by_crop(cfg["stds"], crop_names)
    base_scenarios, _ = generate_profit_scenarios(
        means,
        stds,
        int(config["n_scenarios"]),
        "Clayton",
        float(base_row.get("theta", 2.0)),
        int(config["random_seed"]) + 80000,
        crop_names=crop_names,
        marginal_model=cfg.get("marginal_model"),
    )
    corn_idx = crop_names.index("Corn")
    soybean_idx = crop_names.index("Soybean")
    high_scenarios = base_scenarios.copy()
    low_scenarios = base_scenarios.copy()
    high_scenarios[:, corn_idx] *= 1.15
    high_scenarios[:, soybean_idx] *= 0.85
    low_scenarios[:, corn_idx] *= 0.85
    low_scenarios[:, soybean_idx] *= 1.15

    rows = []
    baseline_locked = controlled_wheat_allocation(config, 0.0)
    for phi in np.linspace(0.0, 1.0, 6):
        flex_cfg = deepcopy(cfg)
        flex_cfg["budget"] = float(config["budget"]) + float(phi) * (400000.0 - float(config["budget"]))
        corn_cap = baseline_locked[corn_idx] + float(phi) * (0.80 * float(config["total_acres"]) - baseline_locked[corn_idx])
        flex_cfg["rotation_caps"] = {"Corn": corn_cap}
        flex_cfg["upper_bounds"] = {
            crop: baseline_locked[idx] + float(phi) * (float(config["total_acres"]) - baseline_locked[idx])
            for idx, crop in enumerate(crop_names)
        }
        prior_allocation = _solve_allocation(flex_cfg, base_scenarios)
        prior_expected = 0.5 * np.mean(high_scenarios @ prior_allocation) + 0.5 * np.mean(low_scenarios @ prior_allocation)
        rows.append(
            {
                "mechanism_regime": "information_flexibility_stress",
                "phi": float(phi),
                "signal_regime": "No information",
                "information_accuracy": 0.50,
                "budget": flex_cfg["budget"],
                "corn_rotation_cap": flex_cfg["rotation_caps"]["Corn"],
                "prior_expected_profit": prior_expected,
                "signal_expected_profit": prior_expected,
                "value_of_information": 0.0,
                "signal_allocation_l1_gap": 0.0,
                "high_signal_acres_Corn": prior_allocation[corn_idx],
                "low_signal_acres_Corn": prior_allocation[corn_idx],
            }
        )
        for regime, accuracy in [("75% accurate signal", 0.75), ("Perfect signal", 1.0)]:
            if accuracy >= 0.999:
                high_signal_scenarios = high_scenarios
                low_signal_scenarios = low_scenarios
            else:
                high_signal_scenarios = _posterior_signal_scenarios(high_scenarios, low_scenarios, accuracy)
                low_signal_scenarios = _posterior_signal_scenarios(low_scenarios, high_scenarios, accuracy)
            high_signal_allocation = _solve_allocation(flex_cfg, high_signal_scenarios)
            low_signal_allocation = _solve_allocation(flex_cfg, low_signal_scenarios)
            allocation_gap = float(np.abs(high_signal_allocation - low_signal_allocation).sum())
            signal_expected_profit = 0.0
            for actual_state, actual_scenarios in [("high", high_scenarios), ("low", low_scenarios)]:
                for signal_state, signal_scenarios, signal_allocation in [
                    ("high", high_scenarios, high_signal_allocation),
                    ("low", low_scenarios, low_signal_allocation),
                ]:
                    probability = 0.5 * (accuracy if signal_state == actual_state else 1.0 - accuracy)
                    signal_expected_profit += probability * np.mean(actual_scenarios @ signal_allocation)
            rows.append(
                {
                    "mechanism_regime": "information_flexibility_stress",
                    "phi": float(phi),
                    "signal_regime": regime,
                    "information_accuracy": accuracy,
                    "budget": flex_cfg["budget"],
                    "corn_rotation_cap": flex_cfg["rotation_caps"]["Corn"],
                    "prior_expected_profit": prior_expected,
                    "signal_expected_profit": signal_expected_profit,
                    "value_of_information": signal_expected_profit - prior_expected,
                    "signal_allocation_l1_gap": allocation_gap,
                    "high_signal_acres_Corn": high_signal_allocation[corn_idx],
                    "low_signal_acres_Corn": low_signal_allocation[corn_idx],
                }
            )
    return pd.DataFrame(rows)


def _posterior_signal_scenarios(focal_scenarios: np.ndarray, other_scenarios: np.ndarray, accuracy: float) -> np.ndarray:
    n = len(focal_scenarios)
    focal_count = int(round(float(accuracy) * n))
    focal_count = min(max(focal_count, 0), n)
    other_count = n - focal_count
    return np.vstack([focal_scenarios[:focal_count], other_scenarios[:other_count]])


def _solve_allocation(config: Dict[str, object], scenarios: np.ndarray) -> np.ndarray:
    crop_names = list(config["crop_names"])
    result = solve_cvar_allocation(
        scenarios,
        array_by_crop(config["costs"], crop_names),
        float(config["total_acres"]),
        float(config["budget"]),
        float(config["alpha"]),
        float(config["cvar_limit"]),
        array_by_crop(config["lower_bounds"], crop_names),
        array_by_crop(config["upper_bounds"], crop_names),
        dict(config.get("rotation_caps") or {}),
        crop_names,
        dict(config.get("contract_minimums") or {}),
    )
    if result.allocation is None:
        return array_by_crop(config["lower_bounds"], crop_names)
    return result.allocation


def benchmark_policy_stress(config: Dict[str, object], selected_row: Optional[Dict[str, object]]) -> pd.DataFrame:
    if not selected_row:
        return pd.DataFrame()
    cfg = stress_config_from_row(config, selected_row)
    crop_names = list(cfg["crop_names"])
    scenarios, metadata = generate_profit_scenarios(
        array_by_crop(cfg["means"], crop_names),
        array_by_crop(cfg["stds"], crop_names),
        int(config["n_scenarios"]),
        "Clayton",
        float(selected_row.get("theta", 2.0)),
        int(config["random_seed"]) + 88000,
        crop_names=crop_names,
        marginal_model=cfg.get("marginal_model"),
    )
    df = run_policy_comparison(scenarios, cfg)
    df["mechanism_regime"] = "risk_binding_stress"
    df["scenario_copula"] = metadata["copula_type"]
    df["lambda_L"] = metadata["lower_tail_dependence"]
    df["tail_distribution"] = selected_row.get("tail_distribution", _tail_label(cfg.get("marginal_model")))
    return df
