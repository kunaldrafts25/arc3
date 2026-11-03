"""Freeze the built runtime delta and repack modified FlashInfer payloads."""
from email.parser import Parser
from hashlib import sha256
import importlib.metadata as md
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def packages():
    return {re.sub(r'[-_.]+','-',d.metadata['Name']).lower():d.version for d in md.distributions()}


def repack(name, output, compiled=False):
    dist=md.distribution(name)
    stage=Path('/tmp/hydra-serving-v3/repack')/name
    stage.mkdir(parents=True)
    tops={entry.parts[0] for entry in dist.files or () if entry.parts and entry.parts[0]!='..'}
    for top in tops:
        source=Path(dist.locate_file(top))
        if source.is_dir():
            shutil.copytree(source,stage/top,ignore=shutil.ignore_patterns('__pycache__'))
        elif source.is_file():
            shutil.copy2(source,stage/top)
    wheel=next(stage.glob('*.dist-info/WHEEL'))
    if compiled:
        data=Parser().parsestr(wheel.read_text())
        del data['Tag']
        data['Tag']='cp312-cp312-linux_x86_64'
        data.replace_header('Root-Is-Purelib','false')
        wheel.write_text(str(data))
    subprocess.run([sys.executable,'-m','wheel','pack',str(stage),'--dest-dir',str(output)],check=True)


if __name__=='__main__':
    command=sys.argv[1]
    if command=='freeze':
        Path(sys.argv[2]).write_text(json.dumps(packages(),indent=2)+'\n')
    elif command=='package':
        root=Path(sys.argv[2]);base=json.loads(Path(sys.argv[3]).read_text())
        after=packages();delta={k:v for k,v in after.items() if base.get(k)!=v}
        assert delta['sglang']=='0.5.19+g560edbdca18a'
        assert delta['flashinfer-python']=='0.7.0.post1'
        (root/'delta.json').write_text(json.dumps(delta,indent=2)+'\n')
        (root/'requirements-overlay.lock').write_text(''.join(f'{k}=={v}\n' for k,v in sorted(delta.items())))
        custom={'sglang','flashinfer-python','flashinfer-cubin'}
        (root/'download.lock').write_text(''.join(f'{k}=={v}\n' for k,v in sorted(delta.items()) if k not in custom))
        repack('flashinfer-python',root/'wheels',compiled=True)
        repack('flashinfer-cubin',root/'wheels')
    elif command=='manifest':
        root=Path(sys.argv[2]);entries={}
        for path in sorted(root.rglob('*')):
            if path.is_file() and path.name!='manifest.json':
                digest=sha256()
                with path.open('rb') as stream:
                    for block in iter(lambda:stream.read(8*1024*1024),b''):
                        digest.update(block)
                entries[path.relative_to(root).as_posix()]=dict(sha256=digest.hexdigest(),bytes=path.stat().st_size)
        (root/'manifest.json').write_text(json.dumps(dict(files=entries),indent=2)+'\n')
