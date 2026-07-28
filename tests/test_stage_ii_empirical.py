from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "empirical/src"))

from crop_empirical.stage_ii_analysis import (  # noqa: E402
    build_transition_panel,
    claim_boundaries,
    load_stage_ii_design,
    model_observed_boundary,
    rank_transition_events,
)


def test_stage_ii_transition_panel_is_lagged_and_share_conserving():
    panel = pd.read_csv(ROOT / "data/processed/empirical_state_crop_analysis_panel.csv")
    transition = build_transition_panel(panel)
    assert len(transition) == 612
    assert transition["decision_year"].sub(transition["lag_year"]).eq(1).all()
    totals = transition.groupby(["ranking_definition", "state", "decision_year"])["acreage_share_change"].sum()
    assert np.allclose(totals, 0, atol=1e-12)


def test_rank_transition_events_retain_complete_definition_family():
    panel = pd.read_csv(ROOT / "data/processed/empirical_state_crop_analysis_panel.csv")
    events = rank_transition_events(build_transition_panel(panel))
    assert events.groupby("ranking_definition").size().eq(51).all()
    assert events["lagged_inversion_intensity"].between(0, 1).all()


def test_stage_ii_boundaries_separate_observed_model_and_unidentified():
    layers = model_observed_boundary().set_index("construct")["evidence_layer"]
    assert layers["state planted acreage"] == "DIRECTLY_OBSERVED"
    assert layers["E2 allocations and KKT pressures"] == "MODEL_GENERATED"
    assert layers["private budgets, rotations and contracts"] == "UNIDENTIFIED"
    boundaries = claim_boundaries().set_index("claim_domain")["status"]
    assert boundaries["CVaR preference or binding"] == "NOT_IDENTIFIED"
    assert boundaries["welfare effect"] == "NOT_IDENTIFIED"


def test_stage_ii_empirical_design_is_frozen():
    design = load_stage_ii_design()
    assert design["uncertainty"]["replications"] == 5000
    assert design["admitted_inputs"]["county_data_admitted"] is False
