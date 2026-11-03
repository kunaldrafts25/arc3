from pathlib import Path
from uuid import uuid4

import pytest

from scripts.resolve_kaggle_inputs import resolve_inputs


def inputs(legacy):
    root=Path(__file__).resolve().parents[1]/'test-artifacts'/('mounts-'+uuid4().hex)
    root.mkdir(parents=True)
    values=dict(WHEELHOUSE_DIR=str(root/'datasets/owner/wheels'),
                ORIG_BUNDLE_DIR=str(root/'datasets/owner/source'),
                MODEL_DIR=str(root/'models/owner/target/transformers/default/1'),
                DRAFT_MODEL_DIR=str(root/'models/owner/draft/transformers/default/1'),
                COMPETITION_WHEELHOUSE=str(root/'competitions/contest/arc_agi_3_wheels'))
    for key,path in values.items():
        path=Path(path)
        if legacy:
            parent=(root/'datasets/owner' if '/datasets/' in path.as_posix() else
                    root/'models/owner' if '/models/' in path.as_posix() else root/'competitions')
            path=root/path.relative_to(parent)
        marker=('requirements.lock' if key=='WHEELHOUSE_DIR' else
                'src/ARC3-Inference/inference/agent/tool_agent.py' if key=='ORIG_BUNDLE_DIR' else
                'arc_agi-0.9.8-py3-none-any.whl' if key=='COMPETITION_WHEELHOUSE' else 'config.json')
        target=path/marker
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text('{}')
    return root,values


@pytest.mark.parametrize('legacy',[False,True])
def test_exact_inputs_resolve_in_both_layouts(legacy):
    root,values=inputs(legacy)
    resolved=resolve_inputs(values,root)
    assert all(Path(path).is_dir() for path in resolved.values())
    assert (resolved!=values)==legacy


def test_missing_model_fails_before_expensive_startup():
    root,values=inputs(True)
    (root/'target/transformers/default/1/config.json').unlink()
    with pytest.raises(FileNotFoundError,match='MODEL_DIR not mounted'):
        resolve_inputs(values,root)


def test_packaged_wheel_and_public_environment_paths_use_resolver():
    from scripts.build_ultimate_notebook import package
    notebook,_,_=package()
    for cell in notebook['cells']:
        if cell['cell_type']!='code' or cell['source'].startswith('import json\nimport os'):
            continue
        assert '/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels' not in cell['source']
    install=next(c['source'] for c in notebook['cells'] if c['source'].startswith('# Install the ARC runtime'))
    assert 'COMPETITION_WHEELHOUSE' in install
    run=next(c['source'] for c in notebook['cells'] if c['source'].startswith("print('Starting benchmark...')"))
    assert 'Path(COMPETITION_WHEELHOUSE).parent' in run
