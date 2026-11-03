from pathlib import Path
import pytest
from scripts.serving_v3.install_overlay import manifest_path
from scripts.build_duck_notebook import build


def test_overlay_manifest_cannot_select_files_outside_its_root():
    root=Path(__file__).resolve().parents[1]
    for value in ('../outside','wheels/../../outside','/outside','wheels\\outside'):
        with pytest.raises(ValueError):
            manifest_path(root,value)
    assert manifest_path(root,'wheels/package.whl')==root/'wheels/package.whl'


def test_runtime_variant_is_offline_isolated_and_checks_real_manifest():
    with pytest.raises(ValueError,match='actual manifest'):
        build(runtime_overlay_dataset='owner/runtime')
    notebook,metadata,provenance=build(runtime_overlay_dataset='owner/runtime',runtime_overlay_sha256='a'*64)
    assert metadata['id']=='kunalsinghh25/arc-hydra-duck-v3-runtime'
    assert 'owner/runtime' in metadata['dataset_sources']
    assert metadata['enable_internet'] is False
    assert provenance['runtime_overlay_manifest_sha256']=='a'*64
    serving=next(c['source'] for c in notebook['cells'] if c['source'].startswith('# Paste this entire file into the launcher cell.'))
    compile(serving,'overlay-launcher','exec')
    assert serving.index('Runtime overlay manifest differs') < serving.index('install_v3_overlay.py')
    assert serving.index('env.update(json.loads(hydra_runtime_env.read_text()))') < serving.index('# ---- launch detached and wait for health ----')


def test_completed_kernel_overlay_is_versioned_and_hash_pinned():
    kernel='owner/completed-builder/6'
    for invalid in ('owner/completed-builder', 'owner/completed-builder/0'):
        with pytest.raises(ValueError,match='exact owner/kernel/version'):
            build(runtime_overlay_kernel=invalid,runtime_overlay_sha256='a'*64)
    with pytest.raises(ValueError,match='one runtime overlay source'):
        build(runtime_overlay_dataset='owner/data',runtime_overlay_kernel=kernel)
    with pytest.raises(ValueError,match='separately'):
        build(runtime_overlay_kernel=kernel,model_variant='swift-1.5')
    notebook,metadata,provenance=build(runtime_overlay_kernel=kernel,runtime_overlay_sha256='a'*64)
    assert metadata['kernel_sources']==[kernel]
    assert metadata['enable_internet'] is False
    assert provenance['runtime_overlay_kernel']==kernel
    serving=next(c['source'] for c in notebook['cells'] if c['source'].startswith('# Paste this entire file into the launcher cell.'))
    compile(serving,'kernel-overlay-launcher','exec')
    assert '/kaggle/input/notebooks/owner/completed-builder/pennyroyal-v3-overlay' in serving
    assert serving.index('Runtime overlay manifest differs') < serving.index('run([sys.executable, hydra_installer')
