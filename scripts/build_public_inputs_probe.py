"""Offline CPU validation of public-only development assets on the compute account."""
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def build():
    manifest=json.loads((ROOT/'reference/public-development-inputs/public-input-manifest.json').read_text(encoding='utf-8'))
    expected=json.loads((ROOT/'reference/public-development-reset-references.json').read_text(encoding='utf-8'))
    assert set(expected)==set(manifest['game_ids']) and len(expected)==25
    code='''from pathlib import Path
from hashlib import sha256
import importlib.metadata
import json,subprocess,sys
root=Path('/kaggle/input/datasets/kunalsinghh03/arc3-public-development-inputs')
if not root.is_dir():root=Path('/kaggle/input/arc3-public-development-inputs')
assert root.is_dir(), 'Public development dataset not mounted'
print('PUBLIC INPUT ROOT',str(root),flush=True)
print('PUBLIC INPUT CONTENTS',sorted(p.name for p in root.iterdir()),flush=True)
manifest=json.loads((root/'public-input-manifest.json').read_text())
for item in manifest['environment_files']:
    assert sha256((root/item['file']).read_bytes()).hexdigest()==item['sha256']
for item in manifest['pypi_wheels']:
    assert sha256((root/'arc_agi_3_wheels'/item['file']).read_bytes()).hexdigest()==item['sha256']
subprocess.run([sys.executable,'-m','pip','install','--quiet','--no-index','--no-warn-conflicts',
               '--find-links',str(root/'arc_agi_3_wheels'),'arc-agi==0.9.8','arcengine==0.9.3'],check=True)
import numpy as np
from arc_agi import Arcade,OperationMode
arc=Arcade(operation_mode=OperationMode.OFFLINE,environments_dir=str(root/'environment_files'))
ids=sorted(e.game_id for e in arc.get_environments())
assert ids==manifest['game_ids'], 'Public game set differs'
'''
    code+=f'expected={expected!r}\n'
    code+='''checks=[]
for game_id in ids:
    env=arc.make(game_id,seed=0)
    observation=env.reset()
    frame=np.asarray(observation.frame[-1],dtype=np.int16)
    digest=sha256(frame.tobytes()).hexdigest()
    assert digest==expected[game_id], 'Initial public observation differs: '+game_id
    checks.append(dict(game_id=game_id,shape=list(frame.shape),initial_observation_sha256=digest,total_levels=observation.win_levels))
report=dict(passed=True,games=len(checks),total_levels=sum(c['total_levels'] for c in checks),
            versions={name:importlib.metadata.version(name) for name in ('arc-agi','arcengine')},checks=checks,
            boundary='Offline public input/hash/RESET equivalence only. No model gameplay or score measured.')
Path('/kaggle/working/public-input-probe.json').write_text(json.dumps(report,indent=2))
print('PUBLIC_INPUT_CPU_PROBE_PASSED',json.dumps(report),flush=True)
'''
    compile(code,'public-inputs-probe','exec')
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='markdown',metadata={},source='# Public practice input equivalence gate\n\nCPU only; validates public PyPI artifacts, 25 practice versions and exact seeded RESET observations against prior direct public play. No competition datasource, entry or submission.'),dict(cell_type='code',metadata={},source=code,outputs=[],execution_count=None)])
    metadata=json.loads((ROOT/'notebooks/verified_cpu_probe/kernel-metadata.json').read_text())
    metadata.update(id='kunalsinghh03/arc-hydra-public-inputs-probe',title='ARC Hydra Public Inputs Probe',
        dataset_sources=['kunalsinghh03/arc3-public-development-inputs'])
    output=ROOT/'notebooks/public_inputs_probe';output.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',metadata)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('Prepared CPU public-input equivalence gate')


if __name__=='__main__':build()
