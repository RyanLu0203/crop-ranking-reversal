import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "simulation/outputs"


def test_formal_run_cardinality_and_replay():
    primary = pd.read_csv(OUTPUT / "formal_results.csv")
    replay = pd.read_csv(OUTPUT / "independent_replay.csv")
    assert len(primary) == 450
    assert primary["cell_id"].nunique() == 90
    assert primary["solver_status"].eq("optimal").all()
    assert len(replay) == 450
    assert replay["verification_pass"].all()


def test_direct_cvar_and_kkt_tolerances():
    primary = pd.read_csv(OUTPUT / "formal_results.csv")
    assert (primary["cvar_loss"] - primary["risk_limit"]).max() <= 1e-7
    assert primary["kkt_primal_residual"].max() <= 1e-8
    assert primary["kkt_stationarity_residual"].max() <= 1e-7


def test_adverse_convergence_result_is_retained():
    convergence = pd.read_csv(OUTPUT / "convergence_summary.csv")
    summary = json.loads((OUTPUT / "summary.json").read_text())
    assert len(convergence) == 5
    assert not convergence["convergence_pass"].any()
    assert summary["headline_admissible"] is False


def test_information_flexibility_and_claim_boundaries():
    frame = pd.read_csv(OUTPUT / "information_flexibility.csv")
    info = frame.loc[frame["analysis"].eq("information")]
    flex = frame.loc[frame["analysis"].eq("flexibility")]
    assert info["value_of_information"].fillna(0).ge(-1e-12).all()
    assert flex["nested_value_nondecreasing"].fillna(False).all()
    assert frame["evidence_status"].str.contains("NOT_EMPIRICAL_EVIDENCE").all()
