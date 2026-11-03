import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest

from hydra.verified_planning import install
from scripts.install_verified_agent import patched_sources


ROOT=Path(__file__).resolve().parents[1]


def frame(value, step=0, level=1):
    return SimpleNamespace(_grid=[[value]],step=step,level=level)


def transition(before, after, action='RIGHT', **result):
    return SimpleNamespace(before_frame=before,after_frame=after,action=action,result=result)


def setup(outcomes=None,terminal=False,enforce_probes=True):
    before, current=frame(0),frame(1,1)
    namespace=dict(current_frame=current,transitions=[transition(before,current)])
    spent=[]
    def raw(commands):
        spent.append(commands[0])
        prior=namespace['current_frame']
        value=(outcomes or {}).get(len(spent),prior._grid[0][0]+1)
        after=frame(value,prior.step+1,2 if terminal else prior.level)
        namespace['current_frame']=after
        namespace['transitions'].append(transition(prior,after,commands[0]['action']))
        return dict(executed=True,level_completed=terminal)
    def normalize(actions):
        if isinstance(actions,(str,dict)):
            actions=[actions]
        return [dict(action=a) if isinstance(a,str) else dict(a) for a in actions]
    namespace['action']=raw
    install(namespace,normalize,enforce_probes=enforce_probes)
    return namespace, spent


def increment(state, action):
    return [[state[0][0]+1]]


def test_optional_mode_preserves_raw_batches_repeated_calls_and_result():
    calls=[]
    result=dict(executed=True,executed_count=2,host_guard='preserved')
    def raw(commands):
        calls.append(commands)
        return result
    namespace=dict(action=raw)
    events=install(namespace,lambda actions:actions,enforce_probes=False)
    batch=[dict(action='RIGHT'),dict(action='LEFT')]
    assert namespace['action'](batch) is result
    assert namespace['action'](batch) is result
    assert calls==[batch,batch]
    assert not events  # Ordinary actions are accounted by the original host.


def test_optional_mode_still_checks_plans_and_blocks_impure_models():
    api,spent=setup({1:7},enforce_probes=False)
    report=api['execute_plan'](['RIGHT']*2,increment)
    assert report['stop_reason']=='prediction_mismatch' and len(spent)==1
    def impure(state,command):
        api['action']('RIGHT')
        return [[0]]
    assert 'cannot spend' in api['verify_model'](impure)['error']
    assert len(spent)==1


def test_correct_model_replays_history_and_checks_each_real_step():
    api, spent=setup()
    report=api['execute_plan'](['RIGHT']*3,increment)
    assert report['verification']['verified']
    assert report['executed']==3 and report['stop_reason']=='complete'
    assert len(spent)==3 and api['current_frame']._grid==[[4]]


def test_historical_counterexample_refuses_plan_without_spending_actions():
    api, spent=setup()
    report=api['execute_plan'](['RIGHT']*3,lambda state,action:[[99]])
    assert report['stop_reason']=='unverified_model'
    assert report['verification']['counterexample']['difference']['path']==[0,0]
    assert not spent


def test_prospective_mismatch_stops_before_second_action():
    api, spent=setup({1:7})
    report=api['execute_plan'](['RIGHT']*3,increment)
    assert report['stop_reason']=='prediction_mismatch'
    assert report['executed']==len(spent)==1
    assert report['counterexample']['difference']['observed']==7


def test_level_completion_stops_before_next_level_actions():
    api, spent=setup({1:99},terminal=True)
    report=api['execute_plan'](['RIGHT']*3,increment)
    assert report['stop_reason']=='terminal_or_level_boundary'
    assert report['executed']==len(spent)==1


def test_abstention_and_empty_history_are_not_certification():
    api, spent=setup()
    assert not api['verify_model'](lambda state,action:None)['verified']
    api['transitions']=[]
    assert not api['verify_model'](increment)['verified']
    assert not spent


def test_prediction_cannot_spend_actions_even_if_model_is_wrong():
    api, spent=setup()
    def cheating(state, action):
        api['action']('RIGHT')
        return [[1]]
    report=api['verify_model'](cheating)
    assert 'cannot spend' in report['error']
    assert not spent


def test_encoder_cannot_spend_actions():
    api, spent=setup()
    report=api['verify_model'](increment,lambda grid:api['action']('RIGHT'))
    assert not report['verified'] and 'cannot spend' in report['error']
    assert not spent


def test_constant_projection_is_not_a_useful_certificate():
    api, spent=setup()
    report=api['execute_plan'](['RIGHT']*3,lambda state,action:0,lambda grid:0)
    assert not report['verification']['verified']
    assert 'no observed state changes' in report['verification']['error']
    assert not spent


def test_probe_available_without_model_but_unverified_batches_are_refused():
    api, spent=setup()
    with pytest.raises(RuntimeError,match='One exploratory'):
        api['action'](['RIGHT','RIGHT'])
    assert not spent
    api['action']('RIGHT')
    with pytest.raises(RuntimeError,match='One exploratory'):
        api['action']('RIGHT')
    assert len(spent)==1


def test_scope_is_explicit_and_abstract_model_can_plan():
    api, spent=setup()
    report=api['execute_plan'](['RIGHT']*2,lambda state,action:state+1,lambda grid:grid[0][0])
    assert report['verification']['scope']=='abstract-state'
    assert report['verification']['encoded_changes']==1
    assert len(spent)==2


def test_truncated_replay_does_not_certify_partial_history():
    api, spent=setup()
    api['transitions'].append(transition(frame(1,1),frame(2,2)))
    report=api['execute_plan'](['RIGHT'],increment,max_checks=1)
    assert report['verification']['truncated'] and not report['verification']['verified']
    assert not spent


def test_mouse_coordinates_and_reset_boundary_are_preserved():
    api, spent=setup()
    api['transitions']=[transition(frame(9),frame(0),action='RESET'),
        transition(frame(0),frame(1,1),action='MOUSE(row=3, col=8)')]
    observed=[]
    def predict(state,action):
        observed.append(action)
        return increment(state,action)
    report=api['verify_model'](predict)
    assert report['verified'] and report['excluded']==1
    assert observed==[dict(action='MOUSE',row=3,col=8)]


def test_user_prompt_gate_detects_original_batching_contract(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'vendor/duck-m2/ARC3-Inference'))
    from scripts.verified_agent_probe import check_user_prompts
    original=(ROOT/'vendor/duck-m2/ARC3-Inference/inference/agent/tool_agent.py').read_text(encoding='utf-8')
    with pytest.raises(AssertionError,match='more than once'):
        check_user_prompts(original)
    sandbox=(ROOT/'vendor/duck-m2/ARC3-Inference/inference/agent/python_tool_sandbox.py').read_text(encoding='utf-8')
    _,agent=patched_sources(sandbox,original,(ROOT/'hydra/verified_planning.py').read_text(encoding='utf-8'))
    assert len(check_user_prompts(agent))==16


def test_patched_real_sandbox_executes_checked_plan(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'vendor/duck-m2/ARC3-Inference'))
    source=ROOT/'vendor/duck-m2/ARC3-Inference/inference/agent'
    sandbox,agent=patched_sources((source/'python_tool_sandbox.py').read_text(encoding='utf-8'),
        (source/'tool_agent.py').read_text(encoding='utf-8'),
        (ROOT/'hydra/verified_planning.py').read_text(encoding='utf-8'))
    from scripts.verified_agent_probe import check_prompt
    check_prompt(agent)
    module={'__name__':'hydra_sandbox_test'}
    exec(compile(sandbox,'patched-sandbox','exec'),module)
    def view(value,step):
        return dict(grid=[[value]],ascii=str(value),step=step,level=1,shape=[1,1])
    def state(value,step):
        return dict(current_frame=view(value,step),history=[
            dict(action='',frame=view(0,0)),dict(action='RIGHT',frame=view(1,1))],valid_actions=['RIGHT'])
    initial=dict(code="def predict(state, action):\n    return [[state[0][0]+1]]\nresult=execute_plan(['RIGHT','RIGHT'],predict)",
                 timeout_seconds=5,state=state(1,1),color_chars='0123456789ABCDEF')
    replies=[initial]+[dict(type='action_result',action_result=dict(executed=True),state=state(i,i)) for i in (2,3)]
    # Windows limits command lines far below Linux's per-argument ceiling.
    directory=ROOT/'test-artifacts'
    directory.mkdir(exist_ok=True)
    bootstrap=directory/('verified-sandbox-'+uuid4().hex+'.py')
    bootstrap.write_text(module['_SANDBOX_BOOTSTRAP'],encoding='utf-8')
    assert len(module['_SANDBOX_BOOTSTRAP'].encode()) < 120000
    result=subprocess.run([sys.executable,'-I','-S',str(bootstrap)],
        input=''.join(json.dumps(row)+'\n' for row in replies),text=True,capture_output=True,timeout=15)
    assert result.returncode==0,result.stderr
    rows=[json.loads(line) for line in result.stdout.splitlines()]
    assert sum(r['type']=='action' for r in rows)==2
    final=rows[-1]
    assert final['type']=='final',final
    assert final['result']['executed']==2
    assert 'HYDRA_VERIFY' in final['stdout'] and 'HYDRA_PLAN' in final['stdout']
    assert [r['event'] for r in final['hydra_verified_events']]==['verify','plan']
    assert final['hydra_verified_events'][-1]['report']['executed']==2


def test_extension_refuses_unknown_or_already_patched_sources():
    with pytest.raises(ValueError,match='layout'):
        patched_sources('unknown','unknown','')
    with pytest.raises(ValueError,match='already installed'):
        patched_sources('ARC_HYDRA_VERIFIED_PLANNING','unknown','')
