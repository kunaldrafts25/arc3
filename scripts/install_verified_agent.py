"""Apply the declared verified-planning extension to a writable Duck source copy."""
import base64
from hashlib import sha256
import json
from pathlib import Path


GUIDANCE='''

Evidence-driven planning tools:
- Ordinary action(...) permits ONE exploratory action per Python tool call.
  Unverified batches and repeated exploratory actions in the same call are refused.
- For a planned sequence, define predict(state, action_dict), then call
  execute_plan(actions, predict, encode=None, max_steps=12, max_checks=512).
  Actions are dictionaries such as {'action':'UP'} or {'action':'MOUSE','row':3,'col':8}.
- By default state is a copied JSON-style grid (list of rows of integer colors).
  Optional encode(grid) extracts a JSON-style abstract state; predict receives that
  encoded state and must return the next encoded state. None means unknown.
- verify_model(predict, encode=None, max_checks=512) replays recorded, non-reset
  transitions in the current level. It reports coverage and the first counterexample.
  Zero coverage, abstentions, truncated checks, errors and constant abstractions
  cannot certify a plan. Abstract-state checks do not prove full-grid accuracy.
- execute_plan verifies first, checks each next prediction, and stops its own batch
  on unknown predictions, mismatch, host refusal or a level/game boundary. Inspect
  its returned stop_reason and counterexample; do not continue an invalid plan.
- Predict/encode functions must be pure: they cannot call action or execute_plan.
  They should use only their inputs, not historical target observations.
- Without a supported model, take one cheap discriminating probe. Revise mechanics
  using evidence. Track uncertain win conditions separately; replay consistency
  alone cannot establish a goal. Existing frame/animation tools remain available.
'''

PROMPT_REPLACEMENTS=(
    ('- A strong default loop is: summarize the board, infer the desired environment change, write a small scorer or search over candidate sequences, execute the best probe or plan with `action(...)`, then inspect again until you understand exactly what changed.\n',
     '- Inspect the board, maintain falsifiable mechanics and goal hypotheses, choose one informative probe or a replay-supported plan, execute it with the matching tool, then compare observations.\n'),
    ('- Call `action(actions)` to execute one or more real environment actions from Python.\n',
     '- Call `action(actions)` for one exploratory action; use `execute_plan` for checked sequences.\n'),
    ('- `action(...)` accepts an ordered list of one or more actions. Once your code has selected a reliable sequence, it is often useful to batch it.\n',
     '- Execute planned sequences with `execute_plan(actions, predict, encode=None)`.\n'),
    ('- You can also call `action(...)` multiple times in one Python snippet, including inside loops. Each call updates the preloaded variables before execution continues.\n',
     '- One exploratory `action(...)` call is allowed per snippet; checked plans refresh state after every action.\n'),
)

USER_PROMPT_REPLACEMENTS=(
    ('When ready, call `action(actions)` from inside the `python` tool with the best valid action or ordered batch selected by your code. If your code has found a reliable short sequence, prefer batching it in one call.',
     'When ready, take one exploratory action with `action(actions)`, or execute a replay-supported sequence with `execute_plan(actions, predict, encode=None)`.'),
    ('You may call `action(actions)` more than once in one Python snippet if your search or control loop needs it.',
     'One exploratory action is allowed per Python snippet; use `execute_plan` for checked sequences.'),
    ('You may call `action(actions)` more than once in one Python snippet if your search or control loop needs it, ',
     'Use `execute_plan` for checked sequences, '),
    ('When your evidence supports a choice, call `action(actions)` with the sequence it supports. Probe with a single action when you genuinely need to distinguish two possibilities; otherwise batch the route you have.',
     'When evidence supports a sequence, use `execute_plan` to verify and execute it. Otherwise take one informative exploratory action.'),
)

ASSIST_GUIDANCE='''

Optional prediction-checking tools:
- Ordinary action(...) retains its original batching, repeated calls and host
  guards. You do not need a simulator before exploring or executing a route.
- When a compact mechanics model is useful, verify_model(predict, encode=None,
  max_checks=512) checks recorded non-reset transitions in the current level.
  Default state is a copied JSON-style numeric grid. Optional encode(grid)
  returns a JSON-style abstract state; predict(state, action_dict) returns its
  next state, or None for unknown. Models and encoders must be pure.
- execute_plan(actions, predict, encode=None, max_steps=12, max_checks=512)
  replays history, then predicts and checks each executed action. max_steps is
  an integer from 1 to 16. It stops on contradictions, unknown predictions,
  no gameplay change, host refusal, or terminal/level boundaries.
- A failed replay means the checked plan is unavailable, not that you must stop
  playing. Use ordinary action(...) to investigate and revise the model. Do not
  keep repairing an expensive simulator when direct inspection and actions suffice.
- No coverage, abstentions, truncated checks, contradictions, errors or constant
  abstractions cannot certify a plan. Abstract agreement is not full-grid accuracy
  or proof of the goal. Track uncertain win conditions separately.
- Snippet variables do not persist. Put constants inside retained predict/encode
  functions, use literal defaults, or pass data explicitly; avoid unretained globals.
'''


def patched_sources(sandbox, agent, library, enforce_probes=True):
    if 'ARC_HYDRA_VERIFIED_PLANNING' in sandbox:
        raise ValueError('Verified extension already installed; require fresh source copy')
    anchor='        _refresh_state(initial.get("state") or {})'
    prompt_anchor='    return prompt\n\n\n@dataclass(frozen=True)\nclass AnalyzerModelConfig:'
    result_anchor='                    "action_results": _json_safe(action_results),'
    host_anchor='                    "keepable_functions": list(message.get("keepable_functions") or []),'
    telemetry_anchor='        rendered_stdout = str(sandbox_result.get("stdout", "") or "")'
    user_anchor='        return "\\n".join(lines)\n\n    def _tools('
    if (sandbox.count(anchor)!=1 or agent.count(prompt_anchor)!=1
            or sandbox.count(result_anchor)!=2 or sandbox.count(host_anchor)!=1
            or agent.count(telemetry_anchor)!=1 or agent.count(user_anchor)!=1):
        raise ValueError('Unexpected Duck source layout; refusing an unverified patch')
    payload=base64.b64encode(library.encode()).decode()
    addition=('        # ARC_HYDRA_VERIFIED_PLANNING\n'
              '        _hydra_api = {}\n'
              f'        exec(__import__("base64").b64decode("{payload}"), _hydra_api)\n'
              f'        _hydra_events = _hydra_api["install"](runtime_globals, _normalize_actions, enforce_probes={enforce_probes!r})\n')
    sandbox=sandbox.replace(anchor,addition+anchor)
    sandbox=sandbox.replace(result_anchor,result_anchor+'\n                    "hydra_verified_events": _json_safe(_hydra_events),')
    sandbox=sandbox.replace(host_anchor,host_anchor+'\n                    "hydra_verified_events": list(message.get("hydra_verified_events") or []),')
    prompt_code='\n'.join('    prompt = prompt.replace('+repr(a)+', '+repr(b)+')' for a,b in PROMPT_REPLACEMENTS) if enforce_probes else ''
    agent=agent.replace(prompt_anchor,prompt_code+'\n    return prompt + '+repr(GUIDANCE if enforce_probes else ASSIST_GUIDANCE)
                        +'\n\n\n@dataclass(frozen=True)\nclass AnalyzerModelConfig:')
    user_code='        _hydra_user_prompt = "\\n".join(lines)\n'
    if enforce_probes:
        user_code+='\n'.join('        _hydra_user_prompt = _hydra_user_prompt.replace('+repr(a)+', '+repr(b)+')'
                              for a,b in USER_PROMPT_REPLACEMENTS)
    else:
        user_code+='        _hydra_user_prompt += "\\nOptional: use verify_model/execute_plan for a useful compact model; ordinary action batching remains available."'
    agent=agent.replace(user_anchor,user_code+'\n        return _hydra_user_prompt\n\n    def _tools(')
    telemetry='''
        # Mechanical helper events, separate from model-authored stdout.
        _hydra_events = sandbox_result.get("hydra_verified_events") or []
        if _hydra_events:
            try:
                with state_path.with_suffix(".hydra-events.jsonl").open("a", encoding="utf-8") as _hydra_log:
                    for _hydra_event in _hydra_events:
                        _hydra_log.write(json.dumps(_hydra_event, sort_keys=True) + "\\n")
            except OSError as _hydra_error:
                log.warning("Could not persist verification events: %s", type(_hydra_error).__name__)
'''
    agent=agent.replace(telemetry_anchor,telemetry_anchor+'\n'+telemetry)
    compile(sandbox,'verified-python-sandbox','exec')
    compile(agent,'verified-tool-agent','exec')
    return sandbox, agent


def install(bundle, library, enforce_probes=True):
    directory=Path(bundle)/'src/ARC3-Inference/inference/agent'
    paths=[directory/'python_tool_sandbox.py', directory/'tool_agent.py']
    before=[p.read_text(encoding='utf-8') for p in paths]
    after=patched_sources(*before,library,enforce_probes=enforce_probes)
    # Validate both files before changing either. The source copy is notebook-local.
    for path, source in zip(paths,after):
        path.write_text(source,encoding='utf-8')
    report=dict(extension='verified-planning-v2' if enforce_probes else 'planning-assist-v1',
                enforce_probes=enforce_probes,library_sha256=sha256(library.encode()).hexdigest(),
                files={p.name:dict(before=sha256(a.encode()).hexdigest(),after=sha256(b.encode()).hexdigest())
                       for p,a,b in zip(paths,before,after)})
    print('ARC_HYDRA_VERIFIED_PLANNING_INSTALLED',json.dumps(report,sort_keys=True),flush=True)
    return report
