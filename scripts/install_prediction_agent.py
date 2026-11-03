"""Install host-owned frozen forecasts onto the flexible inspection candidate."""
import base64
from hashlib import sha256
import json
from pathlib import Path

GUIDANCE = '''

Optional competing predictions, for decision-relevant uncertainty:
prediction_start(['h1','h2'], {'p':['cell',row,col], 'b':['bbox','R']}, question='...')
declares level-scoped hypothesis versions and exact raw-pixel measurements.
Features: ['cell',row,col], ['count',color], ['bbox',color]; count/bbox optionally
append row_start,row_stop,col_start,col_stop. Stops are exclusive; bbox is
[row_start,row_stop,col_start,col_stop] or None, not a certified object identity.
prediction_forecast({'probe':{'action':{'action':'RIGHT'},'predictions':
{'h1':{'p':'R'},'h2':{'p':'B'}}}}) freezes forecasts BEFORE any action.
Then use ordinary action(...). The host checks only the next matching SINGLE
action against actual pixels; prediction_status() returns outcomes/counterexamples.
None means an unknown hypothesis prediction; omitted features are unpredicted.
prediction_discard() cancels a pending forecast. A different action/batch cancels
it automatically. These helpers never act. Ordinary batches remain available.
Evidence survives tool/context resets. A new level/reset requires prediction_start
and new checks. A mismatch can indicate perception, mode/history or rule error;
matching motion without completion can indicate a wrong goal or prerequisite.
Use two useful alternatives only when they can change a decision; otherwise act.
Zero disagreement calls for useful exploration/setup, not stopping play.
'''


def replace_once(source, anchor, replacement, name):
    if source.count(anchor) != 1:
        raise ValueError('Unexpected prediction anchor: '+name)
    return source.replace(anchor, replacement, 1)


def patched_sources(sandbox, agent, tools):
    if 'ARC_HYDRA_PREDICTION_RPC' in sandbox:
        raise ValueError('Prediction already installed')
    if 'ARC_HYDRA_GRID_INSPECTION' not in sandbox:
        raise ValueError('Install tested flexible inspection base first')
    start = '        _refresh_state(initial.get("state") or {})'
    encoded = base64.b64encode(tools.encode()).decode()
    hook = ('        # ARC_HYDRA_PREDICTION_RPC\n'
            '        _hydra_prediction_tools = {}\n'
            f'        exec(__import__("base64").b64decode("{encoded}"), _hydra_prediction_tools)\n'
            '        _hydra_prediction_tools["install"](runtime_globals, _send, _recv)\n')
    sandbox = replace_once(sandbox, start, hook+start, 'child install')
    anchor = '    animation_handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None,'
    sandbox = replace_once(sandbox, anchor, anchor+'\n    prediction_handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None,', 'handler argument')
    anchor = '            if msg_type == "animation":'
    rpc = '''            if msg_type == "hydra_prediction":
                try:
                    if prediction_handler is None:
                        raise ValueError("Prediction host unavailable")
                    result = prediction_handler(message.get("request"))
                    response = {"type": "hydra_prediction_result", "result": result}
                except (ValueError, TypeError, KeyError) as exc:
                    response = {"type": "hydra_prediction_error", "error": str(exc)}
                _send_json_line(process.stdin, response)
                continue
'''
    sandbox = replace_once(sandbox, anchor, rpc+anchor, 'RPC dispatch')
    anchor = 'from inference.agent.python_tool_sandbox import run_sandboxed_python'
    agent = replace_once(agent, anchor, anchor+'\nfrom inference.agent.hydra_prediction_host import PredictionSession as _HydraPredictionSession, render_panel as _hydra_prediction_panel', 'host imports')
    anchor = '        sandbox_result = run_sandboxed_python('
    agent = replace_once(agent, anchor, '        _hydra_prediction = _HydraPredictionSession(state_path.with_suffix(".prediction.json"), _serialized_runtime_state)\n'+anchor, 'session')
    agent = replace_once(agent, '            action_handler=_handle_action,',
                         '            action_handler=_hydra_prediction.wrap_action(_handle_action),\n            prediction_handler=_hydra_prediction.rpc,', 'action wrapper')
    anchor = '    return prompt + '
    agent = replace_once(agent, anchor, anchor+repr(GUIDANCE)+' + ', 'system guidance')
    anchor = '    def _ensure_session(self, state_path: Path) -> None:\n'
    agent = replace_once(agent, anchor, anchor+'        self._hydra_prediction_state_path = state_path.with_suffix(".prediction.json")\n', 'prompt path')
    anchor = '        return _hydra_user_prompt\n\n    def _tools('
    replacement = '''        _hydra_prediction_path = getattr(self, "_hydra_prediction_state_path", None)
        if _hydra_prediction_path is not None:
            _hydra_user_prompt += _hydra_prediction_panel(_hydra_prediction_path, current_level)
        return _hydra_user_prompt

    def _tools('''
    agent = replace_once(agent, anchor, replacement, 'user feedback')
    compile(sandbox, 'prediction-sandbox', 'exec')
    compile(agent, 'prediction-agent', 'exec')
    return sandbox, agent


def install(bundle, libraries):
    directory = Path(bundle)/'src/ARC3-Inference/inference/agent'
    paths = [directory/'python_tool_sandbox.py', directory/'tool_agent.py']
    before = [p.read_text(encoding='utf-8') for p in paths]
    after = patched_sources(*before, libraries['tools'])
    for name, source in libraries.items():
        compile(source, 'prediction-'+name, 'exec')
    for p, source in zip(paths, after):
        p.write_text(source, encoding='utf-8')
    (directory/'hydra_prediction_host.py').write_text(libraries['host'], encoding='utf-8')
    (directory/'hydra_prediction_ledger.py').write_text(libraries['ledger'], encoding='utf-8')
    report = dict(extension='prediction-host-v2', action_gating=False,
                  libraries={k:sha256(v.encode()).hexdigest() for k,v in libraries.items()},
                  guidance_sha256=sha256(GUIDANCE.encode()).hexdigest(),
                  files={p.name:dict(before=sha256(a.encode()).hexdigest(), after=sha256(b.encode()).hexdigest())
                         for p,a,b in zip(paths,before,after)})
    print('ARC_HYDRA_PREDICTION_INSTALLED', json.dumps(report, sort_keys=True), flush=True)
    return report
