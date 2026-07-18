from crop_optimization.evaluation import ranking_reversal_flags


def test_pairwise_ranking_reversal_detection():
    reversal, strong = ranking_reversal_flags([80.0, 120.0, 0.0], ["Corn", "Soybean", "Winter Wheat"])

    assert reversal is True
    assert strong is False


def test_no_reversal_when_acreage_order_preserved():
    reversal, strong = ranking_reversal_flags([120.0, 80.0, 0.0], ["Corn", "Soybean", "Winter Wheat"])

    assert reversal is False
    assert strong is False


def test_strong_reversal_detection():
    reversal, strong = ranking_reversal_flags([0.0, 50.0, 450.0], ["Corn", "Soybean", "Winter Wheat"])

    assert reversal is True
    assert strong is True


def test_classification_uses_acreage_not_expected_profit_ordering():
    high_profit_corn_allocation = [10.0, 20.0, 0.0]
    reversal, _ = ranking_reversal_flags(high_profit_corn_allocation, ["Corn", "Soybean", "Winter Wheat"])

    assert reversal is True
