"""Compose a separate offline CPU gate without changing previous validated sources."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_study_probe import build as study_build

ROOT=Path(__file__).resolve().parents[1]


def build():
    notebook,metadata,manifest=study_build()
    files={name:(ROOT/name).read_text(encoding='utf-8') for name in
        ('hydra/recovery_monitor.py','scripts/install_recovery_agent.py','scripts/recovery_agent_probe.py')}
    cell=notebook['cells'][1];source=cell['source']
    anchor="sys.path.insert(0,str(bundle/'src/ARC3-Inference'))"
    hook=f'recovery_sources={files!r}\nrecovery_extension={{}}\nexec(recovery_sources["scripts/install_recovery_agent.py"],recovery_extension)\n'
    hook+='recovery_report=recovery_extension["install"](bundle,recovery_sources["hydra/recovery_monitor.py"])\n'
    hook+='Path("/kaggle/working/hydra_recovery_extension.json").write_text(json.dumps(recovery_report,indent=2))\n'
    assert source.count(anchor)==1
    source=source.replace(anchor,hook+anchor)
    source+='\nrecovery_probe={}\nexec(recovery_sources["scripts/recovery_agent_probe.py"],recovery_probe)\nrecovery_probe["run_probe"]()\n'
    compile(source,'recovery-cpu-probe','exec');cell['source']=source
    notebook['cells'][0]['source']='# ARC-Hydra advisory recovery CPU gate\n\nOriginal mechanical/prompt and study-memory tests, plus actual-host cross-decision recovery evidence, cooldown and game/level isolation. No action gating or model inference.'
    metadata.update(id='kunalsinghh25/arc-hydra-recovery-cpu-probe',title='ARC Hydra Recovery CPU Probe')
    manifest['recovery_files']={name:sha256(text.encode()).hexdigest() for name,text in files.items()}
    return notebook,metadata,manifest


if __name__=='__main__':
    notebook,metadata,manifest=build()
    output=ROOT/'notebooks/recovery_cpu_probe';output.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',metadata),('source-manifest.json',manifest)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('Created CPU-only recovery integration gate')
