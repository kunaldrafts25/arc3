"""Compose bounded study memory/protocol onto the validated optional planner."""
import base64
from hashlib import sha256
import json
from pathlib import Path


def patched_sources(sandbox,agent,library,guidance):
    if 'ARC_HYDRA_STUDY_MEMORY' in sandbox:
        raise ValueError('Study memory already installed')
    anchors={
        'imports':'from inference.agent.python_tool_sandbox import run_sandboxed_python',
        'ensure':'    def _ensure_session(self, state_path: Path) -> None:\n',
        'state':'            return {\n                "current_frame": current_frame_payload,',
        'user':'        return _hydra_user_prompt\n\n    def _tools(',
        'system':'    return prompt + ',
        'telemetry':'        rendered_stdout = str(sandbox_result.get("stdout", "") or "")',
    }
    for name,anchor in anchors.items():
        if agent.count(anchor)!=1:raise ValueError('Unexpected study agent anchor: '+name)
    start='        _refresh_state(initial.get("state") or {})'
    results='                    "action_results": _json_safe(action_results),'
    host='                    "keepable_functions": list(message.get("keepable_functions") or []),'
    if sandbox.count(start)!=1 or sandbox.count(results)!=2 or sandbox.count(host)!=1:
        raise ValueError('Unexpected study sandbox layout')
    encoded=base64.b64encode(library.encode()).decode()
    hook=('        # ARC_HYDRA_STUDY_MEMORY\n'
          '        _hydra_study_api = {}\n'
          f'        exec(__import__("base64").b64decode("{encoded}"), _hydra_study_api)\n'
          '        _hydra_study_export = _hydra_study_api["install"](runtime_globals, (initial.get("state") or {}).get("hydra_study"))\n')
    sandbox=sandbox.replace(start,hook+start)
    sandbox=sandbox.replace(results,results+'\n                    "hydra_study": _json_safe(_hydra_study_export()) if "_hydra_study_export" in locals() else None,')
    sandbox=sandbox.replace(host,host+'\n                    "hydra_study": message.get("hydra_study"),')
    agent=agent.replace(anchors['imports'],anchors['imports']+'\nfrom inference.agent.hydra_study import load_store as _hydra_load_study, persist_store as _hydra_persist_study, render_panel as _hydra_study_panel')
    agent=agent.replace(anchors['ensure'],anchors['ensure']+'        self._hydra_study = _hydra_load_study(state_path.with_suffix(".study.json"))\n')
    agent=agent.replace(anchors['state'],'            return {\n                "hydra_study": self._hydra_study,\n                "current_frame": current_frame_payload,')
    agent=agent.replace(anchors['system'],'    return prompt + '+repr(guidance)+' + ',1)
    agent=agent.replace(anchors['user'],'        return _hydra_user_prompt + _hydra_study_panel(getattr(self, "_hydra_study", {}), current_level)\n\n    def _tools(')
    telemetry='''        if isinstance(sandbox_result.get("hydra_study"), dict):
            try:
                self._hydra_study = _hydra_persist_study(state_path.with_suffix(".study.json"), sandbox_result["hydra_study"])
            except (OSError, ValueError, TypeError, KeyError) as _hydra_memory_error:
                log.warning("Study memory persistence failed: %s", type(_hydra_memory_error).__name__)
                payload["study_memory_warning"] = type(_hydra_memory_error).__name__
'''
    agent=agent.replace(anchors['telemetry'],telemetry+anchors['telemetry'])
    compile(sandbox,'study-sandbox','exec');compile(agent,'study-agent','exec')
    return sandbox,agent


def install(bundle,library,guidance):
    directory=Path(bundle)/'src/ARC3-Inference/inference/agent'
    paths=[directory/'python_tool_sandbox.py',directory/'tool_agent.py']
    before=[p.read_text(encoding='utf-8') for p in paths]
    after=patched_sources(*before,library,guidance)
    compile(library,'study-memory','exec')
    for p,source in zip(paths,after):p.write_text(source,encoding='utf-8')
    (directory/'hydra_study.py').write_text(library,encoding='utf-8')
    report=dict(extension='general-study-v1',library_sha256=sha256(library.encode()).hexdigest(),
                guidance_sha256=sha256(guidance.encode()).hexdigest(),
                files={p.name:dict(before=sha256(a.encode()).hexdigest(),after=sha256(b.encode()).hexdigest()) for p,a,b in zip(paths,before,after)})
    print('ARC_HYDRA_STUDY_INSTALLED',json.dumps(report,sort_keys=True),flush=True)
    return report
