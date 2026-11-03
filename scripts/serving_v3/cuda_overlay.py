"""Assemble compiler wheels into a CUDA toolkit prefix.

Adapted from Daniel Franzen's Apache-2.0 make_cuda_overlay.py, distributed
with arc-agi-3-solution. License: baselines/duck_m2/LICENSE.
"""
import importlib.metadata as md
from pathlib import Path
import subprocess
import sys

root=Path(sys.argv[1]).absolute()
libraries_only='--libraries-only' in sys.argv[2:]
root.mkdir(exist_ok=libraries_only)
for dist in sorted(md.distributions(),key=lambda d:d.metadata['Name']):
    name=dist.metadata['Name'].lower().replace('_','-')
    if not name.startswith('nvidia-'):
        continue
    # Keep compiler/runtime/CCCL 13.3 from the separate compiler environment.
    # Add Torch's library headers and libraries (notably cuBLAS) afterwards.
    compiler_packages=('nvidia-cuda-nvcc','nvidia-cuda-crt','nvidia-cuda-runtime','nvidia-cuda-cccl','nvidia-nvvm')
    package=name.removesuffix('-cu13').removesuffix('-cu12')
    if libraries_only and package in compiler_packages:
        continue
    for entry in dist.files or ():
        parts=entry.parts
        if len(parts)<4 or parts[0]!='nvidia' or parts[2] not in ('bin','include','lib','lib64','nvvm'):
            continue
        source=Path(dist.locate_file(entry)).absolute()
        if not source.is_file():
            continue
        dest=root/('lib64' if parts[2]=='lib' else parts[2])/Path(*parts[3:])
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() or dest.is_symlink():
            if dest.read_bytes()!=source.read_bytes():
                raise RuntimeError(f'Conflicting CUDA files: {dest}')
        else:
            dest.symlink_to(source)
if not (root/'lib').is_symlink():
    (root/'lib').symlink_to('lib64')
# CUDA runtime wheels ship the versioned SONAME but may omit the development
# alias needed by the native build's -lcudart linker argument.
cudart=root/'lib64/libcudart.so'
if not cudart.exists() and not cudart.is_symlink():
    versioned=root/'lib64/libcudart.so.13'
    assert versioned.is_file(), 'Missing CUDA 13 runtime library'
    cudart.symlink_to(versioned.name)
assert cudart.is_file(), 'Broken CUDA runtime linker alias'
for name in ('bin/nvcc','bin/ptxas','include/cuda.h','include/cuda_runtime.h',
             'include/crt/host_config.h','nvvm/libdevice/libdevice.10.bc'):
    assert (root/name).is_file(),name
assert (root/'include/cccl/cuda/std').is_dir()
version=subprocess.check_output([str(root/'bin/nvcc'),'--version'],text=True)
assert 'release 13.3,' in version,version
print(version)
if libraries_only:
    assert (root/'include/cublasLt.h').is_file(), 'Missing cuBLAS development headers'
    assert (root/'include/nvrtc.h').is_file(), 'Missing NVRTC development headers'
