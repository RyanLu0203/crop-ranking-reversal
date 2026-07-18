import numpy as np
import pytest

from crop_optimization.information_flexibility import flexibility_config, information_flexibility_experiment


def test_phi_bounds(baseline_config):
    with pytest.raises(ValueError, match="phi must be in"):
        flexibility_config(baseline_config, -0.1)
    with pytest.raises(ValueError, match="phi must be in"):
        flexibility_config(baseline_config, 1.1)


def test_flexibility_relaxation_monotone(baseline_config):
    low = flexibility_config(baseline_config, 0.0)
    mid = flexibility_config(baseline_config, 0.5)
    high = flexibility_config(baseline_config, 1.0)

    assert low["budget"] <= mid["budget"] <= high["budget"]
    assert low["upper_bounds"]["Corn"] <= mid["upper_bounds"]["Corn"] <= high["upper_bounds"]["Corn"]
    assert low["rotation_caps"]["Corn"] <= mid["rotation_caps"]["Corn"] <= high["rotation_caps"]["Corn"]


def test_no_information_incremental_value_zero(baseline_config):
    df = information_flexibility_experiment(baseline_config)
    no_info = df.loc[df["signal_regime"] == "No information"]

    assert np.allclose(no_info["value_of_information"], 0.0)
    assert np.allclose(no_info["signal_expected_profit"], no_info["prior_expected_profit"])


def test_information_value_not_hardcoded_positive(baseline_config):
    df = information_flexibility_experiment(baseline_config)

    assert np.allclose(
        df["value_of_information"],
        df["signal_expected_profit"] - df["prior_expected_profit"],
    )
    assert np.isfinite(df["value_of_information"]).all()
