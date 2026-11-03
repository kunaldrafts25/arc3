"""Test simultaneous memory/prediction use in the actual composed host and child."""
import json
from pathlib import Path


def run_probe(prediction_report,study_report):
    from inference.agent.hydra_prediction_host import PredictionSession
    from inference.agent.hydra_study import load_store
    from inference.agent.python_tool_sandbox import run_sandboxed_python
    from inference.agent.runtime_state import Frame,HistoryEntry,write_runtime_state
    from inference.agent.tool_agent import ToolAgent

    root = Path('/kaggle/working/prediction-study-probe');root.mkdir(exist_ok=True)
    cases = []
    frame = Frame(grid=((8,5),(5,5)),step=0,level=1)
    history = [HistoryEntry(action='',frame=frame)]
    path = root/'first.runtime.json'
    write_runtime_state(path,current_frame=frame,history=history)
    agent = ToolAgent(model='local',provider='vllm',base_url='http://127.0.0.1:9/v1')
    agent._current_valid_actions = ['RIGHT']
    start = "remember('motion','A competing movement explanation remains untested',scope='game')\nprediction_start(['move','stay'], {'red':['bbox','R']}, question='Which measured outcome follows RIGHT?')\n"
    forecast = "prediction_forecast({'r':{'action':{'action':'RIGHT'},'predictions':{'move':{'red':[0,1,1,2]},'stay':{'red':[0,1,0,1]}}}})\n"
    response = agent._run_python_tool(path,dict(code=start+forecast))
    payload = json.loads(response.content)
    assert 'error' not in payload,payload
    assert load_store(path.with_suffix('.study.json'))['notes']['motion']['status'] == 'hypothesis'
    session = PredictionSession(path.with_suffix('.prediction.json'),lambda:dict(
        current_frame=dict(ascii='RB\nBB',shape=[2,2],step=0,level=1)))
    assert session.status()['pending']['step'] == 0
    cases.append('one_actual_host_call_persists_memory_and_frozen_forecast')

    other = ToolAgent(model='local',provider='vllm',base_url='http://127.0.0.1:9/v1')
    other._current_valid_actions = ['RIGHT']
    response = other._run_python_tool(path,dict(code='result=[recall(),prediction_status(),read_cells([(0,0)])]'))
    payload = json.loads(response.content)
    assert 'error' not in payload,payload
    assert payload['result'][0]['notes']['motion']['claim'].startswith('A competing')
    assert payload['result'][1]['pending']['step'] == 0
    assert payload['result'][2]['cells'][0]['color'] == 'R'
    prompt = other._build_user_prompt(0,valid_actions=['RIGHT'],current_frame=frame,history_entries=history)
    assert 'A competing movement explanation' in prompt and 'Which measured outcome follows RIGHT?' in prompt
    cases.append('new_host_and_empty_context_restore_both_panels_and_exact_inspection')

    state = dict(current_frame=dict(ascii='RB\nBB',shape=[2,2],step=0,level=1),
                 history=[],valid_actions=['RIGHT'],hydra_study=load_store(path.with_suffix('.study.json')))
    session = PredictionSession(root/'action.prediction.json',lambda:state)
    calls = []
    def handler(actions,**kwargs):
        calls.extend(actions)
        state['current_frame'] = dict(ascii='BR\nBB',shape=[2,2],step=1,level=1)
        return dict(action_result=dict(executed=True,gameplay_changed=True),state=state)
    result = run_sandboxed_python(code=start+forecast+"action('RIGHT')\nremember('motion','Selected red pixels moved on RIGHT',status='supported',evidence_steps=[1],scope='game')\nresult=[recall(),prediction_status()]",
        timeout_seconds=5,initial_state=state,action_handler=session.wrap_action(handler),prediction_handler=session.rpc)
    assert not result['error'],result
    assert len(calls) == 1 and len(result['action_results']) == 1,result
    assert result['hydra_study']['notes']['motion']['status'] == 'supported'
    assert result['result'][1]['models']['stay']['status'] == 'contradicted'
    cases.append('one_ordinary_action_updates_model_note_and_host_measured_counterexample')

    second = root/'other-game.runtime.json';write_runtime_state(second,current_frame=frame,history=history)
    response = other._run_python_tool(second,dict(code='result=recall()'))
    assert json.loads(response.content)['result']['notes'] == {}
    response = other._run_python_tool(second,dict(code='result=prediction_status()'))
    assert 'prediction_start first' in json.loads(response.content).get('error','')
    cases.append('both_extensions_isolate_different_games')
    report = dict(passed=True,prediction_cases=prediction_report['cases'],study_cases=study_report['study_cases'],
        combined_cases=cases,base_mechanical_cases=prediction_report['base_mechanical_cases'],
        prompt_combinations=prediction_report['prompt_combinations'],
        boundary='CPU real host/child compatibility only. No model proposals, ARC gameplay, score gain or promotion established.')
    (root.parent/'prediction-study-probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PREDICTION_STUDY_CPU_PROBE_PASSED',json.dumps(report),flush=True)
    return report
