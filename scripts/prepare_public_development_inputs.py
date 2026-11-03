"""Package only public practice environments and hash-verified public PyPI wheels.

No competition-only or evaluation-game inputs, credentials, solutions or model
weights are included. Game implementations are copied, never inspected by the
agent. Output is for a private development dataset, not a competition entry.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import shutil

from packaging.utils import parse_wheel_filename
import requests

ROOT=Path(__file__).resolve().parents[1]


def prepare():
    output=ROOT/'reference/public-development-inputs';output.mkdir(exist_ok=True)
    wheels=output/'arc_agi_3_wheels';wheels.mkdir(exist_ok=True)
    names=json.loads((ROOT/'reference/kaggle/file-names.json').read_text(encoding='utf-8'))
    names=[Path(n).name for n in names if n.startswith('arc_agi_3_wheels/') and n.endswith('.whl')]
    def download(name):
        package,version,_,_=parse_wheel_filename(name)
        url=f'https://pypi.org/pypi/{package}/{version}/json'
        response=requests.get(url,timeout=60);response.raise_for_status()
        matches=[f for f in response.json()['urls'] if f['filename']==name]
        if len(matches)!=1:raise ValueError('Public PyPI artifact not found: '+name)
        info=matches[0];expected=info['digests']['sha256'];path=wheels/name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest()!=expected:
            if not info['url'].startswith('https://files.pythonhosted.org/'):raise ValueError('Unexpected artifact host')
            data=requests.get(info['url'],timeout=120);data.raise_for_status()
            if sha256(data.content).hexdigest()!=expected:raise ValueError('Wheel digest mismatch')
            path.write_bytes(data.content)
        return dict(file=name,sha256=expected,source=info['url'],bytes=path.stat().st_size)
    with ThreadPoolExecutor(max_workers=4) as pool:artifacts=list(pool.map(download,names))
    benchmark=json.loads((ROOT/'reports/kaggle/ultimate-candidate-v3/benchmark.json').read_text(encoding='utf-8'))
    ids=sorted(g['game_id'] for g in benchmark['game_runs']);assert len(ids)==25 and len(set(ids))==25
    games=[]
    for game in ids:
        prefix,version=game.split('-',1);source=ROOT/'environment_files'/prefix/version
        metadata=json.loads((source/'metadata.json').read_text(encoding='utf-8'))
        if metadata['game_id']!=game:raise ValueError('Unexpected public practice version')
        target=output/'environment_files'/prefix/version;target.mkdir(exist_ok=True,parents=True)
        for name in ('metadata.json',prefix+'.py'):
            shutil.copyfile(source/name,target/name)
            games.append(dict(file=str((target/name).relative_to(output)).replace('\\','/'),sha256=sha256((target/name).read_bytes()).hexdigest()))
    manifest=dict(scope='25 public practice environments only; not evaluation games',game_ids=ids,
        environment_files=games,pypi_wheels=artifacts,source='Public ARC Arcade practice downloads and official PyPI releases')
    (output/'public-input-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    metadata=dict(id='kunalsinghh03/arc3-public-development-inputs',title='ARC3 Public Development Inputs',
        subtitle='Public practice environments and pinned public toolkit wheels',
        description='Private development mirror of the 25 public practice games and official PyPI toolkit artifacts. No private evaluation games, credentials or trained solutions.',
        licenses=[dict(name='Apache 2.0')])
    (output/'dataset-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(output),public_games=len(ids),wheels=len(artifacts),wheel_bytes=sum(a['bytes'] for a in artifacts))))


if __name__=='__main__':prepare()
