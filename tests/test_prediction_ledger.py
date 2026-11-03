import pytest

from hydra.prediction_ledger import PredictionLedger, rank_probes


def test_forecast_is_frozen_before_outcome_and_can_only_be_consumed_once():
    ledger = PredictionLedger(['right', 'left'])
    forecasts = {'A': {'right': {'x': 1}, 'left': {'x': -1}}}
    proposal = ledger.commit(step=7, level=1, forecasts=forecasts)
    forecasts['A']['left']['x'] = 1  # Editing a proposal later cannot erase its error.
    result = ledger.resolve(proposal['ticket'], action='A', step=8, level=1, observed={'x': 1})
    assert result['active'] == ['right']
    assert result['verdicts']['left']['differences']['x']['expected'] == -1
    with pytest.raises(ValueError, match='consumed'):
        ledger.resolve(proposal['ticket'], action='A', step=8, level=1, observed={'x': 1})


def test_counterexample_of_all_candidates_requests_repair_without_forcing_a_winner():
    ledger = PredictionLedger(['a', 'b'])
    proposal = ledger.commit(step=0, level=1, forecasts={'A': {'a': {'x': 1}, 'b': {'x': 2}}})
    result = ledger.resolve(proposal['ticket'], action='A', step=1, level=1, observed={'x': 3})
    assert result['needs_new_hypotheses'] and not ledger.active()
    assert ledger.models['a']['counterexample']['differences']['x']['observed'] == 3


def test_missing_measurement_and_abstention_do_not_become_support_or_disagreement():
    ledger = PredictionLedger(['partial', 'unknown'])
    proposal = ledger.commit(step=0, level=1, forecasts={'A': {'partial': {'x': 1, 'mode': 2}, 'unknown': None}})
    assert proposal['suggested_probe'] is None
    result = ledger.resolve(proposal['ticket'], action='A', step=1, level=1, observed={'x': 1})
    assert result['verdicts']['partial']['verdict'] == 'insufficient_observation'
    assert ledger.models['partial']['consistent'] == 0
    assert result['verdicts']['unknown']['verdict'] == 'unknown'
    assert len(ledger.active()) == 2


def test_probe_cost_and_common_features_prevent_spurious_information():
    forecasts = {'cheap': {'a': {'x': 0}, 'b': {'x': 1}},
                 'expensive': {'a': {'x': 0}, 'b': {'x': 1}},
                 'different_fields': {'a': {'x': 0}, 'b': {'y': 1}}}
    ranked = rank_probes(forecasts, {'a': 1.0, 'b': 1.0}, {'cheap': 1, 'expensive': 9})
    assert ranked[0]['action'] == 'cheap' and ranked[0]['disagreement_bits'] == 1
    assert next(r for r in ranked if r['action'] == 'different_fields')['score'] == 0


def test_changing_unpredicted_counter_does_not_invalidate_a_local_prediction():
    ledger = PredictionLedger(['local'])
    proposal = ledger.commit(step=0, level=1, forecasts={'A': {'local': {'position': [3, 4]}}})
    result = ledger.resolve(proposal['ticket'], action='A', step=1, level=1,
                            observed={'position': [3, 4], 'counter': 999})
    assert result['verdicts']['local']['verdict'] == 'consistent'
    assert ledger.models['local']['status'] == 'consistent_on_observed_predictions'


def test_skipped_steps_are_rejected_and_level_boundary_is_not_a_physics_refutation():
    ledger = PredictionLedger(['local'])
    proposal = ledger.commit(step=9, level=1, forecasts={'A': {'local': {'x': 3}}})
    with pytest.raises(ValueError, match='next real action'):
        ledger.resolve(proposal['ticket'], action='A', step=11, level=1, observed={'x': 7})
    result = ledger.resolve(proposal['ticket'], action='A', step=10, level=2, observed={'x': 7})
    assert not result['checked'] and list(ledger.active()) == ['local']
    with pytest.raises(ValueError, match='fresh level-scoped'):
        ledger.commit(step=10, level=2, forecasts={'A': {'local': {'x': 3}}})


def test_game_restart_does_not_reuse_evidence_from_an_old_step_sequence():
    ledger = PredictionLedger(['local'])
    proposal = ledger.commit(step=9, level=1, forecasts={'A': {'local': {'x': 3}}})
    ledger.resolve(proposal['ticket'], action='A', step=10, level=1, observed={'x': 3})
    with pytest.raises(ValueError, match='backwards'):
        ledger.commit(step=0, level=1, forecasts={'A': {'local': {'x': 3}}})


def test_nested_boolean_does_not_silently_equal_numeric_measurement():
    ledger = PredictionLedger(['typed'])
    proposal = ledger.commit(step=0, level=1, forecasts={'A': {'typed': {'cells': [True]}}})
    result = ledger.resolve(proposal['ticket'], action='A', step=1, level=1, observed={'cells': [1]})
    assert result['needs_new_hypotheses']


def test_counterexample_survives_bounded_evidence_eviction():
    ledger = PredictionLedger(['wrong', 'right'], max_evidence=1)
    for step in range(3):
        proposal = ledger.commit(step=step, level=1,
                                 forecasts={'A': {'wrong': {'x': -1}, 'right': {'x': 1}}})
        ledger.resolve(proposal['ticket'], action='A', step=step+1, level=1, observed={'x': 1})
    assert len(ledger.evidence) == 1 and ledger.evidence_dropped == 2
    assert ledger.models['wrong']['counterexample']['after_step'] == 1


def test_abstaining_models_reduce_coverage_instead_of_being_counted_as_a_third_outcome():
    ranked = rank_probes({'A': {'a': {'x': 0}, 'b': {'x': 1}, 'c': None}},
                        {'a': 1.0, 'b': 1.0, 'c': 1.0})
    assert ranked[0]['disagreement_bits'] == 1
    assert ranked[0]['coverage'] == pytest.approx(2/3)
