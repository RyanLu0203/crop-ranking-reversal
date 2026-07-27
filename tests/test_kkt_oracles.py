"""KKT, atom-safe CVaR, contract, risk-slack, and grid-oracle tests."""

from __future__ import annotations

import numpy as np

from crop_optimization.cvar_optimizer import (
    solve_cvar_allocation,
    solve_expected_profit_allocation,
    solve_minimum_cvar_allocation,
)
from crop_optimization.evaluation import empirical_var_cvar_losses
from crop_optimization.oracles import rockafellar_uryasev_cvar_oracle, two_crop_grid_oracle


def test_atom_safe_direct_cvar_matches_independent_ru_oracle():
    losses = np.array([0.0, 0.0, 10.0, 10.0, 30.0])
    direct_var, direct_cvar = empirical_var_cvar_losses(losses, 0.6)
    oracle_var, oracle_cvar = rockafellar_uryasev_cvar_oracle(losses, 0.6)
    assert np.isclose(direct_cvar, oracle_cvar)
    assert oracle_var in set(losses)
    assert direct_var in set(losses)


def test_binding_risk_kkt_and_tail_weights_are_complete():
    scenarios = np.array([[100.0, 10.0], [-40.0, 10.0], [100.0, 10.0], [-40.0, 10.0]])
    result = solve_cvar_allocation(
        scenarios, [1.0, 1.0], 1.0, 10.0, 0.5, 0.0,
        [0.0, 0.0], [1.0, 1.0], {"Corn": 1.0}, ["Corn", "Soybean"],
    )
    diagnostics = result.diagnostics
    assert result.status == "optimal"
    assert diagnostics["risk_dual_eta"] > 0
    assert np.isclose(diagnostics["tail_weight_sum"], 1.0)
    assert diagnostics["tail_weight_max"] <= diagnostics["tail_weight_cap"] + 1e-10
    assert diagnostics["tail_weight_violation"] <= 1e-10
    assert diagnostics["kkt_primal_residual"] <= 1e-8
    assert diagnostics["kkt_stationarity_residual"] <= 1e-8
    assert diagnostics["kkt_complementarity_residual"] <= 1e-8


def test_risk_slack_solution_matches_unconstrained_expected_profit_solution():
    scenarios = np.array([[30.0, 10.0], [-5.0, 10.0]])
    eo = solve_expected_profit_allocation(
        scenarios.mean(axis=0), [1.0, 1.0], 1.0, 10.0,
        [0.0, 0.0], [1.0, 1.0], {}, ["A", "B"],
    )
    cvar = solve_cvar_allocation(
        scenarios, [1.0, 1.0], 1.0, 10.0, 0.5, 100.0,
        [0.0, 0.0], [1.0, 1.0], {}, ["A", "B"],
    )
    assert np.allclose(cvar.allocation, eo.allocation)
    assert cvar.diagnostics["cvar_binds"] is False
    assert np.isclose(cvar.diagnostics["risk_dual_eta"], 0.0)


def test_contract_minimum_is_named_active_constraint_with_dual():
    result = solve_cvar_allocation(
        [[20.0, 5.0], [20.0, 5.0]], [1.0, 1.0], 1.0, 10.0, 0.5, 0.0,
        [0.0, 0.0], [1.0, 1.0], {}, ["A", "B"], {"B": 0.3},
    )
    assert np.isclose(result.allocation[1], 0.3)
    assert result.diagnostics["contract_binds_B"] is True
    assert result.diagnostics["contract_binds"] is True
    assert "shadow_price_contract_B" in result.diagnostics


def test_two_crop_grid_oracle_matches_lp_on_grid_aligned_solution():
    scenarios = np.array([[100.0, 10.0], [-40.0, 10.0], [100.0, 10.0], [-40.0, 10.0]])
    lp = solve_cvar_allocation(
        scenarios, [1.0, 1.0], 1.0, 1.0, 0.5, 0.0,
        [0.0, 0.0], [1.0, 1.0], {}, ["A", "B"],
    )
    oracle = two_crop_grid_oracle(scenarios, [1.0, 1.0], 1.0, 1.0, 0.5, 0.0, 0.1)
    assert oracle["status"] == "optimal_on_grid"
    assert np.allclose(lp.allocation, oracle["allocation"], atol=1e-8)
    assert np.isclose(lp.expected_profit, oracle["objective"])


def test_infeasible_contract_is_reported_not_repaired_silently():
    result = solve_cvar_allocation(
        [[10.0, 10.0], [10.0, 10.0]], [1.0, 1.0], 1.0, 10.0, 0.5, 0.0,
        [0.0, 0.0], [1.0, 1.0], {}, ["A", "B"], {"A": 0.8, "B": 0.8},
    )
    assert result.status == "infeasible_or_failed"
    assert result.allocation is None


def test_shared_labour_capacity_enters_cvar_kkt_and_binds():
    scenarios = np.array([[30.0, 10.0], [30.0, 10.0]])
    shared = {
        "planting_labour": {
            "coefficients": {"A": 2.0, "B": 0.5},
            "capacity": 1.0,
        }
    }
    result = solve_cvar_allocation(
        scenarios, [1.0, 1.0], 1.0, 10.0, 0.5, 0.0,
        [0.0, 0.0], [1.0, 1.0], {}, ["A", "B"],
        shared_capacity_constraints=shared,
    )
    assert result.status == "optimal"
    assert np.isclose(2.0 * result.allocation[0] + 0.5 * result.allocation[1], 1.0)
    assert result.diagnostics["shared_capacity_binds_planting_labour"] is True
    assert result.diagnostics["shared_capacity_binds"] is True
    assert "shadow_price_shared_capacity_planting_labour" in result.diagnostics
    assert result.diagnostics["kkt_stationarity_residual"] <= 1e-8


def test_shared_equipment_capacity_enters_expected_profit_problem():
    shared = {
        "harvest_equipment": {
            "coefficients": [3.0, 1.0],
            "capacity": 1.5,
        }
    }
    result = solve_expected_profit_allocation(
        [20.0, 10.0], [1.0, 1.0], 1.0, 10.0,
        [0.0, 0.0], [1.0, 1.0], {}, ["A", "B"],
        shared_capacity_constraints=shared,
    )
    assert result.status == "optimal"
    assert np.isclose(3.0 * result.allocation[0] + result.allocation[1], 1.5)
    assert "shadow_price_shared_capacity_harvest_equipment" in result.diagnostics


def test_shared_capacity_rejects_unknown_crop():
    with np.testing.assert_raises(ValueError):
        solve_cvar_allocation(
            [[10.0, 10.0]], [1.0, 1.0], 1.0, 10.0, 0.5, 0.0,
            [0.0, 0.0], [1.0, 1.0], {}, ["A", "B"],
            shared_capacity_constraints={
                "labour": {
                    "coefficients": {"A": 1.0, "C": 2.0},
                    "capacity": 1.0,
                }
            },
        )


def test_minimum_cvar_endpoint_honours_shared_capacity():
    scenarios = np.array([[40.0, 8.0], [-30.0, 8.0], [40.0, 8.0], [-30.0, 8.0]])
    result = solve_minimum_cvar_allocation(
        scenarios, [1.0, 1.0], 1.0, 10.0, 0.5,
        [0.0, 0.0], [1.0, 1.0], {}, ["A", "B"],
        shared_capacity_constraints={
            "labour": {
                "coefficients": {"A": 2.0, "B": 1.0},
                "capacity": 1.0,
            }
        },
    )
    assert result.status == "optimal"
    assert result.cvar_loss <= 1e-8
    assert 2.0 * result.allocation[0] + result.allocation[1] <= 1.0 + 1e-8
