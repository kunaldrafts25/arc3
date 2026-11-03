"""CPU gate for native FlashNext GGUF training; never loads full model weights."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_arc3_training_environment_probe import SOURCE as ENV_SOURCE
from scripts.build_arc3_training_data_offline_probe import EXTRACT

ROOT=Path(__file__).resolve().parents[1]
BASE='dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1'
GGUF='buianhtruc/strata-qwen3-8-flash-next-gsq-rco-iq3-s/GGUF/default/1'

PROBE=r'''from pathlib import Path
from hashlib import sha256
from collections import Counter
import json,torch,transformers,peft,accelerate
from transformers import AutoConfig,AutoModelForImageTextToText,AutoProcessor
from accelerate import init_empty_weights
from transformers.integrations.gguf.reader import GgufHeader,read_gguf_metadata
from transformers.integrations.gguf.gguf_quantized_parameter import GgufQuantizedParameter
from transformers.integrations.gguf.modules import GgufLinear
from transformers.integrations.gguf.moe import _project_expert
from peft import LoraConfig,get_peft_model
torch.set_num_threads(4)
work=Path('/kaggle/working');assets=work/'training-assets'
base=Path('/kaggle/input/models/dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/transformers/default/1')
quant=Path('/kaggle/input/models/buianhtruc/strata-qwen3-8-flash-next-gsq-rco-iq3-s/gguf/default/1')
report=dict(phase='checking',cuda_available=torch.cuda.is_available(),torch=torch.__version__,transformers=transformers.__version__,peft=peft.__version__,errors=[])
def save():
    (work/'flashnext-training-cpu-probe.json').write_text(json.dumps(report,indent=2)+'\n')
save()
try:
    assert not torch.cuda.is_available(),'CPU metadata must not allocate a GPU'
    assert torch.__version__=='2.13.0+cu130','Existing runtime Torch must be retained'
    files=sorted(quant.glob('*.gguf'));assert len(files)==2
    namespace={};exec(SPLIT_HELPER_SOURCE,namespace)
    headers=namespace['read_split_headers'](files)
    report['split_loader']=namespace['install_split_loader'](files)
    from transformers.quantizers.quantizer_gguf import GgufHfQuantizer
    from transformers.utils.quantization_config import GgufConfig
    quantizer=GgufHfQuantizer(GgufConfig(dequantize=False,mmap_policy='pread'))
    quantizer.read_header(str(files[0]))
    lazy=quantizer.get_state_dict(str(files[0]),None)
    assert len(lazy)==sum(len(header.tensors) for header in headers),'Incomplete split lazy-source inventory'
    report['split_lazy_tensors']=len(lazy)
    del lazy,quantizer
    names=[entry.name for header in headers for entry in header.tensors]
    assert len(names)==len(set(names)) and 'per_layer_token_embd.weight' in names
    report['gguf_headers']=[dict(file=path.name,bytes=path.stat().st_size,architecture=header.architecture,
        tensors=len(header.tensors),types=dict(Counter(entry.ggml_type for entry in header.tensors)),
        header_sha256=sha256(json.dumps([entry._asdict() for entry in header.tensors],sort_keys=True).encode()).hexdigest()) for path,header in zip(files,headers)]
    report['split_loading_required']=True
    config=AutoConfig.from_pretrained(base,local_files_only=True,trust_remote_code=False)
    with init_empty_weights():model=AutoModelForImageTextToText.from_config(config,dtype=torch.bfloat16)
    targets=[name for name,module in model.named_modules() if isinstance(module,torch.nn.Linear)
        and 'language_model.layers.' in name and '.indexer.' not in name
        and name.rsplit('.',1)[-1] in ['q_proj','k_proj','v_proj','o_proj','in_proj_qkv','in_proj_z','out_proj','gate_proj','up_proj','down_proj']]
    assert len(targets)==300,('Unexpected native language projection inventory',len(targets))
    assert all(p.device.type=='meta' for p in model.parameters())
    report.update(model_class=type(model).__name__,native_parameters=sum(p.numel() for p in model.parameters()),
        ordinary_lora_targets=targets,vision_parameters=sum(p.numel() for name,p in model.named_parameters() if '.visual.' in name))
    namespace={};exec(VISUAL_HELPER_SOURCE,namespace)
    restored=namespace['restore_visual_weights'](model,base,device='cpu')
    report['actual_visual_restore']={key:value for key,value in restored.items() if key!='verified_tensors'}
    report['actual_visual_restore']['tensor_manifest_sha256']=sha256(json.dumps(restored['verified_tensors'],sort_keys=True).encode()).hexdigest()
    del model
    # Real CPU activation gradients through persistent quantized bytes. The
    # independently known Q4_0 block encodes16 ones followed by16 zeros.
    payload=torch.zeros(32,18,dtype=torch.uint8);payload[:,:2]=torch.tensor([0,60],dtype=torch.uint8);payload[:,2:]=0x89
    weight=GgufQuantizedParameter(payload,quant_type=2,logical_shape=(32,32))
    layer=GgufLinear(32,32,bias=False,dtype=torch.float32,compute_dtype=torch.float32);layer.weight=weight
    expected=torch.cat([torch.ones(32,16),torch.zeros(32,16)],dim=1)
    x=torch.randn(3,32,requires_grad=True);gradient=torch.randn(3,32)
    actual=layer(x);actual.backward(gradient)
    assert torch.allclose(actual,torch.nn.functional.linear(x,expected),atol=1e-6,rtol=1e-6)
    assert torch.allclose(x.grad,gradient@expected,atol=1e-6,rtol=1e-6)
    expert_payload=payload.unsqueeze(0).repeat(4,1,1)
    expert_weight=GgufQuantizedParameter(expert_payload,quant_type=2,logical_shape=(4,32,32))
    selected=torch.tensor([2]);z=torch.randn(3,32,requires_grad=True)
    projected=_project_expert(z,expert_weight,selected,torch.float32,'eager');projected.backward(gradient)
    assert torch.allclose(z.grad,gradient@expected,atol=1e-6,rtol=1e-6)
    class Toy(torch.nn.Module):
        def __init__(self):super().__init__();self.projection=layer
        def forward(self,value):return self.projection(value)
    adapted=get_peft_model(Toy(),LoraConfig(r=4,lora_alpha=8,target_modules=['projection'],bias='none'))
    parameters=[p for p in adapted.parameters() if p.requires_grad]
    loss=adapted(torch.randn(3,32)).square().mean();loss.backward()
    assert parameters and all('lora_' in name for name,p in adapted.named_parameters() if p.requires_grad)
    assert any(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in parameters)
    report['tiny_quantized_activation_gradients']=dict(passed=True,linear_and_selected_expert=True,peft_adapter_gradients=True,
        boundary='Actual tiny CPU Q4_0 math only; not CUDA grouped-MM, full IQ3_S training or ARC3 quality.')
    processor=AutoProcessor.from_pretrained(base,local_files_only=True,trust_remote_code=False)
    namespace={};exec((assets/'arc3_training_collator.py').read_text(),namespace);collate=namespace['collate_example']
    prepared={'train':[],'validation':[]};rejected=[]
    allocation=json.loads((assets/'split.json').read_text())['games']
    for split in prepared:
        rows=[json.loads(line) for line in (assets/'32k'/f'{split}.jsonl').read_text().splitlines()]
        for row in rows:
            assert allocation[row['metadata']['game_id']]==split,'Frozen whole-game training allocation changed'
            kwargs=row['template_kwargs'];render=processor.tokenizer.apply_chat_template
            prefix=render(row['messages'][:-1],tools=row['tools'],tokenize=False,add_generation_prompt=True,**kwargs)
            text=render(row['messages'],tools=row['tools'],tokenize=False,add_generation_prompt=False,**kwargs)
            if not text.startswith(prefix):raise ValueError('Native FlashNext assistant boundary differs')
            row['assistant_start_char']=len(prefix);row['rendered_text_sha256']=sha256(text.encode()).hexdigest()
            try:batch,info=collate(row,processor,max_tokens=16384)
            except ValueError as error:
                if str(error)=='Training context limit exceeded':
                    rejected.append(dict(example=row['example_id'],reason='Actual native context exceeds16384'));continue
                raise
            row['supervised_text_tokens']=info['supervised_tokens'];row['native_flashnext_tensor_check']=info
            prepared[split].append(row);del batch
    for split,rows in prepared.items():
        (work/f'flashnext-{split}.jsonl').write_text(''.join(json.dumps(row,separators=(',',':'))+'\n' for row in rows))
    assert prepared['train'] and prepared['validation']
    report.update(phase='complete',passed=True,dataset_counts={k:len(v) for k,v in prepared.items()},rejected_contexts=rejected,
        dataset_sha256={k:sha256((work/f'flashnext-{k}.jsonl').read_bytes()).hexdigest() for k in prepared},
        boundary='CPU native multimodal processing, meta backbone, split lazy-source inventory, actual frozen visual weights and tiny quantized activation/LoRA gradients. No full-backbone weights, CUDA grouped-MM/training, saved adapter serving or gameplay improvement verified.')
    save();print(json.dumps({k:v for k,v in report.items() if k not in ['ordinary_lora_targets','rejected_contexts']},indent=2))
except BaseException as error:
    report.update(phase='failed',passed=False,error_type=type(error).__name__,error=str(error)[:1000]);save();raise
'''


def build():
    source_info=json.loads((ROOT/'reports/research/arc3-flashnext-gguf-training-20261101/hf-source-archive.json').read_text())
    data=json.loads((ROOT/'reports/arc3/qwen27-training-pilot/input-package.json').read_text())
    source=ENV_SOURCE[:ENV_SOURCE.index('# Public, pinned pure Python wheels only.')]
    extract=EXTRACT[:EXTRACT.index('model=Path(MODEL_PATH)')]
    source+=extract+"\nimport shutil\nfor wheel in (assets/'wheels').glob('*.whl'):shutil.copyfile(wheel,bundle/wheel.name)\n"
    source+="run([uv,'pip','install','--python',python,'--no-index','--no-deps',*sorted(bundle.glob('*.whl'))])\n"
    split_helper=(ROOT/'hydra/arc3_split_gguf.py').read_text()
    visual_helper=(ROOT/'hydra/arc3_flashnext_visual.py').read_text()
    actual_probe='SPLIT_HELPER_SOURCE='+repr(split_helper)+'\nVISUAL_HELPER_SOURCE='+repr(visual_helper)+'\n'+PROBE
    compile(actual_probe,'flashnext-native-probe-v2','exec')
    source+=f'''environment['UV_OFFLINE']='0'
def installed_distributions():
    code='import importlib.metadata as m,json; print(json.dumps({{d.metadata["Name"].lower().replace("_","-"):d.version for d in m.distributions()}}))'
    return json.loads(subprocess.check_output([str(python),'-c',code],env=environment,text=True))
base_distributions=installed_distributions()
archive=work/'transformers-source.tar.gz'
with urllib.request.urlopen({source_info['url']!r},timeout=90) as response:archive.write_bytes(response.read())
assert sha256(archive.read_bytes()).hexdigest()=={source_info['sha256']!r},'Pinned library source changed'
sources=Path('/tmp/arc3-transformers-source');sources.mkdir(exist_ok=True)
with tarfile.open(archive,'r:gz') as handle:handle.extractall(sources,filter='data')
project=next(p for p in sources.iterdir() if p.is_dir())
run([uv,'build','--python',python,'--wheel','--out-dir',bundle,project])
run([uv,'pip','uninstall','--python',python,'sglang'])
constraints=work/'torch-constraint.txt';constraints.write_text('torch==2.13.0+cu130\\n')
run([uv,'pip','install','--python',python,'--constraint',constraints,*sorted(bundle.glob('transformers-*.whl'))])
run([uv,'pip','check','--python',python])
installed=installed_distributions()
changed=[name+'=='+version for name,version in installed.items() if name!='transformers' and base_distributions.get(name)!=version]
if changed:run([sys.executable,'-m','pip','download','--no-deps','--only-binary=:all:','--dest',bundle,*changed])
(bundle/'manifest.json').write_text(json.dumps(dict(source_archive_sha256={source_info['sha256']!r},
    installed_distributions=installed,changed_requirements=changed,
    files={{p.name:sha256(p.read_bytes()).hexdigest() for p in bundle.glob('*.whl')}}),indent=2)+'\\n')
probe=work/'flashnext_native_probe.py';probe.write_text({actual_probe!r})
run([python,probe])
'''
    constants=dict(BASE_LOCK_SHA256=data['manifest']['files']['base-requirements.lock']['sha256'],ARCHIVE_SHA256=data['archive_sha256'],EXPECTED_INPUT_MANIFEST=data['manifest'])
    source='\n'.join(name+'='+repr(value) for name,value in constants.items())+'\n'+source
    compile(source,'flashnext-native-training-cpu-probe','exec')
    metadata=json.loads((ROOT/'notebooks/training_data_offline_probe_v2/kernel-metadata.json').read_text())
    metadata.update(id='kunalsinghh25/arc-hydra-flashnext-training-cpu-probe',title='ARC Hydra FlashNext Training CPU Probe',
        enable_gpu=False,enable_tpu=False,enable_internet=True,is_private=True,kernel_sources=[],competition_sources=[],
        model_sources=[BASE,GGUF],dataset_sources=['dfranzen/pennyroyal-v253',data['dataset']])
    metadata.pop('machine_shape',None)
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='markdown',metadata={},source='# Native FlashNext training CPU gate\n\nNo GPU or full checkpoint allocation. Pinned experimental Transformers GGUF fork, native vision processor, packed-weight tiny activation gradients. AMD-specific optimized kernels are not installed. Apache2.0 notices for Qwen, Hugging Face and the reviewed recipe remain applicable. No performance claim.'),dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None)])
    destination=ROOT/'notebooks/flashnext_training_cpu_probe_v2';destination.mkdir(exist_ok=True)
    for name,value in [('probe.ipynb',notebook),('kernel-metadata.json',metadata)]:
        (destination/name).write_text(json.dumps(value,indent=2)+'\n')
    result=dict(kernel=metadata['id'],cpu_only=True,wall_seconds=1800,files={name:sha256((destination/name).read_bytes()).hexdigest() for name in ['probe.ipynb','kernel-metadata.json']})
    (destination/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':build()
