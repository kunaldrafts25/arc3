"""Actual Linux sandbox RPC and ToolAgent persistence gates, without model inference."""
import json
import os
from pathlib import Path


def run_probe(base_probe):
    os.environ.setdefault('LOCAL_ANALYZER_MODEL_ID', 'synthetic-cpu-probe')
    mechanical = base_probe['run_probe'](enforce_probes=False)
    from inference.agent.python_tool_sandbox import run_sandboxed_python
    from inference.agent.hydra_prediction_host import PredictionSession
    from inference.agent.runtime_state import Frame, HistoryEntry, write_runtime_state
    from inference.agent.tool_agent import ToolAgent

    root = Path('/kaggle/working/prediction-host-probe')
    root.mkdir(exist_ok=True)
    state = dict(current_frame=dict(ascii='RB\nBB', shape=[2,2], step=0, level=1), history=[], valid_actions=['RIGHT'])
    calls = []
    def handler(actions, **kwargs):
        calls.extend(actions)
        state['current_frame'] = dict(ascii='BR\nBB', shape=[2,2], step=state['current_frame']['step']+len(actions), level=1)
        return dict(action_result=dict(executed=True, gameplay_changed=True), state=state)
    def call(code, path='rpc.prediction.json', timeout=5):
        session = PredictionSession(root/path, lambda:state)
        return run_sandboxed_python(code=code, timeout_seconds=timeout, initial_state=state,
            action_handler=session.wrap_action(handler), prediction_handler=session.rpc)
    start = "prediction_start(['move','stay','unknown'], {'red':['bbox','R']}, question='Does the measured color move?')\n"
    forecast = "prediction_forecast({'r':{'action':{'action':'RIGHT'},'predictions':{'move':{'red':[0,1,1,2]},'stay':{'red':[0,1,0,1]},'unknown':None}}})\n"
    cases = []
    result = call(start+forecast)
    assert not result['error'] and len(calls) == 0, result
    cases.append('actual_rpc_freezes_before_action_without_spending_actions')
    result = call("action('RIGHT')\nresult=prediction_status()")
    assert not result['error'] and len(calls) == 1, result
    status = result['result']
    assert status['models']['move']['consistent'] == 1, status
    assert status['models']['stay']['status'] == 'contradicted', status
    assert status['models']['unknown']['abstained'] == 1, status
    cases.append('host_measures_after_original_action_and_returns_counterexample')
    result = call('result=prediction_status()')
    assert result['result']['models']['stay']['counterexample']['after_step'] == 1, result
    cases.append('counterexample_survives_sandbox_and_session_restart')
    result = call(start+forecast+"action(['RIGHT','RIGHT'])\nresult=prediction_status()", 'batch.prediction.json')
    assert not result['error'] and len(calls) == 3, result
    assert not result['result']['last_outcome']['checked'], result
    assert all(m['status']=='untested' for m in result['result']['models'].values()), result
    cases.append('ordinary_batch_is_unchanged_and_not_falsely_verified')
    result = call(start+forecast+"action('RIGHT')\nwhile True: pass", 'timeout.prediction.json', timeout=2)
    assert result['error'] and len(calls) == 4, result
    restored = PredictionSession(root/'timeout.prediction.json', lambda:state).status()
    assert restored['models']['stay']['status'] == 'contradicted', restored
    assert restored['pending'] is None
    cases.append('post_action_timeout_cannot_erase_host_owned_evidence')
    result = call("result=prediction_start(['x'], {'bad':['cell',-1,0]})", 'invalid.prediction.json')
    assert 'outside observed grid' in result['error'] and len(calls) == 4, result
    cases.append('invalid_measurement_rejected_without_accidental_action')

    path = root/'first.runtime.json'
    frame = Frame(grid=((8,5),(5,5)), step=0, level=1)
    write_runtime_state(path, current_frame=frame, history=[HistoryEntry(action='', frame=frame)])
    agent = ToolAgent(model='local', provider='vllm', base_url='http://127.0.0.1:9/v1')
    agent._current_valid_actions = ['RIGHT']
    response = agent._run_python_tool(path, dict(code=start+forecast))
    payload = json.loads(response.content)
    assert 'error' not in payload, payload
    assert path.with_suffix('.prediction.json').exists()
    cases.append('actual_toolagent_routes_rpc_and_persists_frozen_forecast')
    agent._history_messages = []
    other = ToolAgent(model='local', provider='vllm', base_url='http://127.0.0.1:9/v1')
    other._current_valid_actions = ['RIGHT']
    response = other._run_python_tool(path, dict(code='result=prediction_status()'))
    payload = json.loads(response.content)
    assert payload['result']['pending']['step'] == 0, payload
    prompt = other._build_user_prompt(0, valid_actions=['RIGHT'], current_frame=frame,
                                     history_entries=[HistoryEntry(action='',frame=frame)])
    assert 'Frozen prediction evidence' in prompt and 'Does the measured color move?' in prompt
    cases.append('actual_new_toolagent_and_drained_context_restore_feedback')
    second = root/'second.runtime.json'
    write_runtime_state(second, current_frame=frame, history=[])
    response = other._run_python_tool(second, dict(code='result=prediction_status()'))
    assert 'prediction_start first' in json.loads(response.content).get('error',''), response.content
    cases.append('same_directory_game_paths_isolate_predictions')

    state['current_frame'] = dict(ascii='RB\nBB',shape=[2,2],step=0,level=1)
    session = PredictionSession(root/'write-failure.prediction.json',lambda:state)
    result = run_sandboxed_python(code=start+forecast,timeout_seconds=5,initial_state=state,
        action_handler=session.wrap_action(handler),prediction_handler=session.rpc)
    assert not result['error'],result
    original_save = session._save
    saves = []
    def failed_save(*args,**kwargs):
        saves.append(1)
        if len(saves) == 2:
            raise OSError('synthetic post-action write failure')
        return original_save(*args,**kwargs)
    session._save = failed_save
    before = len(calls)
    result = run_sandboxed_python(code="result=action('RIGHT')",timeout_seconds=5,initial_state=state,
        action_handler=session.wrap_action(handler),prediction_handler=session.rpc)
    assert not result['error'] and len(calls) == before+1,result
    assert len(result['action_results']) == 1 and result['action_results'][0]['executed'],result
    assert 'hydra_prediction_warning' in result['action_results'][0],result
    assert session.status()['last_outcome']['checked'] is False
    cases.append('actual_rpc_preserves_executed_action_despite_post_action_write_failure')

    path.with_suffix('.prediction.json').write_text('{synthetic corrupt store')
    response = agent._run_python_tool(path,dict(code='result=read_cells([(0,0)])'))
    payload = json.loads(response.content)
    assert 'error' not in payload and payload['result']['cells'][0]['color'] == 'R',payload
    cases.append('corrupt_optional_prediction_store_keeps_actual_toolagent_observation_tool_working')

    state['current_frame'] = dict(ascii='RB\nBB',shape=[2,2],step=0,level=1)
    session = PredictionSession(root/'boundary.prediction.json',lambda:state)
    result = run_sandboxed_python(code=start+forecast,timeout_seconds=5,initial_state=state,
        action_handler=session.wrap_action(handler),prediction_handler=session.rpc)
    assert not result['error'],result
    def boundary_handler(actions,**kwargs):
        calls.extend(actions)
        state['current_frame'] = dict(ascii='BR\nBB',shape=[2,2],step=1,level=2)
        return dict(state=state,action_result=dict(executed=True))
    result = run_sandboxed_python(code="action('RIGHT')\nresult=prediction_status()",timeout_seconds=5,
        initial_state=state,action_handler=session.wrap_action(boundary_handler),prediction_handler=session.rpc)
    assert not result['error'] and not result['result'].get('disabled'),result
    assert set(result['result']['models']) == {'move','stay','unknown'},result
    assert result['result']['last_outcome']['checked'] is False,result
    cases.append('observed_level_boundary_without_flag_is_unchecked_without_disabling_tools')

    report = dict(passed=True, cases=cases, base_mechanical_cases=len(mechanical['cases']),
                  prompt_combinations=16, actual_synthetic_actions=len(calls),event_format=2,
                  boundary='Actual sandbox/ToolAgent CPU checks. No model inference or ARC gameplay benefit established.')
    (root.parent/'prediction-probe.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PREDICTION_CPU_PROBE_PASSED', json.dumps(report), flush=True)
    return report
