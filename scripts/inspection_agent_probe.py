"""Actual sandbox/host inspection integration without model inference."""
import json
import os
from pathlib import Path


def run_probe(base_probe):
    os.environ.setdefault('LOCAL_ANALYZER_MODEL_ID','synthetic-cpu-probe')
    mechanical=base_probe['run_probe'](enforce_probes=False)
    from inference.agent.python_tool_sandbox import run_sandboxed_python
    from inference.agent.runtime_state import Frame,HistoryEntry,write_runtime_state
    from inference.agent.tool_agent import ToolAgent
    old=dict(grid=[[11,11],[5,5]],ascii='YY\nBB',shape=[2,2],step=0,level=1)
    now=dict(grid=[[5,5,1,1,5,5],[8,8,11,8,11,11]],ascii='BBwwBB\nRRYRYY',shape=[2,6],step=1,level=1)
    state=dict(current_frame=now,history=[dict(action='',frame=old),dict(action='RIGHT',frame=now)],valid_actions=['RIGHT'])
    def forbidden(*args,**kwargs):raise AssertionError('Read-only inspection executed an action')
    def call(code):return run_sandboxed_python(code=code,timeout_seconds=5,initial_state=state,action_handler=forbidden)
    cases=[]
    result=call('result=read_cells([(0,1)],step=0)')
    assert not result['error'] and result['result']['cells'][0]['color']=='Y',result
    assert result['hydra_inspection_events'][0]['step']==0
    cases.append('actual_child_reads_historical_observation_and_exports_adoption')
    result=call('result=row_runs(0,cols=(1,6))')
    assert not result['error'] and result['result']['runs'][1]==dict(col_start=2,col_stop=4,color='w'),result
    assert result['result']['runs'][0]['col_start']==1
    cases.append('absolute_run_endpoints_are_exact_and_exclusive')
    result=call('result=read_region((0,2,1,6),stride=(1,2))')
    assert not result['error'] and result['result']['colors']==['BwB','RRY'],result
    assert result['result']['col_coordinates']==[1,3,5]
    cases.append('sampled_regions_retain_raw_coordinate_axes')
    result=call('result=read_cells([(0,0)],step=999)')
    assert 'not in supplied observation history' in result['error'],result
    cases.append('unobserved_step_is_rejected')
    result=call('result=read_cells([(-1,0)])')
    assert 'outside observed grid' in result['error'],result
    cases.append('negative_index_cannot_silently_wrap')
    root=Path('/kaggle/working/inspection-host-probe');root.mkdir(exist_ok=True)
    path=root/'first.runtime.json'
    frame=Frame(grid=tuple(tuple(row) for row in now['grid']),step=1,level=1)
    history=[HistoryEntry(action='',frame=Frame(grid=((11,11),(5,5)),step=0,level=1)),HistoryEntry(action='RIGHT',frame=frame)]
    write_runtime_state(path,current_frame=frame,history=history)
    agent=ToolAgent(model='local',provider='vllm',base_url='http://127.0.0.1:9/v1')
    agent._current_valid_actions=['RIGHT']
    result=agent._run_python_tool(path,dict(code='result=read_cells([(1,2)])'))
    payload=json.loads(result.content)
    assert 'error' not in payload and payload['result']['cells'][0]['color']=='Y',payload
    events=[json.loads(line) for line in path.with_suffix('.inspection.events.jsonl').read_text().splitlines()]
    assert len(events)==1 and events[0]['tool']=='read_cells'
    cases.append('actual_host_returns_values_and_persists_adoption_events')
    second=root/'second.runtime.json';write_runtime_state(second,current_frame=frame,history=[])
    result=agent._run_python_tool(second,dict(code='result=read_cells([(0,0)],step=0)'))
    assert 'not in supplied observation history' in json.loads(result.content).get('error','')
    assert not second.with_suffix('.inspection.events.jsonl').exists()
    cases.append('new_game_cannot_read_previous_game_steps')
    report=dict(passed=True,cases=cases,base_mechanical_cases=len(mechanical['cases']),prompt_combinations=16,
        boundary='Synthetic actual-host CPU checks only. Pixel values are observations, not certified object roles or rules. No model gameplay/score gain established.')
    Path('/kaggle/working/inspection-probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print('INSPECTION_CPU_PROBE_PASSED',json.dumps(report),flush=True)
    return report
