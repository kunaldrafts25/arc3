"""CPU-only check of exact completed training output mounts and adapter headers."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_arc3_lora_gameplay import TRAIN

ROOT=Path(__file__).resolve().parents[1]


def build():
    gate=ROOT/'reports/kaggle/qwen27-lora-pilot-v1'
    report_path=gate/'sft-pilot/training-report.json'
    report=json.loads(report_path.read_text())
    assert report['phase']=='complete' and report['optimizer_steps']==40
    constants=dict(EXPECTED_FILES=report['serving_export']['files'],EXPECTED_REPORT_SHA256=sha256(report_path.read_bytes()).hexdigest())
    source='\n'.join(k+'='+repr(v) for k,v in constants.items())+'\n'
    source+='''from pathlib import Path
from hashlib import sha256
import json,struct,time
roots=[Path('/kaggle/input/notebooks/kunalsinghh25/arc-hydra-qwen27-lora-pilot/1'),
    Path('/kaggle/input/notebooks/kunalsinghh25/arc-hydra-qwen27-lora-pilot'),
    Path('/kaggle/input/arc-hydra-qwen27-lora-pilot')]
hits=set()
for root in roots:
    if root.is_dir():hits.update(p.parent.resolve() for p in root.rglob('serving-adapter/adapter_config.json'))
if len(hits)!=1:raise ValueError('Pinned training adapter not uniquely mounted: '+str(hits))
adapter=next(iter(hits))
def digest(path):
    value=sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):value.update(chunk)
    return value.hexdigest()
for name,record in EXPECTED_FILES.items():
    path=adapter/name
    assert path.stat().st_size==record['bytes'] and digest(path)==record['sha256'],name
assert digest(adapter.parent/'training-report.json')==EXPECTED_REPORT_SHA256
config=json.loads((adapter/'adapter_config.json').read_text())
assert config['r']==16 and config['lora_alpha']==32
assert sorted(config['target_modules'])==sorted(['qkv_proj','o_proj','out_proj','in_proj_qkvz','gate_up_proj','down_proj'])
with (adapter/'adapter_model.safetensors').open('rb') as stream:
    length=struct.unpack('<Q',stream.read(8))[0]
    assert 0<length<2**20
    header=json.loads(stream.read(length))
tensors={name:value for name,value in header.items() if name!='__metadata__'}
assert len(tensors)==992 and all(value['dtype']=='F32' for value in tensors.values())
qkvz=[]
for name,value in tensors.items():
    if '.in_proj_q.' not in name or '.lora_B.' not in name:continue
    for projection,width in [('q',2048),('k',2048),('v',6144),('z',6144)]:
        b=name.replace('.in_proj_q.','.in_proj_'+projection+'.')
        a=b.replace('.lora_B.','.lora_A.')
        assert tensors[b]['shape']==[width,16] and tensors[a]['shape']==[16,5120],b
    qkvz.append(name)
assert len(qkvz)==48
result=dict(passed=True,training_kernel='kunalsinghh25/arc-hydra-qwen27-lora-pilot/1',
    adapter_directory=str(adapter),actual_tensor_count=len(tensors),recurrent_groups_checked=len(qkvz),
    training_report_sha256=EXPECTED_REPORT_SHA256,adapter_files=EXPECTED_FILES,
    boundary='CPU-only exact mount, file hashes and saved tensor-header check. No weights loaded into a model; no inference or gameplay claim.')
Path('/kaggle/working/adapter-mount-probe.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result,indent=2))
'''
    compile(source,'actual-adapter-mount-cpu-probe','exec')
    meta=json.loads((ROOT/'notebooks/training_data_offline_probe_v2/kernel-metadata.json').read_text())
    meta.update(id='kunalsinghh25/arc-hydra-adapter-mount-cpu-probe',title='ARC Hydra Adapter Mount CPU Probe',
        code_file='probe.ipynb',kernel_sources=[TRAIN],dataset_sources=[],model_sources=[],competition_sources=[],
        enable_gpu=False,enable_tpu=False,enable_internet=False,is_private=True)
    meta.pop('machine_shape',None)
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None)])
    destination=ROOT/'notebooks/adapter_mount_cpu_probe';destination.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',meta)]:
        (destination/name).write_text(json.dumps(value,indent=2)+'\n')
    result=dict(kernel=meta['id'],wall_seconds=600,cpu_only=True,files={name:sha256((destination/name).read_bytes()).hexdigest() for name in ['probe.ipynb','kernel-metadata.json']})
    (destination/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':build()
