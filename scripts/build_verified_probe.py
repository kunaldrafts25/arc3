"""Package the exact extension for a CPU-only check against Kaggle's source bundle."""
from hashlib import sha256
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def build(enforce_probes=True):
    upstream=json.loads((ROOT/'baselines/duck_m2/upstream.ipynb').read_text(encoding='utf-8'))
    patch=next(''.join(c['source']) for c in upstream['cells'] if ''.join(c['source']).startswith('%%writefile /kaggle/harness-changes.patch')).split('\n',1)[1]
    # IPython's %%writefile adds the final newline; direct write_text does not.
    if not patch.endswith('\n'):
        patch+='\n'
    sources={p:(ROOT/p).read_text(encoding='utf-8') for p in
        ('hydra/verified_planning.py','scripts/install_verified_agent.py','scripts/verified_agent_probe.py')}
    source='''from pathlib import Path
import json, shutil, subprocess, sys
original=Path('/kaggle/input/datasets/dfranzen/taaf-kaggle-source-bundle-copy')
if not original.is_dir(): original=Path('/kaggle/input/taaf-kaggle-source-bundle-copy')
assert original.is_dir(), 'Original source bundle is not mounted'
bundle=Path('/kaggle/working/verified-probe-source')
shutil.copytree(original,bundle)
patch=Path('/kaggle/working/harness-changes.patch')
'''
    source+=f'patch.write_text({patch!r})\n'
    source+='subprocess.run(["git","apply","--include=ARC3-Inference/*",str(patch)],cwd=bundle/"src",check=True)\n'
    source+=f'sources={sources!r}\n'
    source+='''extension={}
exec(sources['scripts/install_verified_agent.py'],extension)
'''
    source+=f"report=extension['install'](bundle,sources['hydra/verified_planning.py'],enforce_probes={enforce_probes!r})\n"
    source+='''
Path('/kaggle/working/hydra_extension.json').write_text(json.dumps(report,indent=2))
sys.path.insert(0,str(bundle/'src/ARC3-Inference'))
probe={}
exec(sources['scripts/verified_agent_probe.py'],probe)
'''
    source+=f"probe['run_probe'](enforce_probes={enforce_probes!r})\n"
    compile(source,'verified-agent-cpu-probe','exec')
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='markdown',metadata={},source='# ARC-Hydra verified agent CPU integration probe\n\nPrivate, offline CPU-only synthetic tests against the actual attributed Duck source bundle. No model weights or competition gameplay. Original harness: Daniel Franzen / Jeroen Cottaar / Tufa Labs, Apache-2.0; notices retained.'),
               dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None)])
    metadata=json.loads((ROOT/'notebooks/serving_v3_repair/kernel-metadata.json').read_text())
    metadata.update(id='kunalsinghh25/arc-hydra-verifier-cpu-probe',title='ARC Hydra Verifier CPU Probe',code_file='probe.ipynb',
        enable_gpu=False,enable_tpu=False,enable_internet=False,is_private=True,
        dataset_sources=['dfranzen/taaf-kaggle-source-bundle-copy'],model_sources=[],kernel_sources=[],competition_sources=[])
    manifest=dict(files={name:sha256(data.encode()).hexdigest() for name,data in sources.items()},upstream_patch_sha256=sha256(patch.encode()).hexdigest(),enforce_probes=enforce_probes)
    return notebook,metadata,manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--planning-assist',action='store_true')
    args=parser.parse_args()
    notebook,metadata,manifest=build(enforce_probes=not args.planning_assist)
    output=ROOT/'notebooks/verified_cpu_probe'
    output.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',metadata),('source-manifest.json',manifest)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('Created offline CPU extension probe; no model, competition or GPU attachment')
