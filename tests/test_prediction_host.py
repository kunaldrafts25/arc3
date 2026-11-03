from copy import deepcopy
import json

import pytest

from hydra.prediction_host import PredictionSession, measure, render_panel


def view(step=0, level=1, ascii='RB\nBB'):
    return dict(ascii=ascii, shape=[2, 2], step=step, level=level)


def setup_session(tmp_path):
    state = dict(current_frame=view())
    path = tmp_path/'game.prediction.json'
    session = PredictionSession(path, lambda: state)
    session.rpc(dict(operation='start', models=['moves', 'stays', 'unknown'],
                     features={'red': ['bbox', 'R'], 'corner': ['cell', 0, 0]}, question='Does red move?'))
    return state, path, session


def forecast(session, predictions=None):
    return session.rpc(dict(operation='forecast', probes={'right':dict(
        action={'action':'RIGHT'}, predictions=predictions or {
            'moves': {'red':[0,1,1,2]}, 'stays': {'red':[0,1,0,1]}, 'unknown': None})}))


def test_host_freezes_then_measures_actual_frame_and_persists_counterexample(tmp_path):
    state, path, session = setup_session(tmp_path)
    predictions = {'moves': {'red':[0,1,1,2]}, 'stays': {'red':[0,1,0,1]}}
    forecast(session, predictions)
    predictions['stays']['red'] = [0,1,1,2]
    calls = []
    def action(actions, **kwargs):
        calls.extend(actions)
        state['current_frame'] = view(1, ascii='BR\nBB')
        return dict(state=deepcopy(state), action_result={'executed':True})
    original = session.wrap_action(action)([{'action':'RIGHT'}])
    assert len(calls) == 1 and original['action_result']['executed']
    restored = PredictionSession(path, lambda: state).status()
    assert restored['models']['moves']['consistent'] == 1
    assert restored['models']['stays']['counterexample']['differences']['red']['observed'] == [0,1,1,2]
    assert restored['models']['unknown']['abstained'] == 1
    assert 'contradicted' in render_panel(path, 1)
    assert render_panel(path, 2) == ''


def test_pending_survives_new_tool_instance_and_uses_no_model_outcome(tmp_path):
    state, path, session = setup_session(tmp_path)
    forecast(session)
    session = PredictionSession(path, lambda: state)
    assert session.status()['pending']['step'] == 0
    with pytest.raises(ValueError, match='Unknown'):
        session.rpc(dict(operation='resolve', observed={'red':[9,9,9,9]}))
    with pytest.raises(ValueError, match='declared measured'):
        session.rpc(dict(operation='forecast', probes={'r':dict(action={'action':'RIGHT'},
                        predictions={'moves': {'invented_goal': True}})}))
    assert json.loads(path.read_text())['ledger']['pending']['step'] == 0


@pytest.mark.parametrize('commands', [[{'action':'LEFT'}], [{'action':'RIGHT'}, {'action':'RIGHT'}]])
def test_different_action_or_batch_keeps_original_behavior_without_false_checks(tmp_path, commands):
    state, path, session = setup_session(tmp_path)
    forecast(session)
    calls = []
    sentinel = dict(action_result={'executed':True}, state=state)
    def handler(actions, **kwargs):
        calls.append(deepcopy(actions))
        return sentinel
    assert session.wrap_action(handler)(commands) is sentinel
    assert calls == [commands]
    status = session.status()
    assert not status['last_outcome']['checked'] and status['pending'] is None
    assert all(m['status'] == 'untested' for m in status['models'].values())


@pytest.mark.parametrize('outcome,step,level', [({'executed':False},0,1),
    ({'executed':True,'game_over':True},1,1), ({'executed':True,'level_completed':True},1,2),
    ({'executed':True},3,1), ({'executed':True},1,2)])
def test_refusal_boundaries_and_skipped_steps_cannot_certify_rules(tmp_path,outcome,step,level):
    state, path, session = setup_session(tmp_path)
    forecast(session)
    def handler(*args, **kwargs):
        state['current_frame'] = view(step,level)
        return dict(action_result=outcome, state=state)
    session.wrap_action(handler)([{'action':'RIGHT'}])
    status = session.status()
    assert not status['last_outcome']['checked']
    assert set(status['models']) == {'moves','stays','unknown'}
    assert all(m['status'] == 'untested' for m in status['models'].values())


def test_reset_invalidates_same_level_hypotheses_even_without_pending_probe(tmp_path):
    state, path, session = setup_session(tmp_path)
    session.wrap_action(lambda *args,**kwargs:dict(action_result={'executed':True},state=state))([{'action':'RESET'}])
    assert not session.status()['scope_current']
    with pytest.raises(ValueError, match='fresh hypotheses'):
        forecast(session)
    assert not render_panel(path,1)


def test_host_restart_after_interrupted_action_reports_uncertified_outcome(tmp_path):
    state, path, session = setup_session(tmp_path)
    forecast(session)
    session.data['in_flight'] = True
    session._save()
    restored = PredictionSession(path, lambda: state).status()
    assert restored['pending'] is None
    assert 'interrupted' in restored['last_outcome']['reason']
    assert all(m['status'] == 'untested' for m in restored['models'].values())


def test_stale_forecast_cancels_but_never_suppresses_next_action(tmp_path):
    state, path, session = setup_session(tmp_path)
    forecast(session)
    state['current_frame'] = view(1)
    calls = []
    session.wrap_action(lambda *args,**kwargs: calls.append(args) or dict(action_result={},state=state))([{'action':'RIGHT'}])
    assert len(calls) == 1
    assert 'observation changed' in session.status()['last_outcome']['reason']


def test_new_game_path_does_not_read_other_game_memory(tmp_path):
    state, path, session = setup_session(tmp_path)
    forecast(session)
    other = PredictionSession(tmp_path/'other.prediction.json', lambda:state)
    with pytest.raises(ValueError, match='start first'):
        other.status()


def test_feature_queries_are_exact_bounded_and_color_based():
    assert measure(view(), {'p':['cell',0,0], 'n':['count','B',0,2,0,2], 'r':['bbox','R'],
                            'empty':['bbox','Y']}) == dict(p='R',n=3,r=[0,1,0,1],empty=None)
    with pytest.raises(ValueError, match='outside'):
        measure(view(), {'wrap':['cell',-1,0]})
    with pytest.raises(ValueError, match='Queries'):
        measure(view(), {'untrusted':['execute','some_code']})


def test_bad_forecast_does_not_mutate_durable_state(tmp_path):
    state, path, session = setup_session(tmp_path)
    before = path.read_bytes()
    with pytest.raises(ValueError):
        forecast(session, {'moves': {'red': float('nan')}})
    assert before == path.read_bytes()


def test_evidence_write_failure_after_real_action_preserves_action_result_and_count(tmp_path):
    state,path,session = setup_session(tmp_path)
    forecast(session)
    original_save = session._save
    saves,calls = [],[]
    def failing_save(*args,**kwargs):
        saves.append(1)
        if len(saves) == 2:
            raise OSError('synthetic full disk after action')
        return original_save(*args,**kwargs)
    session._save = failing_save
    reply = dict(action_result={'executed':True},state=state)
    def handler(actions,**kwargs):
        calls.append(actions)
        state['current_frame'] = view(1,ascii='BR\nBB')
        return reply
    result = session.wrap_action(handler)([{'action':'RIGHT'}])
    assert len(calls) == 1 and result is reply and result['action_result']['executed']
    assert 'hydra_prediction_warning' in result['action_result']
    assert not session.status()['last_outcome']['checked']


def test_complete_forecast_is_logged_before_dispatch_and_authoritative_outcome(tmp_path):
    state,path,session = setup_session(tmp_path)
    forecast(session)
    def handler(actions,**kwargs):
        events = [json.loads(line) for line in path.with_suffix('.events.jsonl').read_text().splitlines()]
        assert [e['event'] for e in events] == ['start','forecast','dispatch']
        assert events[1]['pending']['forecasts']['right']['stays']['red'] == [0,1,0,1]
        state['current_frame'] = view(1,ascii='BR\nBB')
        return dict(action_result={'executed':True},state=state)
    session.wrap_action(handler)([{'action':'RIGHT'}])
    events = [json.loads(line) for line in path.with_suffix('.events.jsonl').read_text().splitlines()]
    assert events[-1]['event'] == 'resolve'
    assert events[-1]['evidence']['observed']['red'] == [0,1,1,2]
    assert len(events[-1]['frame_sha256']) == 64


def test_write_failure_before_dispatch_keeps_ordinary_action_once_and_unverified(tmp_path):
    state,path,session = setup_session(tmp_path)
    forecast(session)
    calls = []
    session._save = lambda *a,**k:(_ for _ in ()).throw(OSError('synthetic full disk'))
    def handler(actions,**kwargs):
        calls.append(actions)
        return dict(action_result={'executed':True},state=state)
    result = session.wrap_action(handler)([{'action':'RIGHT'}])
    assert len(calls) == 1 and result['action_result']['executed']
    assert not session.status()['last_outcome']['checked']


def test_original_action_failure_survives_a_second_failure_in_cancel_logging(tmp_path):
    state,path,session = setup_session(tmp_path)
    forecast(session)
    original_save = session._save
    calls = []
    def handler(actions,**kwargs):
        calls.append(actions)
        session._save = lambda *a,**k:(_ for _ in ()).throw(OSError('secondary storage error'))
        raise RuntimeError('original action error')
    with pytest.raises(RuntimeError,match='original action error'):
        session.wrap_action(handler)([{'action':'RIGHT'}])
    assert len(calls) == 1


def test_corrupt_optional_store_does_not_disable_ordinary_action_execution(tmp_path):
    path = tmp_path/'bad.prediction.json'
    path.write_text('{corrupt')
    state = dict(current_frame=view())
    session = PredictionSession(path,lambda:state)
    calls = []
    def handler(actions,**kwargs):
        calls.append(actions)
        return dict(action_result={'executed':True},state=state)
    result = session.wrap_action(handler)([{'action':'RIGHT'}])
    assert result['action_result']['executed'] and len(calls) == 1
    assert session.status()['disabled']
    with pytest.raises(ValueError,match='unavailable'):
        session.rpc(dict(operation='status'))
    session.rpc(dict(operation='start',models=['fresh'],features={'r':['cell',0,0]},question='retry'))
    assert session.status()['models']['fresh']['status'] == 'untested'
