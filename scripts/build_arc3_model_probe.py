"""Stage a bounded CPU-only inspection of public checkpoint compatibility."""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1'
CANDIDATE = 'lamdang/thinkingcap-qwen3-8-flash-next-w4a16-autoround/Transformers/default/1'

SOURCE = r'''from pathlib import Path
from hashlib import sha256
import json,struct,time
started=time.monotonic()
deadline=started+1200
def locate(owner,slug):
    roots=[Path('/kaggle/input/models')/owner/slug,Path('/kaggle/input')/owner/slug]
    matches=[]
    for root in roots:
        if root.exists(): matches += list(root.rglob('config.json'))
    matches=[p.parent for p in matches if (p.parent/'model.safetensors.index.json').is_file()]
    if len(matches)!=1: raise ValueError('Expected one exact mounted checkpoint: '+slug+' '+str(matches))
    return matches[0]
def flatten(value,path=''):
    if isinstance(value,dict):
        return {k:v for key,item in value.items() for k,v in flatten(item,path+'/'+key).items()}
    return {path:value}
def inspect(root):
    config=json.loads((root/'config.json').read_text())
    index=json.loads((root/'model.safetensors.index.json').read_text())
    tensors={}
    files={}
    for filename in sorted(set(index['weight_map'].values())):
        if time.monotonic()>deadline: raise TimeoutError('CPU header inspection budget exhausted')
        path=(root/filename).resolve()
        if not path.is_relative_to(root.resolve()): raise ValueError('Checkpoint index path escapes input')
        with path.open('rb') as stream:
            length=struct.unpack('<Q',stream.read(8))[0]
            if length>128*1024*1024: raise ValueError('Unexpectedly large safetensors header')
            encoded=stream.read(length)
        header=json.loads(encoded)
        files[filename]=dict(size=path.stat().st_size,header_bytes=length,header_sha256=sha256(encoded).hexdigest())
        for key,value in header.items():
            if key=='__metadata__': continue
            if key in tensors: raise ValueError('Duplicate tensor name')
            tensors[key]=dict(shape=value['shape'],dtype=value['dtype'])
    missing=sorted(set(index['weight_map'])-set(tensors))
    if missing: raise ValueError('Index references missing tensors: '+str(missing[:5]))
    small={}
    for name in ('config.json','quantization_config.json','generation_config.json','tokenizer.json','tokenizer_config.json','chat_template.jinja','preprocessor_config.json','processor_config.json'):
        path=root/name
        if path.is_file():
            if path.stat().st_size>32*1024*1024: raise ValueError('Metadata unexpectedly large')
            small[name]=dict(size=path.stat().st_size,sha256=sha256(path.read_bytes()).hexdigest())
    return dict(config=config,tensors=tensors,files=files,metadata=small)
base=inspect(locate('dfranzen','intel-qwen3.8-flash-next-w4a16-autoround'))
candidate=inspect(locate('lamdang','thinkingcap-qwen3-8-flash-next-w4a16-autoround'))
base_config=flatten(base['config']);candidate_config=flatten(candidate['config'])
config_diff={k:dict(base=base_config.get(k),candidate=candidate_config.get(k)) for k in sorted(set(base_config)|set(candidate_config)) if base_config.get(k)!=candidate_config.get(k)}
base_keys=set(base['tensors']);candidate_keys=set(candidate['tensors'])
shape_diff={k:dict(base=base['tensors'][k],candidate=candidate['tensors'][k]) for k in sorted(base_keys&candidate_keys) if base['tensors'][k]!=candidate['tensors'][k]}
report=dict(base_ref='dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1',candidate_ref='lamdang/thinkingcap-qwen3-8-flash-next-w4a16-autoround/Transformers/default/1',elapsed_seconds=time.monotonic()-started,config_differences=config_diff,base_only_tensors=sorted(base_keys-candidate_keys),candidate_only_tensors=sorted(candidate_keys-base_keys),tensor_shape_dtype_differences=shape_diff,base_metadata=base['metadata'],candidate_metadata=candidate['metadata'],base_files=base['files'],candidate_files=candidate['files'],base_tensor_count=len(base_keys),candidate_tensor_count=len(candidate_keys),boundary='CPU metadata and safetensors headers only. Weight payloads are not loaded or compared. This does not establish inference correctness, draft acceptance, hardware fit, gameplay quality or a competition score. No GPU or game access.')
Path('/kaggle/working/model-compatibility.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('base_files','candidate_files','base_metadata','candidate_metadata','config_differences')},indent=2))
print('Config differences:',len(config_diff))
'''


def build():
    compile(SOURCE,'arc3-model-cpu-probe','exec')
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='markdown',metadata={},source='# ARC3 model compatibility research\n\nCPU-only inspection of public checkpoint metadata and tensor headers. No model inference, game access or score claim. Model authors retain all rights and attribution.'),
               dict(cell_type='code',metadata={},source=SOURCE,outputs=[],execution_count=None)])
    metadata=json.loads((ROOT/'notebooks/arc3_prediction_ablation_v2/control/kernel-metadata.json').read_text())
    metadata.update(id='kunalsinghh25/arc-hydra-model-compatibility-cpu-probe',title='ARC Hydra Model Compatibility CPU Probe',
        code_file='probe.ipynb',enable_gpu=False,enable_tpu=False,enable_internet=False,is_private=True,
        dataset_sources=[],kernel_sources=[],competition_sources=[],model_sources=[BASE,CANDIDATE])
    # machine_shape overrides enable_gpu in Kaggle's API. Preserve the executed
    # V1 package and eliminate the inherited accelerator in future builds.
    metadata.pop('machine_shape',None)
    assert not metadata['enable_gpu'] and not metadata.get('machine_shape')
    output=ROOT/'notebooks/model_compatibility_cpu_probe_v2';output.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',metadata)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(kernel=metadata['id'],cpu_only=True,launched=False,files={name:sha256((output/name).read_bytes()).hexdigest() for name in ('probe.ipynb','kernel-metadata.json')})))


if __name__=='__main__':build()
