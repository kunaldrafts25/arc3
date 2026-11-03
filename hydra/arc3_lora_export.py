"""Export native Qwen3.5 GDN adapters to the pinned SGLang split format."""
from hashlib import sha256
import json
from pathlib import Path

PACKED_TARGETS=['qkv_proj','o_proj','out_proj','in_proj_qkvz','gate_up_proj','down_proj']


def preflight_export(output,normalizer_source):
    """Execute the pinned runtime's normalizer on an actual tiny export."""
    import torch
    from safetensors.torch import load_file,save_file
    output=Path(output);native=output/'native';native.mkdir(parents=True)
    generator=torch.Generator().manual_seed(20261101)
    weights={}
    for layer in range(48):
        for projection,width in [('in_proj_qkv',8),('in_proj_z',4)]:
            prefix=f'base_model.model.model.language_model.layers.{layer}.linear_attn.{projection}'
            weights[prefix+'.lora_A.weight']=torch.randn(2,6,generator=generator)
            weights[prefix+'.lora_B.weight']=torch.randn(width,2,generator=generator)
    save_file(weights,str(native/'adapter_model.safetensors'))
    (native/'adapter_config.json').write_text(json.dumps(dict(r=2,lora_alpha=4,target_modules=['in_proj_qkv','in_proj_z'])))
    config=dict(linear_key_head_dim=1,linear_num_key_heads=2,linear_value_head_dim=1,linear_num_value_heads=4)
    exported=export_serving_adapter(native,output/'serving',config)
    converted=load_file(str(output/'serving/adapter_model.safetensors'))
    namespace={};exec(normalizer_source,namespace)
    namespace['_normalize_in_proj_qkvz'](None,converted)
    probe=torch.randn(6,3,generator=generator);errors=[]
    for layer in range(48):
        prefix=f'base_model.model.model.language_model.layers.{layer}.linear_attn.'
        expected=torch.cat([weights[prefix+p+'.lora_B.weight']@(weights[prefix+p+'.lora_A.weight']@probe)
            for p in ['in_proj_qkv','in_proj_z']],dim=0)
        a=converted[prefix+'in_proj_qkvz.lora_A.weight'];b=converted[prefix+'in_proj_qkvz.lora_B.weight']
        actual=torch.cat([bb@(aa@probe) for aa,bb in zip(a.split(2,dim=0),b.split([2,2,4,4],dim=0))],dim=0)
        if not torch.allclose(actual,expected,rtol=1e-4,atol=1e-5):raise ValueError('Pinned serving normalizer changes native recurrent adapter math')
        errors.append(float((actual-expected).abs().max()))
    return dict(passed=True,actual_runtime_normalizer_sha256=sha256(normalizer_source.encode()).hexdigest(),
        groups_checked=len(errors),max_absolute_error=max(errors),boundary='Actual Torch/safetensors export and pinned runtime normalization on tiny synthetic tensors only; saved trained weights and gameplay remain required.')


def export_serving_adapter(native_adapter,output,text_config):
    import torch
    from safetensors.torch import load_file,save_file
    native_adapter=Path(native_adapter);output=Path(output)
    if output.exists():raise ValueError('Refusing to overwrite serving export')
    weights=load_file(str(native_adapter/'adapter_model.safetensors'),device='cpu')
    config=json.loads((native_adapter/'adapter_config.json').read_text())
    key=int(text_config['linear_key_head_dim'])*int(text_config['linear_num_key_heads'])
    value=int(text_config['linear_value_head_dim'])*int(text_config['linear_num_value_heads'])
    if config.get('rank_pattern') or config.get('alpha_pattern'):
        raise ValueError('Only uniform rank/scaling is supported')
    converted={};checks=[]
    for name in sorted(weights):
        tensor=weights[name]
        if '.in_proj_qkv.' not in name:
            converted[name]=tensor
            continue
        if '.lora_A.' in name:
            for suffix in ['q','k','v']:
                converted[name.replace('.in_proj_qkv.','.in_proj_'+suffix+'.')]=tensor.clone()
        elif '.lora_B.' in name:
            if tensor.shape[0]!=2*key+value:raise ValueError('Unexpected QKV adapter output width')
            for suffix,part in zip(['q','k','v'],tensor.split([key,key,value],dim=0)):
                converted[name.replace('.in_proj_qkv.','.in_proj_'+suffix+'.')]=part.contiguous()
            a_name=name.replace('.lora_B.','.lora_A.')
            a=weights[a_name].float()
            # Check the actual trained delta on deterministic probe vectors;
            # no gigantic dense B@A matrix is materialized.
            probe=torch.linspace(-1,1,a.shape[1]*2,dtype=torch.float32).reshape(a.shape[1],2)
            expected=tensor.float()@(a@probe)
            actual=torch.cat([converted[name.replace('.in_proj_qkv.','.in_proj_'+s+'.')].float()
                @(converted[a_name.replace('.in_proj_qkv.','.in_proj_'+s+'.')].float()@probe)
                for s in ['q','k','v']],dim=0)
            error=float((actual-expected).abs().max())
            if not torch.allclose(actual,expected,rtol=1e-4,atol=1e-5):
                raise ValueError('Serving QKV export changes the trained delta')
            z_name=name.replace('.in_proj_qkv.','.in_proj_z.')
            if z_name not in weights or weights[z_name].shape[0]!=value:
                raise ValueError('Matching native Z adapter missing')
            checks.append(dict(native=name,max_absolute_error=error,widths=[key,key,value]))
        else:raise ValueError('Unrecognized native QKV adapter tensor')
    if len(checks)!=48:raise ValueError('Expected48 native recurrent QKV adapters')
    config['target_modules']=PACKED_TARGETS
    config['inference_mode']=True
    output.mkdir(parents=True)
    save_file({name:tensor.contiguous() for name,tensor in converted.items()},str(output/'adapter_model.safetensors'),metadata={'format':'pt'})
    (output/'adapter_config.json').write_text(json.dumps(config,indent=2)+'\n')
    report=dict(format='SGLang d00d88efc8d6 GDN four-slice adapter',native_tensor_count=len(weights),
        serving_tensor_count=len(converted),qkv_delta_checks=checks,target_modules=PACKED_TARGETS,
        serving_verified=False,boundary='Actual-weight algebraic export only. Runtime load, routing and gameplay remain required.')
    (output/'export-report.json').write_text(json.dumps(report,indent=2)+'\n')
    report['files']={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p.read_bytes()).hexdigest()) for p in output.iterdir() if p.is_file()}
    return report
