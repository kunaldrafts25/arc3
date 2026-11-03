"""Stage a CPU gate for composing existing study memory with prediction tools."""
from hashlib import sha256
import json
from pathlib import Path

from hydra.research_guidance import GUIDANCE
from scripts.build_prediction_probe import build as prediction_build

ROOT = Path(__file__).resolve().parents[1]


def build():
    notebook,metadata,manifest = prediction_build()
    files = {name:(ROOT/name).read_text(encoding='utf-8') for name in (
        'hydra/study_memory.py','hydra/research_guidance.py','scripts/install_study_agent.py',
        'scripts/study_agent_probe.py','scripts/prediction_study_agent_probe.py')}
    source = notebook['cells'][1]['source']
    anchor = "sys.path.insert(0,str(bundle/'src/ARC3-Inference'))"
    assert source.count(anchor) == 1
    hook = f'study_sources={files!r}\nstudy_extension={{}}\n'
    hook += 'exec(study_sources["scripts/install_study_agent.py"],study_extension)\n'
    hook += f'study_report=study_extension["install"](bundle,study_sources["hydra/study_memory.py"],{GUIDANCE!r})\n'
    hook += 'Path("/kaggle/working/hydra_study_extension.json").write_text(json.dumps(study_report,indent=2))\n'
    source = source.replace(anchor,hook+anchor)
    anchor = "prediction_probe['run_probe'](probe)"
    assert source.count(anchor) == 1
    source = source.replace(anchor,"""study_probe={}
exec(study_sources['scripts/study_agent_probe.py'],study_probe)
study_report=study_probe['run_probe'](probe)
mechanical=json.loads(Path('/kaggle/working/verified-probe.json').read_text())
prediction_report=prediction_probe['run_probe']({'run_probe':lambda **kwargs:mechanical})
combined_probe={}
exec(study_sources['scripts/prediction_study_agent_probe.py'],combined_probe)
combined_probe['run_probe'](prediction_report,study_report)
""")
    compile(source,'prediction-study-cpu-gate','exec')
    notebook['cells'][1]['source'] = source
    notebook['cells'][0]['source'] = ('# ARC3 prediction and study-memory composition gate\n\n'
        'CPU-only real sandbox/ToolAgent checks for composition of existing extensions. '
        'No model inference, game solutions, GPU or competition submission. '
        'This gate does not establish score benefit; existing attribution retained.')
    metadata.update(id='kunalsinghh25/arc-hydra-prediction-study-cpu-probe',
                    title='ARC Hydra Prediction Study CPU Probe')
    manifest['study_files'] = {name:sha256(text.encode()).hexdigest() for name,text in files.items()}
    return notebook,metadata,manifest


if __name__ == '__main__':
    notebook,metadata,manifest = build()
    output = ROOT/'notebooks/prediction_study_cpu_probe'
    output.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',metadata),('source-manifest.json',manifest)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('Staged CPU-only prediction/study composition gate; no launch')
