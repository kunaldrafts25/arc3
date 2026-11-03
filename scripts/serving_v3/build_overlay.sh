#!/usr/bin/env bash
# CPU-only, online build. The resulting delta still needs real GPU validation.
set -euo pipefail
SOURCE_FILES="$1"
ROOT=/tmp/hydra-serving-v3
OUT=/kaggle/working/pennyroyal-v3-overlay
mkdir -p "$ROOT" "$OUT/wheels" "$OUT/compiler-wheels" "$OUT/licenses"
exec > >(tee -a /kaggle/working/v3-build.log) 2>&1
trap 'echo "BUILD FAILED at line $LINENO; partial artifacts retained" >&2' ERR
BASE=/kaggle/input/datasets/dfranzen/pennyroyal-v253
if [[ ! -d "$BASE" ]]; then BASE=/kaggle/input/pennyroyal-v253; fi
[[ -d "$BASE/wheels" ]]
NOTEBOOK_PY="$(command -v python)"
"$NOTEBOOK_PY" -c 'import sys; assert sys.version_info[:2]==(3,12); print(sys.version)'
if [[ -n "${HYDRA_REUSE_WHEEL_SHA256:-}" ]]; then
  # Check the attachment before spending time preparing the toolchain.
  "$NOTEBOOK_PY" - "$OUT/wheels" "$HYDRA_REUSE_WHEEL_SHA256" <<'PY'
from hashlib import sha256
from pathlib import Path
import shutil,sys
name='sglang-0.5.19+g560edbdca18a-cp312-cp312-linux_x86_64.whl'
slug='arc-hydra-retained-v3-native-wheel'
roots=[Path('/kaggle/input/datasets/kunalsinghh25')/slug,Path('/kaggle/input')/slug]
# Kaggle strips '+' from uploaded dataset filenames. Verify contents before
# restoring the valid PEP 427 wheel name used by the original build.
matches=list({p.resolve() for root in roots for filename in (name,name.replace('+',''))
              if (p:=root/filename).is_file()})
assert len(matches)==1, f'Expected one retained native wheel, found {matches}'
assert sha256(matches[0].read_bytes()).hexdigest()==sys.argv[2], 'Retained wheel hash mismatch'
shutil.copy2(matches[0],Path(sys.argv[1])/name)
print('Reused hash-verified native runtime wheel',flush=True)
PY
fi
export UV_HTTP_TIMEOUT=300 UV_HTTP_RETRIES=3 UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
export PIP_DEFAULT_TIMEOUT=300 PIP_RETRIES=3 PYTHONNOUSERSITE=1
unset PYTHONPATH UV_SYSTEM_PYTHON
export MAX_JOBS=2 CMAKE_BUILD_PARALLEL_LEVEL=2 CARGO_BUILD_JOBS=2 FLASHINFER_NVCC_THREADS=1
export TORCH_CUDA_ARCH_LIST='12.0+PTX'
cp "$SOURCE_FILES/pins.json" "$OUT/pins.json"
cp "$SOURCE_FILES/cuda_overlay.py" "$SOURCE_FILES/package_overlay.py" "$OUT/"
cp "$SOURCE_FILES/LICENSE.Franzen" "$OUT/licenses/Franzen-Apache-2.0"

# Use the existing offline bundle's native uv; no global Python replacement.
"$NOTEBOOK_PY" - "$BASE" "$ROOT" <<'PY'
from pathlib import Path
from zipfile import ZipFile
import sys
base,root=map(Path,sys.argv[1:])
wheel=next((base/'wheels').glob('uv-*.whl'))
with ZipFile(wheel) as z:
    name=next(n for n in z.namelist() if n.endswith('/uv'))
    p=root/'uv';p.write_bytes(z.read(name));p.chmod(0o755)
PY
UV="$ROOT/uv"

# Frozen micromamba artifact; resolve the compiler packages and retain explicit
# package URLs/versions. This compiler is private experiment infrastructure.
"$NOTEBOOK_PY" - "$SOURCE_FILES/pins.json" "$ROOT" <<'PY'
from hashlib import sha256
import json
from pathlib import Path
from urllib.request import urlopen
import sys
pins=json.loads(Path(sys.argv[1]).read_text())['micromamba']
with urlopen(pins['url'],timeout=120) as response:data=response.read()
assert sha256(data).hexdigest()==pins['sha256'],'micromamba checksum mismatch'
p=Path(sys.argv[2])/'micromamba';p.write_bytes(data);p.chmod(0o755)
PY
export MAMBA_ROOT_PREFIX="$ROOT/mamba"
"$ROOT/micromamba" create -y -p "$ROOT/gcc" --override-channels -c conda-forge 'gxx_linux-64=15'
"$ROOT/micromamba" list -p "$ROOT/gcc" --explicit > "$OUT/compiler-explicit.txt"
export CC="$ROOT/gcc/bin/x86_64-conda-linux-gnu-gcc"
export CXX="$ROOT/gcc/bin/x86_64-conda-linux-gnu-g++"
export CUDAHOSTCXX="$CXX"
"$CXX" --version

# Keep the CUDA 13.3 build toolkit separate from Torch's CUDA-13.0 wheel deps.
"$UV" venv --python "$NOTEBOOK_PY" "$ROOT/compiler"
"$NOTEBOOK_PY" - "$SOURCE_FILES/pins.json" "$OUT/compiler.lock" <<'PY'
import json
from pathlib import Path
import sys
pins=json.loads(Path(sys.argv[1]).read_text())['cuda']
assert all(pins.values())
Path(sys.argv[2]).write_text(''.join(f'{k}=={v}\n' for k,v in pins.items()))
PY
"$UV" pip install --python "$ROOT/compiler/bin/python" -r "$OUT/compiler.lock"
"$ROOT/compiler/bin/python" "$SOURCE_FILES/cuda_overlay.py" "$ROOT/cuda"
export CUDA_HOME="$ROOT/cuda" CUDA_PATH="$ROOT/cuda" CUDACXX="$ROOT/cuda/bin/nvcc"
export PATH="$ROOT/gcc/bin:$ROOT/cuda/bin:$PATH"
export LD_LIBRARY_PATH="$ROOT/gcc/lib:$ROOT/cuda/lib64:${LD_LIBRARY_PATH:-}"
cat > "$ROOT/probe.cu" <<'CUDA'
#include <cuda_runtime.h>
#include <cuda/std/array>
__global__ void probe(float* x) { x[threadIdx.x] = 1.0f; }
CUDA
"$CUDACXX" -ccbin "$CXX" -arch=sm_120f -std=c++17 -cubin "$ROOT/probe.cu" -o "$ROOT/probe.cubin"
echo 'CPU CUDA SM120f compiler probe passed'

# Exact source. Carry only the same inspected INT4 scale-dtype fix used by the
# original notebook; all other runtime changes are upstream release v3.
git clone --depth 1 --branch pennyroyal-v3.0.0 https://github.com/jpezzulli/sglang-rtxpro6000.git "$ROOT/source"
[[ "$(git -C "$ROOT/source" rev-parse HEAD)" == 560edbdca18aedae13f71ae20b3984efa4d22633 ]]
"$NOTEBOOK_PY" - "$ROOT/source" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])/'python/sglang/srt/layers/quantization/gptq/schemes/gptq_moe.py'
b=p.read_bytes();assert b.count(b'dtype=torch.half')==2,'Unexpected INT4 scale allocations'
p.write_bytes(b.replace(b'dtype=torch.half',b'dtype=params_dtype'))
PY
git -C "$ROOT/source" diff > "$OUT/int4-compatibility.patch"
cp "$ROOT/source/LICENSE" "$OUT/licenses/sglang-LICENSE"

if [[ -z "${HYDRA_REUSE_WHEEL_SHA256:-}" ]]; then
export CARGO_HOME="$ROOT/cargo" RUSTUP_HOME="$ROOT/rustup"
export PATH="$CARGO_HOME/bin:$PATH"
if ! command -v cargo >/dev/null; then
  curl --fail --location --retry 2 https://sh.rustup.rs -o "$ROOT/rustup-init.sh"
  sh "$ROOT/rustup-init.sh" -y --profile minimal --no-modify-path
fi
cargo --version
export RUSTFLAGS='-C target-cpu=x86-64'
export CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER="$CC"
export SGLANG_BUILD_RUST_EXTS=all SETUPTOOLS_SCM_PRETEND_VERSION_FOR_SGLANG=0.5.19+g560edbdca18a
"$UV" build --wheel "$ROOT/source/python" --python "$NOTEBOOK_PY" -o "$OUT/wheels"
fi

# Install the known working dependency base, then resolve only what the new
# runtime actually needs. Freeze the delta, never ship unpinned online installs.
"$UV" venv --python "$NOTEBOOK_PY" "$ROOT/runtime"
RUNTIME="$ROOT/runtime/bin/python"
"$UV" pip install --python "$RUNTIME" --no-index --find-links "$BASE/wheels" -r "$BASE/requirements.lock"
"$RUNTIME" "$SOURCE_FILES/package_overlay.py" freeze "$ROOT/base-packages.json"
"$UV" pip install --python "$RUNTIME" --prerelease=allow --index-strategy unsafe-best-match \
  --extra-index-url https://docs.sglang.ai/whl/cu130/ \
  --constraint "$ROOT/source/docker/pennyroyal/constraints.txt" "$OUT"/wheels/sglang-*.whl
# The umbrella cache declares every architecture provider. Resolve these too:
# --no-deps left five missing requirements and failed v1's dependency check.
"$UV" pip install --python "$RUNTIME" --index-url https://flashinfer.ai/whl/cu130 \
  'flashinfer-jit-cache==0.7.0.post1+cu130' 'flashinfer-jit-cache-sm120f==0.7.0.post1+cu130'
"$UV" pip install --python "$RUNTIME" --no-deps --index-url https://flashinfer.ai/whl \
  'flashinfer-cubin==0.7.0.post1'
# Kaggle's inherited sitecustomize imports wrapt, which the base lock omits.
# Include it in the frozen overlay rather than tolerating startup import errors.
"$UV" pip install --python "$RUNTIME" 'wrapt==1.17.3'
"$RUNTIME" -m pip check
# The compiler-only environment has no cuBLAS. Use the already-installed Torch
# dependency's development files, retaining the separate 13.3 compiler headers.
"$RUNTIME" "$SOURCE_FILES/cuda_overlay.py" "$ROOT/cuda" --libraries-only
cat > "$ROOT/library-probe.cu" <<'CUDA'
#include <cuda_runtime.h>
#include <cuda/std/array>
#include <cublasLt.h>
#include <nvrtc.h>
__global__ void library_probe(float* x) { x[threadIdx.x] = 1.0f; }
CUDA
"$CUDACXX" -ccbin "$CXX" -arch=sm_120f -std=c++17 -cubin "$ROOT/library-probe.cu" -o "$ROOT/library-probe.cubin"
echo 'CPU CUDA library-header compilation probe passed'
# Exercise the same host-library search paths and linker inputs as FlashInfer.
# Do not execute this binary: the CPU builder has no CUDA driver/device.
cat > "$ROOT/link-probe.cpp" <<'CPP'
#include <cuda_runtime_api.h>
#include <cuda.h>
#include <nvrtc.h>
int main() {
    int runtime_version=0, major=0, minor=0;
    return int(cudaRuntimeGetVersion(&runtime_version))
        + int(nvrtcVersion(&major, &minor)) + int(cuInit(0));
}
CPP
"$CXX" "$ROOT/link-probe.cpp" -I"$CUDA_HOME/include" \
  -L"$CUDA_HOME/lib64" -L"$CUDA_HOME/lib64/stubs" \
  -Wl,-rpath-link,"$CUDA_HOME/lib64" -lcudart -lcuda -lnvrtc -o "$ROOT/link-probe"
echo 'CPU CUDA host-link probe passed (not executed)'
"$RUNTIME" "$ROOT/source/scripts/pennyroyal/flashinfer/install.py"
"$RUNTIME" "$ROOT/source/scripts/pennyroyal/flashinfer/install.py" --check
"$RUNTIME" "$SOURCE_FILES/package_overlay.py" package "$OUT" "$ROOT/base-packages.json"
"$RUNTIME" -m pip download --only-binary=:all: --no-deps -r "$OUT/download.lock" \
  --extra-index-url https://docs.sglang.ai/whl/cu130/ \
  --extra-index-url https://flashinfer.ai/whl/cu130 \
  --extra-index-url https://flashinfer.ai/whl -d "$OUT/wheels"
"$RUNTIME" -m pip download --only-binary=:all: --no-deps -r "$OUT/compiler.lock" -d "$OUT/compiler-wheels"

# A fresh offline reinstall is mandatory. A completed build without these
# checks is not an installable runtime, and none of this proves GPU inference.
"$UV" venv --python "$NOTEBOOK_PY" "$ROOT/verify"
VERIFY="$ROOT/verify/bin/python"
"$UV" pip install --python "$VERIFY" --no-index --find-links "$BASE/wheels" -r "$BASE/requirements.lock"
"$UV" pip install --python "$VERIFY" --no-index --find-links "$BASE/wheels" --find-links "$OUT/wheels" \
  -r "$OUT/requirements-overlay.lock"
"$VERIFY" -m pip check
"$VERIFY" "$ROOT/source/scripts/pennyroyal/flashinfer/install.py" --check
"$VERIFY" -c 'import sglang,torch,flashinfer; print(sglang.__version__,torch.__version__,flashinfer.__version__)'
tar -C "$ROOT" -czf "$OUT/gcc-toolchain.tar.gz" gcc
"$NOTEBOOK_PY" - "$ROOT" "$OUT" <<'PY'
import json,shutil,sys
from pathlib import Path
root,out=map(Path,sys.argv[1:])
for p in (root/'mamba/pkgs').glob('*/info/licenses'):
    shutil.copytree(p,out/'licenses/toolchain'/p.parent.parent.name,dirs_exist_ok=True)
provenance=dict(source_commit='560edbdca18aedae13f71ae20b3984efa4d22633',
                base_dataset='dfranzen/pennyroyal-v253',
                validation='CPU build, compiled SM120f module and fresh offline installation; GPU inference unverified',
                int4_patch='Daniel Franzen INT4 scale-dtype compatibility fix, Apache-2.0')
import os
provenance['reused_native_wheel_sha256']=os.environ.get('HYDRA_REUSE_WHEEL_SHA256')
(out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
PY
"$RUNTIME" "$SOURCE_FILES/package_overlay.py" manifest "$OUT"
echo 'CPU_BUILD_AND_OFFLINE_INSTALL_VERIFIED; GPU_INFERENCE_NOT_TESTED' > "$OUT/BUILD_COMPLETE"
echo 'Pennyroyal v3 overlay build complete; GPU validation still required'
