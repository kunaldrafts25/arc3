"""CPU-only integration gate for the research-derived memory/protocol extension."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_verified_probe import build as base_build
from hydra.research_guidance import GUIDANCE

ROOT=Path(__file__).resolve().parents[1]


def build():
    notebook,metadata,manifest=base_build(enforce_probes=False)
    files={name:(ROOT/name).read_text(encoding='utf-8') for name in
           ('hydra/study_memory.py','hydra/research_guidance.py','scripts/install_study_agent.py','scripts/study_agent_probe.py')}
    source=notebook['cells'][1]['source']
    anchor="sys.path.insert(0,str(bundle/'src/ARC3-Inference'))"
    hook=f'study_sources={files!r}\nstudy_extension={{}}\nexec(study_sources["scripts/install_study_agent.py"],study_extension)\n'
    hook+=f'study_report=study_extension["install"](bundle,study_sources["hydra/study_memory.py"],{GUIDANCE!r})\n'
    hook+='Path("/kaggle/working/hydra_study_extension.json").write_text(json.dumps(study_report,indent=2))\n'
    assert source.count(anchor)==1
    source=source.replace(anchor,hook+anchor)
    run="probe['run_probe'](enforce_probes=False)"
    assert source.count(run)==1
    source=source.replace(run,'study_probe={}\nexec(study_sources["scripts/study_agent_probe.py"],study_probe)\nstudy_probe["run_probe"](probe)')
    compile(source,'study-cpu-probe','exec')
    notebook['cells'][1]['source']=source
    notebook['cells'][0]['source']='# ARC-Hydra general learning CPU integration gate\n\nOffline CPU-only synthetic tests of bounded evidence memory, actual host persistence/prompting, game isolation and original action flexibility. No LLM or game implementations are inspected.'
    metadata.update(id='kunalsinghh25/arc-hydra-study-cpu-probe',title='ARC Hydra Study CPU Probe')
    manifest['study_files']={name:sha256(text.encode()).hexdigest() for name,text in files.items()}
    manifest['guidance_sha256']=sha256(GUIDANCE.encode()).hexdigest()
    return notebook,metadata,manifest


if __name__=='__main__':
    notebook,metadata,manifest=build()
    output=ROOT/'notebooks/study_cpu_probe';output.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',metadata),('source-manifest.json',manifest)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('Created CPU-only study integration gate')
