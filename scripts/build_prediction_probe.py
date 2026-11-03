"""Package a separate CPU-only host gate on the frozen flexible inspection base."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_verified_probe import build as base_build

ROOT = Path(__file__).resolve().parents[1]


def build():
    notebook, metadata, manifest = base_build(enforce_probes=False)
    files = {name:(ROOT/name).read_text(encoding='utf-8') for name in (
        'hydra/grid_inspection.py', 'scripts/install_inspection_agent.py',
        'hydra/prediction_ledger.py', 'hydra/prediction_host.py', 'hydra/prediction_tools.py',
        'scripts/install_prediction_agent.py', 'scripts/prediction_agent_probe.py')}
    source = notebook['cells'][1]['source']
    anchor = "sys.path.insert(0,str(bundle/'src/ARC3-Inference'))"
    hook = f'prediction_sources={files!r}\n'
    hook += '''inspection_extension={}
exec(prediction_sources['scripts/install_inspection_agent.py'],inspection_extension)
inspection_report=inspection_extension['install'](bundle,prediction_sources['hydra/grid_inspection.py'])
Path('/kaggle/working/hydra_inspection_extension.json').write_text(json.dumps(inspection_report,indent=2))
prediction_extension={}
exec(prediction_sources['scripts/install_prediction_agent.py'],prediction_extension)
prediction_report=prediction_extension['install'](bundle,{
    'tools':prediction_sources['hydra/prediction_tools.py'],
    'host':prediction_sources['hydra/prediction_host.py'],
    'ledger':prediction_sources['hydra/prediction_ledger.py']})
Path('/kaggle/working/hydra_prediction_extension.json').write_text(json.dumps(prediction_report,indent=2))
'''
    assert source.count(anchor) == 1
    source = source.replace(anchor, hook+anchor)
    run = "probe['run_probe'](enforce_probes=False)"
    assert source.count(run) == 1
    source = source.replace(run, "prediction_probe={}\nexec(prediction_sources['scripts/prediction_agent_probe.py'],prediction_probe)\nprediction_probe['run_probe'](probe)")
    compile(source, 'prediction-cpu-gate', 'exec')
    notebook['cells'][1]['source'] = source
    notebook['cells'][0]['source'] = ('# ARC3 host-owned prospective prediction gate\n\n'
        'Private offline CPU test of the original attributed Duck/M2 sandbox and host. '
        'No model inference, game solutions, GPU use or competition submission. '
        'Checks exact measurement, frozen timing, original action accounting, durable '
        'counterexamples through timeout/reset, actual host prompting and game isolation. '
        'Original attribution and third-party notices retained.')
    metadata.update(id='kunalsinghh25/arc-hydra-prediction-cpu-probe',
                    title='ARC Hydra Prediction CPU Probe')
    manifest['prediction_files'] = {name:sha256(value.encode()).hexdigest() for name,value in files.items()}
    return notebook, metadata, manifest


if __name__ == '__main__':
    notebook, metadata, manifest = build()
    output = ROOT/'notebooks/prediction_cpu_probe_v3'
    output.mkdir(exist_ok=True)
    for name, value in [('probe.ipynb',notebook), ('kernel-metadata.json',metadata), ('source-manifest.json',manifest)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('Created private offline CPU gate; no GPU, model or competition attachment')
