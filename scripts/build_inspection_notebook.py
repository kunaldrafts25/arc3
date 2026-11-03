"""Package an isolated coordinate-inspection experiment on the flexible agent."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_ultimate_notebook import package as flexible_package

ROOT=Path(__file__).resolve().parents[1]


def package(wall_seconds=32400):
    gate=ROOT/'reports/kaggle/inspection-cpu-probe-v1'
    report=json.loads((gate/'inspection-probe.json').read_text(encoding='utf-8'))
    if not report['passed'] or len(report['cases'])!=7:raise ValueError('Inspection CPU gate has not passed')
    upload=json.loads((gate/'upload.json').read_text(encoding='utf-8'));cpu=ROOT/'notebooks/inspection_cpu_probe'
    for name,expected in upload['files'].items():
        if sha256((cpu/name).read_bytes()).hexdigest()!=expected:raise ValueError('CPU upload changed: '+name)
    manifest=json.loads((cpu/'source-manifest.json').read_text(encoding='utf-8'))
    for group in ('files','inspection_files'):
        for name,expected in manifest[group].items():
            if sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise ValueError('CPU-tested source changed: '+name)
    notebook,metadata,provenance=flexible_package('benchmark',public_runtime_seconds=wall_seconds-600,notebook_budget_seconds=wall_seconds)
    installer=(ROOT/'scripts/install_inspection_agent.py').read_text(encoding='utf-8')
    library=(ROOT/'hydra/grid_inspection.py').read_text(encoding='utf-8')
    expected=json.loads((gate/'hydra_inspection_extension.json').read_text(encoding='utf-8'))
    base=json.loads((gate/'hydra_extension.json').read_text(encoding='utf-8'))
    setup=next(c for c in notebook['cells'] if c['source'].startswith('# Each bundled repo exposes'))
    setup['source']+=f'\nassert _hydra_extension_report == {base!r}, "Base differs from inspection gate"\n'
    setup['source']+=f'_hydra_inspection_ns={{}}\nexec({installer!r},_hydra_inspection_ns)\n'
    setup['source']+=f'_hydra_inspection_report=_hydra_inspection_ns["install"](BUNDLE_DIR,{library!r})\n'
    setup['source']+=f'assert _hydra_inspection_report == {expected!r}, "Inspection differs from completed CPU gate"\n'
    setup['source']+='(WORKING_DIR/"hydra_inspection_extension.json").write_text(json.dumps(_hydra_inspection_report,indent=2))\n'
    provenance.update(candidate='inspection-candidate',inspection_cpu_gate=upload['kernel'],inspection_extension=expected,
        inspection_source_manifest=manifest['inspection_files'],
        experiment='Flexible agent plus exact coordinate inspection; no study-memory/recovery additions.',
        promotion_status='CPU-gated; not launched, no gameplay improvement established')
    setup['source']+=f'(WORKING_DIR/"hydra_inspection_provenance.json").write_text(json.dumps({provenance!r},indent=2))\n'
    compile(setup['source'],'inspection-notebook-setup','exec')
    metadata.update(id='kunalsinghh25/arc-hydra-inspection-candidate',title='ARC Hydra Exact Inspection Candidate')
    notebook['cells'][0]['source']=(
        '# ARC-Hydra Exact Inspection Candidate\n\n'
        'Experimental optional exact-cell, sampled-region and same-color row-run tools. '
        'Coordinates remain raw zero-based row,col, with exclusive rectangle/run stops. '
        'Historical lookup only uses supplied observations, with unknown/ambiguous steps rejected. '
        'Tools do not infer object roles, mechanics or goals, or execute environment actions. '
        'Usage events distinguish actual adoption from score changes.\n\n'
        'Based on the preserved 48.29 flexible optional-planning agent. '
        'No added study-memory/recovery protocol and no weight training. '
        f'All 25 public games share a {wall_seconds}-second whole-notebook budget '
        'including startup and a 600-second finalization reserve. No two-hour cap. '
        'Original model/draft/runtime/scheduler and attribution retained. '
        'CPU gate passed seven inspection cases, eight mechanical cases and 16 prompt combinations. '
        'GPU gameplay has not been run; no score improvement is claimed.')
    return notebook,metadata,provenance


if __name__=='__main__':
    notebook,metadata,provenance=package();output=ROOT/'notebooks/inspection_candidate';output.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(kernel=metadata['id'],wall_seconds=32400,launched=False)))
