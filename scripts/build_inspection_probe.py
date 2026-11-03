"""Separate CPU gate for exact coordinate inspection on the flexible baseline."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_verified_probe import build as base_build

ROOT=Path(__file__).resolve().parents[1]


def build():
    notebook,metadata,manifest=base_build(enforce_probes=False)
    files={name:(ROOT/name).read_text(encoding='utf-8') for name in
        ('hydra/grid_inspection.py','scripts/install_inspection_agent.py','scripts/inspection_agent_probe.py')}
    source=notebook['cells'][1]['source'];anchor="sys.path.insert(0,str(bundle/'src/ARC3-Inference'))"
    hook=f'inspection_sources={files!r}\ninspection_extension={{}}\nexec(inspection_sources["scripts/install_inspection_agent.py"],inspection_extension)\n'
    hook+='inspection_report=inspection_extension["install"](bundle,inspection_sources["hydra/grid_inspection.py"])\n'
    hook+='Path("/kaggle/working/hydra_inspection_extension.json").write_text(json.dumps(inspection_report,indent=2))\n'
    assert source.count(anchor)==1;source=source.replace(anchor,hook+anchor)
    run="probe['run_probe'](enforce_probes=False)";assert source.count(run)==1
    source=source.replace(run,'inspection_probe={}\nexec(inspection_sources["scripts/inspection_agent_probe.py"],inspection_probe)\ninspection_probe["run_probe"](probe)')
    compile(source,'inspection-cpu-probe','exec');notebook['cells'][1]['source']=source
    notebook['cells'][0]['source']='# ARC-Hydra exact inspection CPU gate\n\nFlexible baseline regression cases plus exact pixel/region/run inspection, historical lookup, invalid-coordinate handling, actual host telemetry and game isolation. No model inference.'
    metadata.update(id='kunalsinghh25/arc-hydra-inspection-cpu-probe',title='ARC Hydra Inspection CPU Probe')
    manifest['inspection_files']={name:sha256(text.encode()).hexdigest() for name,text in files.items()}
    return notebook,metadata,manifest


if __name__=='__main__':
    notebook,metadata,manifest=build();output=ROOT/'notebooks/inspection_cpu_probe';output.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',metadata),('source-manifest.json',manifest)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('Created CPU-only exact inspection integration gate')
