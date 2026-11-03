"""Link two pinned public checkpoint parts without copying any model weights."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath


def prepare(parts, destination, manifest):
    parts={key:Path(value).resolve() for key,value in parts.items()}
    destination=Path(destination)
    sources={}
    for name,entry in manifest['files'].items():
        relative=PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name:
            raise ValueError('Invalid checkpoint inventory path')
        source=parts[entry['part']]/name
        if not source.is_file() or source.stat().st_size!=entry['bytes']:
            raise ValueError(f'Missing or wrong-sized checkpoint input: {name}')
        sources[name]=source
    config=json.loads(sources['config.json'].read_text())
    quant=config.get('quantization_config',{})
    if config.get('model_type')!='qwen4_exp' or (quant.get('quant_method'),quant.get('bits'),quant.get('group_size'))!=('auto-round',4,128):
        raise ValueError('Swift checkpoint is not the expected AutoRound INT4 architecture')
    index=json.loads(sources['model.safetensors.index.json'].read_text())
    shards=set(index['weight_map'].values())
    if not shards or not shards <= sources.keys():
        raise ValueError('Split checkpoint index references unavailable weight shards')
    identity=dict(parts={k:str(v) for k,v in parts.items()},
                  inventory=manifest['files'],
                  config_sha256=sha256(sources['config.json'].read_bytes()).hexdigest(),
                  index_sha256=sha256(sources['model.safetensors.index.json'].read_bytes()).hexdigest())
    destination.mkdir(parents=True,exist_ok=True)
    marker=destination/'hydra_model_view.json'
    if marker.exists() and json.loads(marker.read_text())!=identity:
        raise ValueError('Checkpoint view already belongs to different inputs')
    for name,source in sources.items():
        target=destination/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() or target.is_symlink():
            if not target.is_symlink() or target.resolve()!=source:
                raise ValueError(f'Unexpected existing checkpoint file: {name}')
        else:
            target.symlink_to(source)
    marker.write_text(json.dumps(identity,indent=2)+'\n')
    print(f'Swift input view: {len(shards)} shards, {len(sources)} files; weights linked without copying')
    print('Swift mounted config SHA-256:',identity['config_sha256'])
    return str(destination.resolve())
