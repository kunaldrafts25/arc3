"""Package an isolated CPU dependency/meta-model check for a future ARC3 trainer."""
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'reports/research/arc3-training-selection-20261101'

SOURCE=r'''from pathlib import Path
from hashlib import sha256
import json,os,subprocess,sys,zipfile,urllib.request
work=Path('/kaggle/working');bundle=work/'arc3-training-dependencies';bundle.mkdir(exist_ok=True)
roots=[Path('/kaggle/input/datasets/dfranzen/pennyroyal-v253'),Path('/kaggle/input/pennyroyal-v253')]
root=next(p for p in roots if p.is_dir());wheels=root/'wheels';lock=root/'requirements.lock'
assert sha256(lock.read_bytes()).hexdigest()==BASE_LOCK_SHA256,'Base lock changed'
environment=dict(os.environ,UV_OFFLINE='1',UV_PYTHON_DOWNLOADS='never',PYTHONNOUSERSITE='1',
    HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',USE_TF='0',USE_TORCHVISION='0')
environment.pop('PYTHONPATH',None)
venv=Path('/tmp/arc3-training-cpu-env');uv=Path('/tmp/arc3-training-uv');python=venv/'bin/python'
uv_wheels=list(wheels.glob('uv-*.whl'));assert len(uv_wheels)==1
with zipfile.ZipFile(uv_wheels[0]) as archive:
    names=[n for n in archive.namelist() if Path(n).name=='uv' and not n.endswith('/')];assert len(names)==1
    uv.write_bytes(archive.read(names[0]));uv.chmod(0o755)
def run(arguments):
    result=subprocess.run(list(map(str,arguments)),env=environment,text=True,capture_output=True)
    print(result.stdout[-3500:],flush=True)
    if result.returncode:print(result.stderr[-7000:],flush=True);raise RuntimeError('Isolated CPU command failed')
run([uv,'venv','--python',sys.executable,venv])
run([uv,'pip','install','--python',python,'--no-index','--find-links',wheels,'-r',lock])
# Public, pinned pure Python wheels only. Existing Torch/CUDA/Transformers are retained.
for name,package in PACKAGES.items():
    with urllib.request.urlopen('https://pypi.org/pypi/'+name+'/'+package['version']+'/json',timeout=30) as stream:
        current=json.load(stream)
    wheel=next(x for x in current['urls'] if x['filename']==package['filename'])
    with urllib.request.urlopen(wheel['url'],timeout=60) as stream:content=stream.read()
    assert sha256(content).hexdigest()==package['sha256'],'Pinned wheel mismatch'
    (bundle/package['filename']).write_bytes(content)
run([uv,'pip','install','--python',python,'--no-index','--no-deps',*sorted(bundle.glob('*.whl'))])
run([uv,'pip','check','--python',python])
config_path=work/'qwen27-bf16-config.json';config_path.write_text(json.dumps(MODEL_CONFIG))
probe=work/'training_meta_probe.py'
probe.write_text(r"""import json,torch,transformers,peft,accelerate,inspect
from pathlib import Path
from transformers import AutoConfig,AutoModelForImageTextToText
from accelerate import init_empty_weights
raw=json.loads(Path('/kaggle/working/qwen27-bf16-config.json').read_text())
kind=raw.pop('model_type');config=AutoConfig.for_model(kind,**raw)
with init_empty_weights():
    model=AutoModelForImageTextToText.from_config(config,torch_dtype=torch.bfloat16)
modules=[]
for name,module in model.named_modules():
    if isinstance(module,torch.nn.Linear) and 'language_model.layers.' in name:
        modules.append(dict(name=name,in_features=module.in_features,out_features=module.out_features))
assert modules,'No language-model linear modules found'
assert all(p.device.type=='meta' for p in model.parameters()),'Unexpected real parameter allocation'
report=dict(passed=True,torch=torch.__version__,transformers=transformers.__version__,peft=peft.__version__,
    accelerate=accelerate.__version__,cuda_available=torch.cuda.is_available(),
    model_class=type(model).__name__,supports_gradient_checkpointing=model.supports_gradient_checkpointing,
    linear_modules=modules,parameters=sum(p.numel() for p in model.parameters()),
    boundary='CPU imports and meta-device model construction only. No loaded checkpoint, multimodal tensor validation, actual gradients, CUDA training, saved-adapter reload or serving compatibility established.')
Path('/kaggle/working/training-environment-probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='linear_modules'},indent=2))
""")
run([python,probe])
manifest=dict(packages=PACKAGES,base_runtime='dfranzen/pennyroyal-v253',base_lock_sha256=BASE_LOCK_SHA256,
    files={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(bundle.glob('*.whl'))})
(bundle/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('TRAINING_DEPENDENCY_CPU_CHECK_COMPLETE',flush=True)
'''


def build():
    packages={}
    for name in ['peft','accelerate']:
        info=json.loads((RESEARCH/(name+'-pypi.json')).read_text())
        wheel=next(x for x in info['urls'] if x['filename'].endswith('py3-none-any.whl'))
        packages[name]=dict(version=info['version'],filename=wheel['filename'],sha256=wheel['sha256'])
    config=json.loads((RESEARCH/'qwen27-config.json').read_text())
    source=f'PACKAGES={packages!r}\nMODEL_CONFIG={config!r}\nBASE_LOCK_SHA256={sha256((RESEARCH/"requirements.lock").read_bytes()).hexdigest()!r}\n'+SOURCE
    compile(source,'training-environment-cpu-probe','exec')
    base=json.loads((ROOT/'notebooks/qwen27_cpu_preflight_v2/kernel-metadata.json').read_text())
    base.update(id='kunalsinghh25/arc-hydra-training-environment-cpu-probe',title='ARC Hydra Training Environment CPU Probe',
        code_file='probe.ipynb',enable_gpu=False,enable_tpu=False,enable_internet=True,is_private=True,
        dataset_sources=['dfranzen/pennyroyal-v253'],model_sources=[],competition_sources=[],kernel_sources=[])
    base.pop('machine_shape',None)
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='markdown',metadata={},source='# ARC3 isolated training dependency probe\n\nCPU only. Reuses the frozen offline runtime; adds pinned PEFT/Accelerate wheels without changing Torch/CUDA/Transformers. Meta-model construction does not establish training or model quality. No game access or weight loading. Qwen, Hugging Face and Pennyroyal attribution retained.'),
               dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None)])
    out=ROOT/'notebooks/training_environment_cpu_probe';out.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',base)]:
        (out/name).write_text(json.dumps(value,indent=2)+'\n')
    manifest=dict(kernel=base['id'],wall_seconds=1800,cpu_only=True,
        files={name:sha256((out/name).read_bytes()).hexdigest() for name in ['probe.ipynb','kernel-metadata.json']})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))

if __name__=='__main__':build()
