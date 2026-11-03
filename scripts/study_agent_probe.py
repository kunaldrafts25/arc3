"""Exercise composed memory RPC plus the real ToolAgent host, without an LLM."""
import json
import os
from pathlib import Path


def run_probe(base_probe):
    os.environ.setdefault('LOCAL_ANALYZER_MODEL_ID','synthetic-cpu-probe')
    from inference.agent import prompts
    from inference.agent.hydra_study import render_panel,load_store
    from inference.agent.python_tool_sandbox import run_sandboxed_python
    from inference.agent.tool_agent import ToolAgent
    from inference.agent.runtime_state import Frame,HistoryEntry,write_runtime_state
    prompts._hydra_study_panel=render_panel
    mechanical=base_probe['run_probe'](enforce_probes=False)

    def view(number,level=1):
        return dict(grid=[[number]],ascii=str(number),shape=[1,1],step=number,level=level)
    def call(code,memory=None,level=1):
        state=dict(current_frame=view(1,level),history=[dict(action='',frame=view(0,level)),
                   dict(action='RIGHT',frame=view(1,level))],valid_actions=['RIGHT'],hydra_study=memory)
        return run_sandboxed_python(code=code,timeout_seconds=5,initial_state=state,
                                    action_handler=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Unexpected action')))

    cases=[]
    result=call("remember('motion','RIGHT depends on active mode',kind='control',status='supported',evidence_steps=[0,1],scope='game')")
    assert not result['error'],result
    memory=result['hydra_study'];assert memory['notes']['motion']['evidence_steps']==[0,1]
    cases.append('real_sandbox_exports_evidence_note')
    result=call("result=recall()",memory)
    assert not result['error'] and result['result']==memory,result
    cases.append('real_sandbox_restores_next_call')
    result=call("remember('bad','unseen evidence',status='supported',evidence_steps=[999])",memory)
    assert 'Evidence step' in result['error'] and result['hydra_study']==memory,result
    cases.append('unseen_evidence_rejected_without_losing_memory')
    result=call("remember('large','x'*241)",memory)
    assert result['error'] and result['hydra_study']==memory,result
    cases.append('oversized_note_rejected')
    assert 'RECHECK' in render_panel(memory,2) and len(render_panel(memory,2))<=1800
    cases.append('prior_level_claim_is_not_silently_certified')
    result=call("result=recall()")
    assert result['result']['notes']=={},result
    cases.append('fresh_game_input_has_no_prior_notes')

    root=Path('/kaggle/working/study-host-probe');root.mkdir(exist_ok=True)
    state_path=root/'first.runtime.json'
    frame=Frame(step=1,level=1,grid=((1,),))
    history=[HistoryEntry(action='',frame=Frame(step=0,level=1,grid=((0,),))),
             HistoryEntry(action='RIGHT',frame=frame)]
    write_runtime_state(state_path,current_frame=frame,history=history)
    agent=ToolAgent(model='local',provider='vllm',base_url='http://127.0.0.1:9/v1')
    agent._current_valid_actions=['RIGHT']
    result=agent._run_python_tool(state_path,dict(code="remember('mode','Test selection before changing physics',kind='state',status='supported',evidence_steps=[0,1],scope='game')"))
    payload=json.loads(result.content);assert 'error' not in payload,payload
    assert load_store(state_path.with_suffix('.study.json'))['notes']['mode']['kind']=='state'
    cases.append('actual_host_persists_child_memory')
    agent._history_messages=[]
    other=ToolAgent(model='local',provider='vllm',base_url='http://127.0.0.1:9/v1')
    other._current_valid_actions=['RIGHT']
    result=other._run_python_tool(state_path,dict(code='result=recall()'))
    payload=json.loads(result.content);assert payload['result']['notes']['mode']['claim'].startswith('Test selection'),payload
    panel=other._build_user_prompt(1,valid_actions=['RIGHT'],current_frame=frame,history_entries=history)
    assert 'Test selection before changing physics' in panel and 'model-authored' in panel
    cases.append('actual_host_restarts_context_and_renders_memory')
    second=root/'second.runtime.json';write_runtime_state(second,current_frame=frame,history=history)
    result=other._run_python_tool(second,dict(code='result=recall()'))
    assert json.loads(result.content)['result']['notes']=={}
    cases.append('actual_host_same_directory_game_isolation')

    report=dict(passed=True,base_mechanical_cases=len(mechanical['cases']),
                prompt_combinations=16,study_cases=cases,
                boundary='Synthetic CPU tests of real sandbox/host and prompt paths. No model inference, ARC gameplay or score gain established.')
    Path('/kaggle/working/study-probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print('STUDY_CPU_PROBE_PASSED',json.dumps(report),flush=True)
    return report
