"""Install a CPU-verified overlay into a stopped, isolated model environment.

This does not test GPU inference and never installs from an online index.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import os
import platform
import shlex
import socket
import subprocess
import sys
import tarfile

PREFIX=Path('/tmp/hydra-serving-v3')
EXPECTED_COMMIT='560edbdca18aedae13f71ae20b3984efa4d22633'


def digest(path):
    result=sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):
            result.update(block)
    return result.hexdigest()


def manifest_path(root, relative):
    value=PurePosixPath(relative)
    if value.is_absolute() or '..' in value.parts or '\\' in relative:
        raise ValueError(f'Unsafe manifest path: {relative}')
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Manifest path escapes overlay: {relative}')
    return path


def verify_bundle(root):
    if (root/'BUILD_COMPLETE').read_text().strip()!='CPU_BUILD_AND_OFFLINE_INSTALL_VERIFIED; GPU_INFERENCE_NOT_TESTED':
        raise ValueError('Missing CPU build/offline-install completion evidence')
    provenance=json.loads((root/'provenance.json').read_text())
    if provenance['source_commit']!=EXPECTED_COMMIT:
        raise ValueError('Unexpected runtime source commit')
    manifest=json.loads((root/'manifest.json').read_text())['files']
    for relative, expected in manifest.items():
        path=manifest_path(root,relative)
        if path.stat().st_size!=expected['bytes'] or digest(path)!=expected['sha256']:
            raise ValueError(f'Overlay checksum mismatch: {relative}')
    required={'gcc-toolchain.tar.gz','compiler.lock','requirements-overlay.lock','cuda_overlay.py'}
    if not required <= manifest.keys():
        raise ValueError('Overlay manifest is incomplete')
    return digest(root/'manifest.json')


def run(command, env):
    print('$',shlex.join(map(str,command)),flush=True)
    subprocess.run(list(map(str,command)),env=env,check=True)


def install(root, base, venv, uv, port):
    if sys.platform!='linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,12):
        raise RuntimeError('Overlay requires Linux x86_64 with Python 3.12')
    # Triton's host-C extension includes Kaggle's system Python headers. The
    # Conda compiler sysroot does not search Debian's multiarch header paths.
    host_cc=Path('/usr/bin/gcc')
    if not host_cc.is_file():
        raise RuntimeError('System host-C compiler required for Python extensions')
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',port))==0:
            raise RuntimeError('Model server is already listening; refusing an in-place update')
    manifest_hash=verify_bundle(root)
    env=dict(os.environ,UV_OFFLINE='1',UV_PYTHON_DOWNLOADS='never',PYTHONNOUSERSITE='1',
             HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    env.pop('PYTHONPATH',None)
    compiler=PREFIX/'compiler'
    gcc=PREFIX/'gcc'
    cuda=PREFIX/'cuda'
    marker=PREFIX/'overlay-installed.json'
    identity=dict(manifest_sha256=manifest_hash,venv=str(venv.resolve()))
    if marker.exists():
        if json.loads(marker.read_text())!=identity:
            raise RuntimeError('Another overlay is already installed in this prefix')
    else:
        if any(p.exists() for p in (compiler,gcc,cuda)):
            raise RuntimeError('Partial toolchain prefix exists; use a fresh notebook runtime')
        PREFIX.mkdir(parents=True,exist_ok=True)
        with tarfile.open(root/'gcc-toolchain.tar.gz','r:gz') as archive:
            archive.extractall(PREFIX,filter='data')
        if not (gcc/'bin/x86_64-conda-linux-gnu-g++').is_file():
            raise RuntimeError('Compiler archive did not contain the expected prefix')
        run([uv,'venv','--python',sys.executable,compiler],env)
        run([uv,'pip','install','--python',compiler/'bin/python','--no-index',
             '--find-links',root/'compiler-wheels','-r',root/'compiler.lock'],env)
        run([compiler/'bin/python',root/'cuda_overlay.py',cuda],env)
        run([uv,'pip','install','--python',venv/'bin/python','--no-index',
             '--find-links',base/'wheels','--find-links',root/'wheels',
             '-r',root/'requirements-overlay.lock'],env)
    env.update(CC=str(host_cc),
               CXX=str(gcc/'bin/x86_64-conda-linux-gnu-g++'),
               CUDAHOSTCXX=str(gcc/'bin/x86_64-conda-linux-gnu-g++'),
               CUDA_HOME=str(cuda),CUDA_PATH=str(cuda),CUDACXX=str(cuda/'bin/nvcc'),
               PATH=f'{gcc}/bin:{cuda}/bin:{venv}/bin:'+env.get('PATH',''),
               LD_LIBRARY_PATH=f'{gcc}/lib:{cuda}/lib64:'+env.get('LD_LIBRARY_PATH',''))
    run([venv/'bin/python','-m','pip','check'],env)
    run([venv/'bin/python',root/'cuda_overlay.py',cuda,'--libraries-only'],env)
    run([cuda/'bin/nvcc','--version'],env)
    run([venv/'bin/python','-c',
         'import importlib.metadata as m; '
         'assert m.version("sglang")=="0.5.19+g560edbdca18a"; '
         'assert m.version("flashinfer-python")=="0.7.0.post1"; '
         'from pathlib import Path; import flashinfer; '
         'assert (Path(flashinfer.__file__).parent/"data/aot/fused_moe_120/fused_moe_120.so").is_file(); '
         'print("Runtime overlay installed; GPU inference still unverified")'],env)
    # Exercise the exact Triton driver-helper compilation that failed v1,
    # before spending time loading the large model checkpoint.
    run([venv/'bin/python','-c',
         'import torch; assert torch.cuda.is_available(); '
         'from triton.runtime import driver; '
         'print("Triton CUDA host-extension probe passed; device",driver.active.get_current_device())'],env)
    marker.write_text(json.dumps(identity,indent=2)+'\n')
    keys=('CC','CXX','CUDAHOSTCXX','CUDA_HOME','CUDA_PATH','CUDACXX','PATH','LD_LIBRARY_PATH')
    return {key:env[key] for key in keys}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for flag in ('overlay','base','venv','uv','environment-output'):
        parser.add_argument('--'+flag,type=Path,required=True)
    parser.add_argument('--port',type=int,default=8001)
    args=parser.parse_args()
    environment=install(args.overlay,args.base,args.venv,args.uv,args.port)
    args.environment_output.write_text(json.dumps(environment,indent=2)+'\n')
