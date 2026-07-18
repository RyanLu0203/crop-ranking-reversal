"""Ranking reversal and robustness experiments."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from .cvar_optimizer import solve_cvar_allocation
from .evaluation import ranking_reversal_flags
from crop_simulation.scenario_generation import generate_profit_scenarios


def array_by_crop(mapping: Dict[str, float], crop_names: List[str]) -> np.ndarray:
    return np.asarray([mapping[crop] for crop in crop_names], dtype=float)


def solve_for_theta(config: Dict[str, object], theta: float, *, n_scenarios: Optional[int] = None) -> Dict[str, object]:
    crop_names = list(config["crop_names"])
    means = array_by_crop(config["means"], crop_names)
    stds = array_by_crop(config["stds"], crop_names)
    costs = array_by_crop(config["costs"], crop_names)
    lower_bounds = array_by_crop(config["lower_bounds"], crop_names)
    upper_bounds = array_by_crop(config["upper_bounds"], crop_names)
    scenarios, metadata = generate_profit_scenarios(
        means,
        stds,
        int(n_scenarios or config["n_scenarios"]),
        "Clayton",
        float(theta),
        int(config["random_seed"]) + int(round(theta * 1000)),
        crop_names=crop_names,
        marginal_model=config.get("marginal_model"),
    )
    result = solve_cvar_allocation(
        scenarios,
        costs,
        float(config["total_acres"]),
        float(config["budget"]),
        float(config["alpha"]),
        float(config["cvar_limit"]),
        lower_bounds,
        upper_bounds,
        dict(config.get("rotation_caps") or {}),
        crop_names,
        dict(config.get("contract_minimums") or {}),
    )
    row = {
        "theta": float(theta),
        "lambda_L": metadata["lower_tail_dependence"],
        "status": result.status,
        "expected_profit": result.expected_profit,
        "cvar_loss": result.cvar_loss,
        "var_loss": result.var_loss,
    }
    if result.allocation is not None:
        reversal, strong = ranking_reversal_flags(result.allocation, crop_names)
        row.update(
            {
                "ranking_reversal": reversal,
                "strong_reversal": strong,
            }
        )
        for idx, crop in enumerate(crop_names):
            row[f"acres_{crop}"] = float(result.allocation[idx])
    else:
        row.update({"ranking_reversal": False, "strong_reversal": False})
    row.update({f"diagnostic_{key}": value for key, value in result.diagnostics.items() if isinstance(value, (int, float))})
    return row


def ranking_reversal_threshold_experiment(config: Dict[str, object]) -> pd.DataFrame:
    rows = [solve_for_theta(config, theta) for theta in config["theta_grid"]]
    return pd.DataFrame(rows)


def first_reversal_threshold(df: pd.DataFrame) -> Optional[float]:
    reversed_rows = df.loc[df["ranking_reversal"] == True]  # noqa: E712
    if reversed_rows.empty:
        return None
    return float(reversed_rows.sort_values("lambda_L").iloc[0]["lambda_L"])


def _threshold_for_config(config: Dict[str, object], n_scenarios: Optional[int] = None) -> Tuple[Optional[float], pd.DataFrame]:
    rows = [solve_for_theta(config, theta, n_scenarios=n_scenarios) for theta in config["theta_grid"]]
    df = pd.DataFrame(rows)
    return first_reversal_threshold(df), df


def run_robustness_checks(config: Dict[str, object]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Run one-at-a-time robustness checks plus an alpha-kappa heatmap grid."""

    base = deepcopy(config)
    robustness = dict(base.get("robustness") or {})
    n_scenarios = int(robustness.get("n_scenarios", 2500))
    rows = []

    def add_result(check: str, value: object, cfg: Dict[str, object], scenarios: Optional[int] = None) -> None:
        threshold, detail = _threshold_for_config(cfg, n_scenarios=scenarios or n_scenarios)
        rows.append(
            {
                "check": check,
                "value": value,
                "reversal_threshold_lambda_L": threshold,
                "reversal_observed": threshold is not None,
                "min_corn_acres": detail.get("acres_Corn", pd.Series(dtype=float)).min(),
                "max_soybean_acres": detail.get("acres_Soybean", pd.Series(dtype=float)).max(),
            }
        )

    for alpha in robustness.get("alpha_grid", [0.85, 0.90, 0.95]):
        cfg = deepcopy(base)
        cfg["alpha"] = float(alpha)
        add_result("CVaR confidence alpha", alpha, cfg)

    for kappa in robustness.get("kappa_grid", [20000, 30000, 40000]):
        cfg = deepcopy(base)
        cfg["cvar_limit"] = float(kappa)
        add_result("CVaR limit kappa", kappa, cfg)

    for budget in robustness.get("budget_grid", [180000, 220000, 260000]):
        cfg = deepcopy(base)
        cfg["budget"] = float(budget)
        add_result("Budget B", budget, cfg)

    for cap_share in robustness.get("corn_cap_share_grid", [0.50, 0.60, 0.70, 0.80]):
        cfg = deepcopy(base)
        cfg["rotation_caps"] = {"Corn": float(cap_share) * float(cfg["total_acres"])}
        add_result("Corn rotation cap share", cap_share, cfg)

    soybean_mean = float(base["means"]["Soybean"])
    for gap in robustness.get("corn_soybean_margin_gaps", [65, 45, 30]):
        cfg = deepcopy(base)
        cfg["means"]["Corn"] = soybean_mean + float(gap)
        add_result("Corn-Soybean margin gap", gap, cfg)

    for scenario_count in robustness.get("scenario_count_grid", [1000, 5000, 10000]):
        cfg = deepcopy(base)
        add_result("Monte Carlo scenario count", scenario_count, cfg, scenarios=int(scenario_count))

    for family in robustness.get("copula_families", ["Gaussian", "Clayton"]):
        cfg = deepcopy(base)
        if family.lower() == "gaussian":
            cfg["theta_grid"] = [0.0]
            threshold = None
            rows.append(
                {
                    "check": "Copula family",
                    "value": "Gaussian",
                    "reversal_threshold_lambda_L": threshold,
                    "reversal_observed": False,
                    "min_corn_acres": np.nan,
                    "max_soybean_acres": np.nan,
                }
            )
        else:
            add_result("Copula family", family, cfg)

    heatmap_rows = []
    for alpha in robustness.get("alpha_grid", [0.85, 0.90, 0.95]):
        for kappa in robustness.get("kappa_grid", [20000, 30000, 40000]):
            cfg = deepcopy(base)
            cfg["alpha"] = float(alpha)
            cfg["cvar_limit"] = float(kappa)
            threshold, _ = _threshold_for_config(cfg, n_scenarios=n_scenarios)
            heatmap_rows.append(
                {
                    "alpha": float(alpha),
                    "kappa": float(kappa),
                    "reversal_threshold_lambda_L": threshold if threshold is not None else np.nan,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(heatmap_rows)
