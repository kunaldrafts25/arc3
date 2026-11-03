from pathlib import Path
from uuid import uuid4

import pytest

from scripts.build_compute_control import package,resolver_source


@pytest.mark.parametrize('legacy',[False,True])
def test_nested_public_wheelhouse_resolves_with_canonical_and_short_mounts(legacy):
    root=Path(__file__).resolve().parents[1]/'test-artifacts'/('compute-input-'+uuid4().hex)
    root.mkdir(parents=True)
    values={};definitions=[('WHEELHOUSE_DIR','runtime','requirements.lock',''),
        ('ORIG_BUNDLE_DIR','source','src/ARC3-Inference/inference/agent/tool_agent.py',''),
        ('COMPETITION_WHEELHOUSE','public','arc_agi-0.9.8.whl','arc_agi_3_wheels')]
    for key,name,marker,suffix in definitions:
        canonical=root/'datasets/owner'/name/suffix
        actual=(root/name/suffix) if legacy else canonical
        file=actual/marker;file.parent.mkdir(parents=True,exist_ok=True);file.write_text('synthetic marker')
        values[key]=str(canonical)
    for key,name in [('MODEL_DIR','target'),('DRAFT_MODEL_DIR','draft')]:
        canonical=root/'models/owner'/name/'transformers/default/1'
        actual=(root/name/'transformers/default/1') if legacy else canonical
        actual.mkdir(parents=True,exist_ok=True);(actual/'config.json').write_text('{}');values[key]=str(canonical)
    ns={};exec(resolver_source(),ns)
    resolved=ns['resolve_inputs'](values,root)
    assert Path(resolved['COMPETITION_WHEELHOUSE']).name=='arc_agi_3_wheels'
    assert all(Path(path).is_dir() for path in resolved.values())


@pytest.mark.parametrize('kind',['control','inspection'])
def test_compute_package_cannot_repeat_unattached_rtx_jobs(kind):
    # These exact source candidates require the competition-only RTX hardware.
    # Public input equivalence does not make that hardware available elsewhere.
    with pytest.raises(ValueError, match='requires an ARC-AGI-3 competition attachment'):
        package(kind)
