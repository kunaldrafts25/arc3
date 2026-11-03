"""Package explicit private ARC3 training assets; no credentials or weights."""
from hashlib import sha256
import gzip
from io import BytesIO
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'reports/research/arc3-training-selection-20261101'
OUTPUT=ROOT/'.tmp/arc3-training-pilot-inputs-v1'


def build():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    sources={}
    for context,subdir in [('16k',''),('32k','context-32768')]:
        for split in ['train','validation']:
            sources[context+'/'+split+'.jsonl']=ROOT/'reports/arc3/qwen27-training-pilot'/subdir/(split+'.jsonl')
    for name in ['peft','accelerate']:
        info=json.loads((RESEARCH/(name+'-pypi.json')).read_text())
        wheel=next(x for x in info['urls'] if x['filename'].endswith('py3-none-any.whl'))
        path=RESEARCH/'training-wheels'/wheel['filename']
        if not path.is_file() or sha256(path.read_bytes()).hexdigest()!=wheel['sha256']:
            raise ValueError('Pinned dependency not downloaded: '+wheel['filename'])
    for path in sorted((RESEARCH/'training-wheels').glob('*.whl')):sources['wheels/'+path.name]=path
    sources['arc3_training_collator.py']=ROOT/'hydra/arc3_training_collator.py'
    sources['split.json']=ROOT/'reports/arc3/qwen27-training-pilot/split.json'
    sources['base-requirements.lock']=RESEARCH/'requirements.lock'
    contents={name:path.read_bytes() for name,path in sources.items()}
    manifest=dict(files={name:dict(sha256=sha256(value).hexdigest(),bytes=len(value)) for name,value in contents.items()},
        purpose='Private offline ARC3 training/evaluation inputs. No pretrained weights, credentials, hidden games or test-game examples.',
        attribution='Agent/prompt source Daniel Franzen, Jeroen Cottaar and Tufa Labs, Apache2.0. Our own recorded Qwen agent outputs. Upstream dependency licenses remain inside wheels. Preserve applicable original notices; no blanket relicensing of third-party material.')
    contents['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    archive=BytesIO()
    with tarfile.open(fileobj=archive,mode='w') as tar:
        for name,value in sorted(contents.items()):
            info=tarfile.TarInfo(name);info.size=len(value);info.mtime=0;info.mode=0o644
            tar.addfile(info,BytesIO(value))
    payload=gzip.compress(archive.getvalue(),mtime=0)
    (OUTPUT/'training-pilot-inputs.tar.gz').write_bytes(payload)
    (OUTPUT/'README.md').write_text('# Private ARC3 training pilot assets\n\n'+manifest['purpose']+'\n\n'+manifest['attribution']+'\n\nModel inputs exclude retrospective metadata. Whole-game gradient holdout is not a researcher-blind or hidden competition evaluation. No score benefit or successful training is asserted.\n')
    metadata=dict(id='kunalsinghh25/arc3-training-pilot-inputs-v1',title='ARC3 Training Pilot Inputs v1',
        subtitle='Private reproducible agent-trace and offline dependency inputs',
        description=manifest['purpose']+' '+manifest['attribution'],licenses=[dict(name='other')])
    (OUTPUT/'dataset-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    report=dict(dataset=metadata['id'],private=True,archive_sha256=sha256(payload).hexdigest(),
        archive_bytes=len(payload),manifest=manifest)
    (ROOT/'reports/arc3/qwen27-training-pilot/input-package.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='manifest'},indent=2))

if __name__=='__main__':build()
