"""Package the CPU-only online builder, separate from competition notebooks."""
from hashlib import sha256
import argparse
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def build(reuse_wheel_sha256=None):
    if reuse_wheel_sha256 is not None and not re.fullmatch('[0-9a-f]{64}',reuse_wheel_sha256):
        raise ValueError('A real lowercase SHA-256 of the retained wheel is required')
    source_dir=ROOT/'scripts/serving_v3'
    sources={p.name:p.read_text(encoding='utf-8') for p in sorted(source_dir.iterdir()) if p.is_file()}
    sources['LICENSE.Franzen']=(ROOT/'baselines/duck_m2/LICENSE').read_text(encoding='utf-8')
    source="""from pathlib import Path
import subprocess
import sys
import os
"""
    if reuse_wheel_sha256:
        source+=f"os.environ['HYDRA_REUSE_WHEEL_SHA256']={reuse_wheel_sha256!r}\n"
    source+='BUILD_SOURCES = '+repr(sources)+'\n'
    source+='''stage=Path('/kaggle/working/build-src')
stage.mkdir(parents=True,exist_ok=True)
for name,content in BUILD_SOURCES.items():
    (stage/name).write_text(content,encoding='utf-8')
subprocess.run(['bash',str(stage/'build_overlay.sh'),str(stage)],check=True)
'''
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='markdown',metadata={},source=(
            '# ARC-Hydra: CPU build of Pennyroyal v3\n\n'
            'Private infrastructure experiment. Builds the pinned upstream runtime and '
            'accepted FlashInfer kernels, then verifies a fresh offline installation. '
            '**GPU inference, throughput, agent quality and leaderboard performance remain untested.**\n\n'
            'Runtime: John Pezzulli / SGLang contributors. INT4 compatibility and CUDA '
            'overlay adaptation: Daniel Franzen, Apache-2.0; original notices retained. '
            'No models or game data are needed by this builder.')),
            dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None)])
    base=json.loads((ROOT/'baselines/duck_m2/upstream-metadata.json').read_text())
    metadata=dict(id='kunalsinghh25/arc-hydra-pennyroyal-v3-build',title='ARC Hydra Pennyroyal v3 Build',
                  code_file='build.ipynb',language='python',kernel_type='notebook',is_private=True,
                  enable_gpu=False,enable_tpu=False,enable_internet=True,
                  dataset_sources=['dfranzen/pennyroyal-v253'],model_sources=[],kernel_sources=[],competition_sources=[],
                  docker_image=base['docker_image'])
    if reuse_wheel_sha256:
        metadata['id']='kunalsinghh25/arc-hydra-pennyroyal-v3-dependency-repair'
        metadata['title']='ARC Hydra Pennyroyal v3 Dependency Repair'
        metadata['dataset_sources'].append('kunalsinghh25/arc-hydra-retained-v3-native-wheel')
    return notebook,metadata,sources


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--reuse-wheel-sha256')
    args=parser.parse_args()
    notebook,metadata,sources=build(args.reuse_wheel_sha256)
    destination=ROOT/'notebooks'/('serving_v3_repair' if args.reuse_wheel_sha256 else 'serving_v3_build')
    destination.mkdir(parents=True,exist_ok=True)
    for name,data in [('build.ipynb',notebook),('kernel-metadata.json',metadata),
                      ('source-manifest.json',{name:sha256(content.encode()).hexdigest() for name,content in sources.items()})]:
        (destination/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print('Created private CPU builder with internet enabled; no competition attachment or models')
