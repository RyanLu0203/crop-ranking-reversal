import numpy as np

from crop_simulation.copula_models import lower_tail_dependence


def test_clayton_tail_dependence_formula():
    theta = 2.0
    expected = 2 ** (-1.0 / theta)

    assert np.isclose(lower_tail_dependence("Clayton", theta), expected)
    assert 0.0 < lower_tail_dependence("Clayton", theta) < 1.0


def test_clayton_tail_dependence_monotonicity():
    theta_grid = [0.5, 1.0, 2.0, 4.0]
    lambdas = [lower_tail_dependence("Clayton", theta) for theta in theta_grid]

    assert all(0.0 < value < 1.0 for value in lambdas)
    assert lambdas == sorted(lambdas)
    assert len(set(lambdas)) == len(lambdas)
