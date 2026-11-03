"""Real host/prompt integration checks for the advisory recovery extension."""
import json
from pathlib import Path


def run_probe():
    from inference.agent.tool_agent import ToolAgent
    from inference.agent.runtime_state import Frame,HistoryEntry,write_runtime_state
    root=Path('/kaggle/working/recovery-host-probe');root.mkdir(exist_ok=True)
    history=[HistoryEntry(action='RIGHT',frame=Frame(grid=((i%2,),),step=i,level=1)) for i in range(71)]
    frame=history[-1].frame
    first=root/'first.runtime.json'
    write_runtime_state(first,current_frame=frame,history=history)
    agent=ToolAgent(model='local',provider='vllm',base_url='http://127.0.0.1:9/v1')
    agent._ensure_session(first)
    panel=agent._build_user_prompt(70,current_frame=frame,history_entries=history,valid_actions=['RIGHT'])
    assert 'Recovery check: 70 recorded transitions' in panel and 'do not prove failure' in panel
    assert 'Ordinary actions remain available' in panel
    evidence=first.with_suffix('.recovery.events.jsonl')
    rows=[json.loads(line) for line in evidence.read_text().splitlines()]
    assert len(rows)==1 and rows[0]['repeated_visible_transitions']
    cases=['actual_host_renders_and_records_cross_turn_recovery_evidence']
    agent._ensure_session(first)
    again=agent._build_user_prompt(70,current_frame=frame,history_entries=history,valid_actions=['RIGHT'])
    assert 'Recovery check:' not in again and len(evidence.read_text().splitlines())==1
    cases.append('same_step_repeated_analysis_does_not_spam_recovery')
    next_frame=Frame(grid=((9,),),step=71,level=2)
    panel=agent._build_user_prompt(71,current_frame=next_frame,history_entries=history+[HistoryEntry(action='RIGHT',frame=next_frame)],valid_actions=['RIGHT'])
    assert 'Recovery check:' not in panel
    cases.append('actual_level_boundary_clears_recovery_streak')
    second=root/'second.runtime.json';write_runtime_state(second,current_frame=frame,history=history)
    agent._ensure_session(second)
    panel=agent._build_user_prompt(70,current_frame=frame,history_entries=history,valid_actions=['RIGHT'])
    assert 'Recovery check:' in panel and second.with_suffix('.recovery.events.jsonl').is_file()
    assert len(evidence.read_text().splitlines())==1
    cases.append('same_parent_new_game_has_independent_recovery_evidence')
    report=dict(passed=True,cases=cases,action_gating=False,
        boundary='Synthetic actual-host CPU integration only. No LLM gameplay or score improvement established.')
    Path('/kaggle/working/recovery-probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RECOVERY_CPU_PROBE_PASSED',json.dumps(report),flush=True)
    return report
