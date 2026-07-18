"""Frozen experiment-design loading, validation, and deterministic expansion."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import yaml
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DESIGN = ROOT / "simulation/configs/experiment_design.yaml"
CONTINUOUS_FACTORS = [
    "kendall_tau", "alpha", "risk_limit_frontier_quantile",
    "budget_to_max_cost_ratio", "dominant_crop_cap_share", "contract_minimum_share",
]


def design_sha256(path: Path = DEFAULT_DESIGN) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_experiment_design(path: Path = DEFAULT_DESIGN) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        design = yaml.safe_load(handle)
    validate_experiment_design(design)
    design["design_sha256"] = design_sha256(path)
    return design


def validate_experiment_design(design: Dict[str, Any]) -> None:
    if design.get("status") != "FROZEN_BEFORE_FORMAL_RUN":
        raise ValueError("experiment design must be frozen before a formal run")
    if design.get("scientific_scope", {}).get("land_unit") != "normalized_share":
        raise ValueError("canonical land unit must be normalized_share")
    cfg = design.get("design", {})
    if int(cfg.get("formal_scenarios", 0)) <= int(cfg.get("dry_run_scenarios", 0)):
        raise ValueError("formal scenario count must exceed dry-run count")
    seeds = list(cfg.get("replication_seeds", []))
    if len(seeds) != int(cfg.get("formal_replications_per_cell", -1)):
        raise ValueError("replication seed count does not match frozen replications")
    if len(seeds) != len(set(seeds)):
        raise ValueError("replication seeds must be unique")
    factors = design.get("factors", {})
    for name in CONTINUOUS_FACTORS:
        factor = factors.get(name, {})
        low, high = factor.get("range", [None, None])
        if factor.get("type") != "continuous_lhs" or low is None or not float(low) < float(high):
            raise ValueError(f"invalid continuous factor: {name}")
        if not factor.get("evidence_status"):
            raise ValueError(f"missing evidence status: {name}")
    for name in ("marginal_family", "copula_family"):
        factor = factors.get(name, {})
        if not factor.get("values") or not factor.get("evidence_status"):
            raise ValueError(f"invalid categorical factor: {name}")
    tolerances = design.get("tolerances", {})
    if any(float(value) <= 0 for value in tolerances.values()):
        raise ValueError("all numerical tolerances must be positive")
    if not design.get("falsification"):
        raise ValueError("falsification criteria are required")


def _scale_lhs(unit: np.ndarray, design: Dict[str, Any]) -> np.ndarray:
    ranges = np.asarray(
        [design["factors"][name]["range"] for name in CONTINUOUS_FACTORS], dtype=float
    )
    return qmc.scale(unit, ranges[:, 0], ranges[:, 1])


def expand_lhs_cells(design: Dict[str, Any]) -> pd.DataFrame:
    n_per = int(design["design"]["lhs_cells_per_copula_family"])
    seed = int(design["design"]["lhs_seed"])
    copulas = list(design["factors"]["copula_family"]["values"])
    marginals = list(design["factors"]["marginal_family"]["values"])
    rows: List[Dict[str, Any]] = []
    for family_index, copula in enumerate(copulas):
        sampler = qmc.LatinHypercube(d=len(CONTINUOUS_FACTORS), seed=seed + family_index)
        values = _scale_lhs(sampler.random(n=n_per), design)
        for local_index, vector in enumerate(values):
            row: Dict[str, Any] = {
                "cell_id": f"LHS-{family_index + 1:02d}-{local_index + 1:03d}",
                "cell_type": "lhs",
                "copula_family": copula,
                "marginal_family": marginals[(local_index + family_index) % len(marginals)],
            }
            row.update({name: float(value) for name, value in zip(CONTINUOUS_FACTORS, vector)})
            rows.append(row)
    return pd.DataFrame(rows)


def expand_anchor_cells(design: Dict[str, Any]) -> pd.DataFrame:
    count = int(design["design"]["anchor_cells"])
    anchors = design["anchors"]
    copulas = list(anchors["copula_families"])
    marginals = list(anchors["marginal_families"])
    taus = list(anchors["dependence_levels_kendall_tau"])
    alphas = list(anchors["alpha_levels"])
    operations = list(anchors["operational_regimes"])
    risks = list(anchors["risk_regimes"])
    operation_values = {
        "unrestricted": (1.10, 1.0, 0.0),
        "budget_tight": (0.70, 1.0, 0.0),
        "rotation_tight": (1.10, 0.35, 0.0),
        "contract_minimum": (1.10, 1.0, 0.15),
    }
    risk_quantile = {"slack": 0.90, "frontier": 0.50, "binding": 0.10}
    rows: List[Dict[str, Any]] = []
    for index in range(count):
        operation = operations[index % len(operations)]
        risk = risks[(index // len(operations)) % len(risks)]
        budget, cap, contract = operation_values[operation]
        rows.append({
            "cell_id": f"ANCHOR-{index + 1:03d}",
            "cell_type": "anchor",
            "copula_family": copulas[index % len(copulas)],
            "marginal_family": marginals[(index // len(copulas)) % len(marginals)],
            "kendall_tau": float(taus[index % len(taus)]),
            "alpha": float(alphas[(index // len(taus)) % len(alphas)]),
            "risk_limit_frontier_quantile": risk_quantile[risk],
            "budget_to_max_cost_ratio": budget,
            "dominant_crop_cap_share": cap,
            "contract_minimum_share": contract,
            "operational_regime": operation,
            "risk_regime": risk,
        })
    return pd.DataFrame(rows)


def expand_design(design: Dict[str, Any]) -> pd.DataFrame:
    cells = pd.concat(
        [expand_lhs_cells(design), expand_anchor_cells(design)], ignore_index=True, sort=False
    )
    expected = (
        int(design["design"]["lhs_cells_per_copula_family"])
        * len(design["factors"]["copula_family"]["values"])
        + int(design["design"]["anchor_cells"])
    )
    if len(cells) != expected or cells["cell_id"].duplicated().any():
        raise ValueError("expanded design cardinality or cell IDs are invalid")
    cells["design_id"] = design["design_id"]
    cells["design_sha256"] = design["design_sha256"]
    return cells
