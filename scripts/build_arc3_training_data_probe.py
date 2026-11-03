"""Build an offline CPU gate for actual 27B multimodal tensors and LoRA modules."""
import base64
import gzip
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_arc3_training_environment_probe import SOURCE as ENV_SOURCE
from scripts.build_qwen27_probe import TARGET

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'reports/research/arc3-training-selection-20261101'

PROBE=r'''import json,torch,hashlib
from pathlib import Path
from transformers import AutoProcessor,AutoConfig,AutoModelForImageTextToText
from accelerate import init_empty_weights
from peft import LoraConfig,get_peft_model
torch.set_num_threads(4)
root=Path(MODEL_PATH)
for name,expected in EXPECTED_METADATA.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected['sha256'],name
processor=AutoProcessor.from_pretrained(root,local_files_only=True,trust_remote_code=False)
namespace={};exec(COLLATOR_SOURCE,namespace)
collate=namespace['collate_example']
rows=json.loads(Path('/kaggle/working/selected-training-rows.json').read_text())
checks=[];errors=[]
for index,entry in enumerate(rows):
    record=entry['record']
    assert record['metadata']['split'] in ['train','validation']
    try:
        tensors,info=collate(record,processor,max_tokens=entry['context'])
        assert tensors['input_ids'].device.type=='cpu'
        assert tensors['labels'].device.type=='cpu'
        assert int((tensors['labels']!=-100).sum())==record['supervised_text_tokens']
        assert info['masked_prompt_tokens']>0
        checks.append(dict(example=record['example_id'],split=record['metadata']['split'],**info))
        del tensors
    except Exception as exc:
        errors.append(dict(example=record['example_id'],type=type(exc).__name__,error=str(exc)[:400]))
    if index%25==0:print('COLLATION_PROGRESS',index,len(rows),flush=True)
config=AutoConfig.from_pretrained(root,local_files_only=True,trust_remote_code=False)
with init_empty_weights():model=AutoModelForImageTextToText.from_config(config,torch_dtype=torch.bfloat16)
targets=[name for name,module in model.named_modules() if isinstance(module,torch.nn.Linear)
    and 'language_model.layers.' in name and '.self_attn.' in name
    and name.rsplit('.',1)[-1] in ['q_proj','k_proj','v_proj','o_proj']]
assert len(targets)==64,('Expected16 full-attention layers *4 projections',len(targets))
model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,target_modules=targets,
    lora_dropout=0.0,bias='none',task_type='CAUSAL_LM'))
trainable=[(name,p.numel()) for name,p in model.named_parameters() if p.requires_grad]
assert trainable and all('lora_' in name for name,count in trainable)
assert all('language_model.layers.' in name and '.self_attn.' in name for name,count in trainable)
report=dict(passed=not errors,examples_expected=len(rows),examples_passed=len(checks),errors=errors,
    tensor_checks=checks,lora_target_modules=targets,lora_trainable_parameters=sum(n for _,n in trainable),
    cuda_available=torch.cuda.is_available(),
    boundary='Actual CPU processor tensors, frozen render/prefix agreement, assistant-only labels and meta-model LoRA placement. No full checkpoint, CUDA backward step, training quality, adapter reload or serving compatibility established.')
Path('/kaggle/working/training-data-probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['tensor_checks','lora_target_modules']},indent=2))
assert report['passed'],'Actual training data processor gate failed; inspect retained report'
'''


def build():
    gate=ROOT/'reports/kaggle/training-environment-cpu-probe-v1'
    verified=json.loads((gate/'verified.json').read_text())
    if verified['status']!='COMPLETE':raise ValueError('Completed dependency gate required')
    manifest=gate/'arc3-training-dependencies/manifest.json'
    if sha256(manifest.read_bytes()).hexdigest()!=verified['manifest_sha256']:raise ValueError('Dependency manifest changed')
    source=ENV_SOURCE[:ENV_SOURCE.index('config_path=work/')]
    begin=source.index('for name,package in PACKAGES.items():')
    end=source.index("run([uv,'pip','install','--python',python,'--no-index','--no-deps'",begin)
    dependency_code=f'''parents=[Path('/kaggle/input/notebooks/kunalsinghh25/arc-hydra-training-environment-cpu-probe/1'),Path('/kaggle/input/arc-hydra-training-environment-cpu-probe')]
hits=[]
for parent in parents:
    if parent.is_dir():hits.extend(parent.rglob('arc3-training-dependencies/manifest.json'))
if len(hits)!=1:raise ValueError('Exact completed dependency kernel output is not uniquely mounted: '+str(hits))
dependency_manifest=hits[0]
assert sha256(dependency_manifest.read_bytes()).hexdigest()=={verified['manifest_sha256']!r}
for name,digest in json.loads(dependency_manifest.read_text())['files'].items():
    dependency=dependency_manifest.parent/name
    assert sha256(dependency.read_bytes()).hexdigest()==digest,name
    (bundle/name).symlink_to(dependency)
'''
    source=source[:begin]+source[end:]
    install_start=source.index("run([uv,'venv'")
    source=source[:install_start]+dependency_code+source[install_start:]
    entries=[]
    dataset=ROOT/'reports/arc3/qwen27-training-pilot'
    hashes={}
    for split in ['train','validation']:
        path=dataset/(split+'.jsonl');hashes[str(path.relative_to(ROOT))]=sha256(path.read_bytes()).hexdigest()
        entries.extend(dict(context=16384,record=json.loads(line)) for line in path.read_text().splitlines())
        path=dataset/'context-32768'/(split+'.jsonl');hashes[str(path.relative_to(ROOT))]=sha256(path.read_bytes()).hexdigest()
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        entries.extend(dict(context=32768,record=row) for row in sorted(rows,key=lambda x:x['text_tokens']+x['visual_expansion_tokens'],reverse=True)[:8])
    packed=base64.b64encode(gzip.compress(json.dumps(entries,separators=(',',':')).encode(),mtime=0)).decode()
    actual=json.loads((ROOT/'reports/kaggle/qwen27-cpu-preflight-v2/qwen27-preflight.json').read_text())
    processor_path=actual['target_path']
    metadata=actual['metadata']['target']
    collator=(ROOT/'hydra/arc3_training_collator.py').read_text()
    probe=f'MODEL_PATH={processor_path!r}\nEXPECTED_METADATA={metadata!r}\nCOLLATOR_SOURCE={collator!r}\n'+PROBE
    compile(probe,'actual-processor-cpu-probe','exec')
    source+='\nimport base64,gzip\n'
    source+=f"(work/'selected-training-rows.json').write_bytes(gzip.decompress(base64.b64decode({packed!r})))\n"
    source+=f"probe=work/'actual_training_data_probe.py'\nprobe.write_text({probe!r})\nrun([python,probe])\n"
    fast_manifest=json.loads((RESEARCH/'training-wheels/manifest.json').read_text())
    for record in fast_manifest.values():
        payload=(RESEARCH/'training-wheels'/record['filename']).read_bytes()
        if sha256(payload).hexdigest()!=record['sha256']:raise ValueError('Pinned training wheel changed')
        packed_wheel=base64.b64encode(payload).decode()
        source+=f"(bundle/{record['filename']!r}).write_bytes(base64.b64decode({packed_wheel!r}))\n"
    source+="run([uv,'pip','install','--python',python,'--no-index','--no-deps',*sorted(bundle.glob('*.whl'))])\n"
    source+="run([uv,'pip','check','--python',python])\n"
    source+="run([python,'-c','from fla.ops.gated_delta_rule import chunk_gated_delta_rule; assert callable(chunk_gated_delta_rule); print(\"FLA_CPU_IMPORT_PASSED\")'])\n"
    source+="(bundle/'manifest.json').write_text(json.dumps(dict(files={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(bundle.glob('*.whl'))},base_lock_sha256=BASE_LOCK_SHA256),indent=2)+'\\n')\n"
    source=f'BASE_LOCK_SHA256={sha256((RESEARCH/"requirements.lock").read_bytes()).hexdigest()!r}\n'+source
    compile(source,'offline-training-data-gate','exec')
    config=json.loads((ROOT/'notebooks/qwen27_cpu_preflight_v2/kernel-metadata.json').read_text())
    config.update(id='kunalsinghh25/arc-hydra-training-data-cpu-probe',title='ARC Hydra Training Data CPU Probe',
        enable_internet=False,enable_gpu=False,enable_tpu=False,model_sources=[TARGET],
        kernel_sources=[verified['kernel']],competition_sources=[])
    config.pop('machine_shape',None)
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='markdown',metadata={},source='# ARC3 actual training data gate\n\nOffline CPU test of native multimodal processor/loss masks and meta-device adapter placement. No model weights, training or gameplay. Original upstream licenses and attribution retained.'),
               dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None)])
    out=ROOT/'notebooks/training_data_cpu_probe';out.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',config)]:
        (out/name).write_text(json.dumps(value,indent=2)+'\n')
    result=dict(kernel=config['id'],wall_seconds=1800,cpu_only=True,examples=len(entries),dataset_sha256=hashes,
        collator_sha256=sha256(collator.encode()).hexdigest(),
        files={name:sha256((out/name).read_bytes()).hexdigest() for name in ['probe.ipynb','kernel-metadata.json']})
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':build()
