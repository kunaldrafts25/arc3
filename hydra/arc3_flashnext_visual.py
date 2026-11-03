"""Restore the pinned visual encoder when training a text-GGUF backbone."""
from hashlib import sha256
import json
from pathlib import Path


def restore_visual_weights(model,checkpoint,device='cuda:0'):
    """Load only exact named visual tensors, without a second full checkpoint.

    This does not infer equivalence between different quantized backbones. It
    requires the caller to use the pinned incumbent config and input revision.
    """
    import torch
    from safetensors import safe_open
    from accelerate.utils import set_module_tensor_to_device
    checkpoint=Path(checkpoint)
    index=json.loads((checkpoint/'model.safetensors.index.json').read_text())['weight_map']
    visual={name:parameter for name,parameter in model.named_parameters() if name.startswith('model.visual.')}
    if not visual:raise ValueError('Native multimodal model exposes no expected visual encoder')
    missing=sorted(set(visual)-index.keys())
    if missing:raise ValueError('Pinned incumbent lacks native visual tensors: '+str(missing[:5]))
    grouped={}
    for name in visual:grouped.setdefault(index[name],[]).append(name)
    verified=[]
    with torch.no_grad():
        for shard,names in sorted(grouped.items()):
            source=(checkpoint/shard).resolve()
            if not source.is_relative_to(checkpoint.resolve()):raise ValueError('Visual shard escapes checkpoint root')
            with safe_open(source,framework='pt',device='cpu') as handle:
                for name in sorted(names):
                    original=handle.get_tensor(name)
                    parameter=visual[name]
                    if not original.is_floating_point() or original.shape!=parameter.shape:
                        raise ValueError('Visual tensor dtype/shape differs from native config: '+name)
                    expected=original.to(dtype=parameter.dtype).contiguous()
                    set_module_tensor_to_device(model,name,device,value=expected,dtype=parameter.dtype)
                    loaded=model.get_parameter(name)
                    if loaded.device.type=='meta' or not loaded.detach().cpu().equal(expected):
                        raise ValueError('Actual loaded visual tensor differs: '+name)
                    loaded.requires_grad_(False)
                    digest=sha256(expected.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest()
                    verified.append(dict(name=name,shape=list(expected.shape),dtype=str(expected.dtype),
                        source_shard=shard,loaded_tensor_sha256=digest))
                    del original,expected
    # This encoder is deliberately frozen; keep all of its tensors on the
    # requested device even when the backbone uses disk-backed n-gram rows.
    if any(parameter.requires_grad for name,parameter in model.named_parameters() if name.startswith('model.visual.')):
        raise ValueError('Visual encoder unexpectedly trainable')
    return dict(tensors=len(verified),source_shards=len(grouped),verified_tensors=verified,
        boundary='Exact source-to-model visual tensor equality only. Native processor/full-model CUDA forward and actual gameplay remain required.')
