import numpy as np
from hydra.abstraction import MeterDetector


def test_learns_monotone_edge_meter_preserves_raw_and_board_changes():
    initial = np.zeros((32, 32), dtype=np.int16)
    initial[0] = 7
    detector = MeterDetector()
    previous = initial.copy()
    for step in range(1, 6):
        current = initial.copy()
        current[0, :step] = 4
        detector.observe(previous, current)
        previous = current
    assert detector.mask[0].all()
    assert np.array_equal(detector.canonical(current), initial)
    assert current[0, 0] == 4
    current[10, 10] = 9
    assert detector.canonical(current)[10, 10] == 9


def test_reversal_revokes_abstraction_and_reset_clears_it():
    detector = MeterDetector()
    initial = np.zeros((32, 32), dtype=np.int16)
    initial[:, 0] = 7
    previous = initial.copy()
    for step in range(1, 6):
        current = initial.copy()
        current[:step, 0] = 4
        detector.observe(previous, current)
        previous = current
    assert detector.mask[:, 0].all()
    current = previous.copy()
    current[:5, 0] = 7
    detector.observe(previous, current)
    assert not detector.mask.any()
    assert detector.revocations >= 1
    detector.reset()
    assert detector.anchor is None


def test_interior_animation_and_large_edge_changes_are_not_masked():
    detector = MeterDetector()
    previous = np.zeros((32, 32), dtype=np.int16)
    for step in range(8):
        current = previous.copy()
        current[10, step] = 7
        current[0, :12] = step % 3
        detector.observe(previous, current)
        previous = current
    assert not detector.mask.any()
