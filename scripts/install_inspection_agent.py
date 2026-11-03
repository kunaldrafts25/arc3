"""Install exact observation helpers onto the flexible optional-planning agent."""
import base64
from hashlib import sha256
import json
from pathlib import Path

GUIDANCE='''

Exact observation inspection (optional Python helpers):
- read_cells([(row,col), ...], step=None) reads up to 64 pixels.
- read_region((row_start,row_stop,col_start,col_stop), stride=(1,1), step=None)
  returns up to 256 sampled letter-coded pixels with their raw coordinates.
  For a supported 4-pixel cell layout, e.g. bounds (2,64,2,64), stride (4,4)
  samples cell centers; the cell size and origin remain your hypotheses.
- row_runs(row, cols=None, step=None) returns maximal same-color runs with
  col_start inclusive and col_stop exclusive, using absolute raw columns.
All coordinates are zero-based row,col; rectangle stops are exclusive.
step=None means current observation; an explicit step must already be observed.
You can also pass frame=current_frame or an observed history entry's frame.
These tools measure pixels, not actor identity, mechanics or goals. Use them
to check uncertain positions/coordinate conversions before committing actions.
Existing segmentation, frame_diff, history and ordinary action batches remain.
'''


def patched_sources(sandbox,agent,library):
    if 'ARC_HYDRA_GRID_INSPECTION' in sandbox:raise ValueError('Inspection already installed')
    anchors=dict(start='        _refresh_state(initial.get("state") or {})',
        result='                    "action_results": _json_safe(action_results),',
        host='                    "keepable_functions": list(message.get("keepable_functions") or []),',
        prompt='    return prompt + ',
        telemetry='        rendered_stdout = str(sandbox_result.get("stdout", "") or "")')
    for name,count,source in [('start',1,sandbox),('result',2,sandbox),('host',1,sandbox),('prompt',1,agent),('telemetry',1,agent)]:
        if source.count(anchors[name])!=count:raise ValueError('Unexpected inspection anchor: '+name)
    encoded=base64.b64encode(library.encode()).decode()
    hook=('        # ARC_HYDRA_GRID_INSPECTION\n        _hydra_inspection_api = {}\n'
          f'        exec(__import__("base64").b64decode("{encoded}"), _hydra_inspection_api)\n'
          '        _hydra_inspection_events = _hydra_inspection_api["install"](runtime_globals)\n')
    sandbox=sandbox.replace(anchors['start'],hook+anchors['start'])
    sandbox=sandbox.replace(anchors['result'],anchors['result']+'\n                    "hydra_inspection_events": _json_safe(_hydra_inspection_events) if "_hydra_inspection_events" in locals() else [],')
    sandbox=sandbox.replace(anchors['host'],anchors['host']+'\n                    "hydra_inspection_events": list(message.get("hydra_inspection_events") or []),')
    agent=agent.replace(anchors['prompt'],anchors['prompt']+repr(GUIDANCE)+' + ',1)
    telemetry='''
        _hydra_inspections = sandbox_result.get("hydra_inspection_events") or []
        if _hydra_inspections:
            try:
                with state_path.with_suffix(".inspection.events.jsonl").open("a", encoding="utf-8") as _hydra_inspection_log:
                    for _hydra_inspection in _hydra_inspections:
                        _hydra_inspection_log.write(json.dumps(_hydra_inspection, sort_keys=True) + "\\n")
            except OSError as exc:
                log.warning("Inspection evidence persistence failed: %s", type(exc).__name__)
'''
    agent=agent.replace(anchors['telemetry'],anchors['telemetry']+telemetry)
    compile(library,'grid-inspection','exec');compile(sandbox,'inspection-sandbox','exec');compile(agent,'inspection-agent','exec')
    return sandbox,agent


def install(bundle,library):
    directory=Path(bundle)/'src/ARC3-Inference/inference/agent'
    paths=[directory/'python_tool_sandbox.py',directory/'tool_agent.py']
    before=[p.read_text(encoding='utf-8') for p in paths]
    after=patched_sources(*before,library)
    for p,source in zip(paths,after):p.write_text(source,encoding='utf-8')
    report=dict(extension='grid-inspection-v1',library_sha256=sha256(library.encode()).hexdigest(),
        guidance_sha256=sha256(GUIDANCE.encode()).hexdigest(),
        files={p.name:dict(before=sha256(a.encode()).hexdigest(),after=sha256(b.encode()).hexdigest()) for p,a,b in zip(paths,before,after)})
    print('ARC_HYDRA_INSPECTION_INSTALLED',json.dumps(report,sort_keys=True),flush=True)
    return report
