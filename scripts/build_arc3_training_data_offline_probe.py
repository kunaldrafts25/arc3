"""Small CPU notebook reading reviewed inputs from a private hashed dataset."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_arc3_training_data_probe import PROBE
from scripts.build_arc3_training_environment_probe import SOURCE as ENV_SOURCE
from scripts.build_qwen27_probe import TARGET

ROOT=Path(__file__).resolve().parents[1]
BF16='dangkhoa2016/qwen-qwen3-8-27b/Transformers/default/1'

EXTRACT=r'''import tarfile
input_roots=[Path('/kaggle/input/datasets/kunalsinghh25/arc3-training-pilot-inputs-v1'),Path('/kaggle/input/arc3-training-pilot-inputs-v1')]
assets=work/'training-assets';assets.mkdir(exist_ok=True)
archives=[root/'training-pilot-inputs.tar.gz' for root in input_roots if (root/'training-pilot-inputs.tar.gz').is_file()]
if archives:
    assert len(archives)==1
    archive=archives[0]
    assert sha256(archive.read_bytes()).hexdigest()==ARCHIVE_SHA256,'Private input archive changed'
    tar=tarfile.open(archive,'r:gz')
    manifest=json.loads(tar.extractfile('manifest.json').read())
    def read_asset(name):
        member=tar.getmember(name)
        if not member.isfile():raise ValueError('Invalid archive member')
        return tar.extractfile(member).read()
    input_asset_mode='archive-sha256-and-file-sha256'
else:
    # Kaggle automatically expanded this uploaded tar.gz. The API file listing
    # verifies this exact prefix; validate every original manifest/file hash.
    roots=[root/'training-pilot-inputs' for root in input_roots if (root/'training-pilot-inputs/manifest.json').is_file()]
    if len(roots)!=1:raise ValueError('Pinned expanded assets are not uniquely mounted: '+str(roots))
    source_root=roots[0].resolve();manifest=json.loads((source_root/'manifest.json').read_text())
    def read_asset(name):
        source=(source_root/name).resolve()
        if not source.is_relative_to(source_root) or not source.is_file():raise ValueError('Invalid expanded asset path')
        return source.read_bytes()
    input_asset_mode='kaggle-expanded-exact-manifest-and-file-sha256'
assert manifest==EXPECTED_INPUT_MANIFEST
try:
    for name,record in manifest['files'].items():
        destination=(assets/name).resolve()
        if not destination.is_relative_to(assets.resolve()):raise ValueError('Asset escapes output root')
        content=read_asset(name)
        assert len(content)==record['bytes'] and sha256(content).hexdigest()==record['sha256'],name
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(content)
finally:
    if archives:tar.close()
(assets/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('TRAINING_ASSET_INTEGRITY',input_asset_mode,flush=True)
model=Path(MODEL_PATH);bf16=Path(BF16_PATH)
assert sha256((bf16/'tokenizer.json').read_bytes()).hexdigest()==EXPECTED_TARGET_METADATA['tokenizer.json']['sha256'],'BF16 training tokenizer differs from deployment target'
bc=json.loads((bf16/'config.json').read_text());tc=json.loads((model/'config.json').read_text())
for key in ['vocab_size','hidden_size','num_hidden_layers','num_attention_heads','num_key_value_heads']:
    assert bc['text_config'][key]==tc['text_config'][key],key
assert bc['architectures']==tc['architectures']==['Qwen3_5ForConditionalGeneration']
for wheel in (assets/'wheels').glob('*.whl'):(bundle/wheel.name).symlink_to(wheel)
'''


def build():
    package=json.loads((ROOT/'reports/arc3/qwen27-training-pilot/input-package.json').read_text())
    actual=json.loads((ROOT/'reports/kaggle/qwen27-cpu-preflight-v2/qwen27-preflight.json').read_text())
    source=ENV_SOURCE[:ENV_SOURCE.index('config_path=work/')]
    begin=source.index('for name,package in PACKAGES.items():')
    end=source.index("run([uv,'pip','install','--python',python,'--no-index','--no-deps'",begin)
    source=source[:begin]+source[end:]
    before=source.index("run([uv,'venv'")
    source=source[:before]+EXTRACT+source[before:]
    source+='''rows=[]
for split in ['train','validation']:
    rows.extend(dict(context=16384,record=json.loads(line)) for line in (assets/'16k'/f'{split}.jsonl').read_text().splitlines())
    candidates=[json.loads(line) for line in (assets/'32k'/f'{split}.jsonl').read_text().splitlines()]
    rows.extend(dict(context=32768,record=row) for row in sorted(candidates,key=lambda r:r['text_tokens']+r['visual_expansion_tokens'],reverse=True)[:8])
(work/'selected-training-rows.json').write_text(json.dumps(rows))
'''
    collator=(ROOT/'hydra/arc3_training_collator.py').read_text()
    expected=package['manifest']['files']['arc3_training_collator.py']['sha256']
    if sha256(collator.encode()).hexdigest()!=expected:raise ValueError('Packaged collator differs')
    probe=f'MODEL_PATH={actual["target_path"]!r}\nEXPECTED_METADATA={actual["metadata"]["target"]!r}\nCOLLATOR_SOURCE={collator!r}\n'+PROBE
    source+=f"probe=work/'actual_training_data_probe.py'\nprobe.write_text({probe!r})\nrun([python,probe])\n"
    source+="run([python,'-c','from fla.ops.gated_delta_rule import chunk_gated_delta_rule; assert callable(chunk_gated_delta_rule); print(\"FLA_CPU_IMPORT_PASSED\")'])\n"
    source+="(bundle/'manifest.json').write_text(json.dumps(dict(files={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(bundle.glob('*.whl'))},base_lock_sha256=BASE_LOCK_SHA256),indent=2)+'\\n')\n"
    constants=dict(ARCHIVE_SHA256=package['archive_sha256'],EXPECTED_INPUT_MANIFEST=package['manifest'],
        BASE_LOCK_SHA256=package['manifest']['files']['base-requirements.lock']['sha256'],
        MODEL_PATH=actual['target_path'],BF16_PATH='/kaggle/input/models/'+BF16.lower(),
        EXPECTED_TARGET_METADATA=actual['metadata']['target'])
    source='\n'.join(name+'='+repr(value) for name,value in constants.items())+'\n'+source
    compile(source,'offline-data-cpu-gate','exec')
    metadata=json.loads((ROOT/'notebooks/qwen27_cpu_preflight_v2/kernel-metadata.json').read_text())
    metadata.update(id='kunalsinghh25/arc-hydra-training-data-offline-probe',title='ARC Hydra Training Data Offline Probe',
        model_sources=[TARGET,BF16],dataset_sources=['dfranzen/pennyroyal-v253',package['dataset']],kernel_sources=[],competition_sources=[],
        enable_gpu=False,enable_tpu=False,enable_internet=False,is_private=True)
    metadata.pop('machine_shape',None)
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='markdown',metadata={},source='# ARC3 offline training data CPU gate\n\nUses hashed private training assets, actual native multimodal processor/loss masks and meta-device LoRA placement. CPU only, no model weights loaded or gradients. No score claim. Upstream attribution and licenses retained.'),
               dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None)])
    out=ROOT/'notebooks/training_data_offline_probe_v2';out.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',metadata)]:
        (out/name).write_text(json.dumps(value,indent=2)+'\n')
    report=dict(kernel=metadata['id'],cpu_only=True,wall_seconds=1800,input_archive_sha256=package['archive_sha256'],
        files={name:sha256((out/name).read_bytes()).hexdigest() for name in ['probe.ipynb','kernel-metadata.json']})
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':build()
