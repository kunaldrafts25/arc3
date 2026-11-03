import pytest
from hydra.evaluation.metrics import official_game_score


def test_official_score_weights_caps_and_missing_baselines():
    assert official_game_score([True, False], [10, 10], [10, 10]) == pytest.approx(100/3)
    assert official_game_score([True, True], [10, 20], [10, 10]) == pytest.approx(50)
    assert official_game_score([True], [1], [10]) == 100
    assert official_game_score([True], [10], None) is None
    assert official_game_score([True], [10], [-1]) is None
    assert official_game_score([False], [10], [10]) == 0
