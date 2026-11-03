"""CPU/Linux smoke tests against the actual installed sandbox RPC runner."""
import json
import ast
import __future__
from itertools import product
import os
from pathlib import Path
from types import SimpleNamespace


def check_user_prompts(agent_source,enforce_probes=True):
    """Render the real per-turn method across memory/batching/opener branches."""
    from inference.agent import prompts
    methods=[node for node in ast.walk(ast.parse(agent_source))
             if isinstance(node,ast.FunctionDef) and node.name=='_build_user_prompt']
    assert len(methods)==1, 'Unexpected user-prompt builder layout'
    namespace=dict(vars(prompts))
    false=lambda *args,**kwargs:False
    namespace.update(_WM_NUDGE_TURNS=0,_wm_revise_nudges_enabled=false,
        _get_env_bool=false,_normalize_valid_actions=lambda actions:actions,
        _format_valid_action_line=lambda actions:', '.join(actions))
    exec(compile(ast.Module(body=methods,type_ignores=[]),'installed-user-prompt','exec',
                 flags=__future__.annotations.compiler_flag),namespace)
    instance=SimpleNamespace(_pending_wm_rebuild_reason='',
        _prepare_auto_diff=lambda *args:[],_death_ledger_observe=lambda *args:None,
        _summarized_knowledge_lines=lambda:[],_memory_section_guidance=lambda *args:[])
    rendered=[]
    for memory_off,dedupe,opener,action_num in product((False,True),repeat=4):
        namespace.update(_memory_sections_disabled=lambda:memory_off,
                         _dedupe_multicall_line=lambda:dedupe,
                         _opener_commit_hint=lambda:opener)
        text=namespace['_build_user_prompt'](instance,int(action_num),valid_actions=['MOUSE'])
        if not enforce_probes:
            assert 'prefer batching it in one call' in text
            assert 'more than once in one Python snippet' in text
            assert 'ordinary action batching remains available' in text
            rendered.append(text)
            continue
        for forbidden in ('more than once in one Python snippet','prefer batching it',
                          'otherwise batch the route','best valid action or ordered batch'):
            assert forbidden not in text, (forbidden,memory_off,dedupe,opener,action_num)
        assert 'One exploratory action is allowed' in text
        assert 'execute_plan(actions, predict, encode=None)' in text
        rendered.append(text)
    return rendered


def check_prompt(agent_source,enforce_probes=True):
    from inference.agent import prompts
    function=next(n for n in ast.parse(agent_source).body if isinstance(n,ast.FunctionDef) and n.name=='_build_system_prompt')
    namespace=dict(vars(prompts))
    false=lambda *args,**kwargs:False
    namespace.update(os=os,_AUTO_FRAME_DIFF=False,_DIFF_IMAGE=False,
        _explain_gameplay_changed=false,_animation_enabled=false,current_grid_image_enabled=false,
        _get_env_bool=false,_persistent_functions=false,_memory_sections_disabled=lambda:True,
        _prefer_tool_calls=false,_level_transfer_guidance_enabled=false)
    exec(compile(ast.Module(body=[function],type_ignores=[]),'installed-prompt','exec'),namespace)
    prompt=namespace['_build_system_prompt'](tool_output_tokens=3072)
    if not enforce_probes:
        assert 'Optional prediction-checking tools:' in prompt
        assert 'Ordinary action(...) retains its original batching' in prompt
        assert 'Unverified batches and repeated exploratory actions in the same call are refused' not in prompt
        check_user_prompts(agent_source,enforce_probes=False)
        return prompt
    assert 'You can also call `action(...)` multiple times' not in prompt
    assert 'Call `action(actions)` to execute one or more' not in prompt
    assert 'execute_plan(actions, predict' in prompt
    assert 'One exploratory `action(...)` call' in prompt
    check_user_prompts(agent_source)
    return prompt


def run_probe(enforce_probes=True):
    from inference.agent.python_tool_sandbox import run_sandboxed_python

    increment="def predict(state, action):\n    return [[state[0][0]+1]]\n"
    cases=[
        dict(name='consistent_plan',code=increment+"result=execute_plan(['RIGHT','RIGHT'],predict)",spent=2,reason='complete'),
        dict(name='retrospective_counterexample',code="def predict(state,action):\n    return [[99]]\nresult=execute_plan(['RIGHT','RIGHT'],predict)",spent=0,reason='unverified_model'),
        dict(name='prospective_counterexample',code=increment+"result=execute_plan(['RIGHT','RIGHT'],predict)",surprise=True,spent=1,reason='prediction_mismatch'),
        dict(name='zero_coverage',code=increment+"result=execute_plan(['RIGHT'],predict)",empty=True,spent=0,reason='unverified_model'),
        dict(name='constant_abstraction',code="def predict(state,action):\n    return 0\ndef encode(grid):\n    return 0\nresult=execute_plan(['RIGHT'],predict,encode)",spent=0,reason='unverified_model'),
        dict(name='impure_prediction',code="def predict(state,action_dict):\n    action('RIGHT')\n    return [[1]]\nresult=execute_plan(['RIGHT'],predict)",spent=0,reason='unverified_model'),
        dict(name='one_exploratory_action',code="action('RIGHT')\naction('RIGHT')",spent=1,error=True),
    ]
    if not enforce_probes:
        cases[-1]=dict(name='ordinary_repeated_actions_preserved',code="action('RIGHT')\naction('RIGHT')",spent=2,ordinary=True)
        cases.append(dict(name='ordinary_batch_preserved',code="action(['RIGHT','RIGHT'])",spent=2,ordinary=True))
    reports=[]
    for case in cases:
        value=1
        calls=[]
        def view(number):
            return dict(grid=[[number]],ascii=str(number),shape=[1,1],step=number,level=1)
        history=[dict(action='',frame=view(0)),dict(action='RIGHT',frame=view(1))]
        def state():
            return dict(current_frame=view(value),history=list(history) if not case.get('empty') else [],valid_actions=['RIGHT'])
        def handler(actions,**kwargs):
            nonlocal value
            if enforce_probes:
                assert len(actions)==1
            calls.extend(actions)
            for command in actions:
                value=7 if case.get('surprise') else value+1
                history.append(dict(action='RIGHT',frame=view(value)))
            return dict(action_result=dict(executed=True,gameplay_changed=True),state=state())
        result=run_sandboxed_python(code=case['code'],timeout_seconds=5,
            initial_state=state(),action_handler=handler)
        assert len(calls)==case['spent'],(case['name'],result,calls)
        if case.get('error'):
            assert 'One exploratory' in result['error'],result
        elif not case.get('ordinary'):
            assert not result['error'],result
            assert result['result']['stop_reason']==case['reason'],result
        else:
            assert not result['error'],result
        events=result.get('hydra_verified_events')
        if not case.get('ordinary'):
            assert events,(case['name'],'missing mechanical event propagation')
        reports.append(dict(name=case['name'],passed=True,actual_actions=len(calls),events=events))
    from inference.agent import python_tool_sandbox
    agent_file=Path(python_tool_sandbox.__file__).with_name('tool_agent.py')
    check_prompt(agent_file.read_text(encoding='utf-8'),enforce_probes=enforce_probes)
    output=dict(passed=True,cases=reports,prompt_contract_consistent=True,
        enforce_probes=enforce_probes,
        prompt_contract_scope='System prompt plus 16 rendered user-prompt combinations: memory on/off, duplicate guidance on/off, opener hint on/off, initial/resumed turn. Not exhaustive configuration coverage.',
        boundary='Synthetic CPU integration checks of installed sandbox and prompt contract; no model inference, gateway or ARC gameplay tested')
    Path('/kaggle/working/verified-probe.json').write_text(json.dumps(output,indent=2)+'\n')
    print('VERIFIED_AGENT_CPU_PROBE_PASSED',json.dumps(dict(cases=len(reports))),flush=True)
    return output
