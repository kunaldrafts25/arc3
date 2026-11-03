import pytest
from pathlib import Path
from uuid import uuid4
from scripts.build_duck_notebook import build
from scripts.swift_model_view import prepare


def test_swift_replaces_only_the_target_and_preserves_original_serving():
    baseline,_,_=build('benchmark')
    notebook,metadata,provenance=build('benchmark',model_variant='swift-1.5')
    def serving(n):
        return next(c['source'] for c in n['cells'] if c['source'].startswith('# Paste this entire file'))
    assert serving(notebook)==serving(baseline)
    configuration=next(c['source'] for c in notebook['cells'] if '# ARC-Hydra Swift split-checkpoint view.' in c['source'])
    compile(configuration.split('# ARC-Hydra Swift split-checkpoint view.\n',1)[1],'swift-notebook','exec')
    refs=metadata['model_sources']
    assert len(refs)==3 and sum('phuongncn/' in r for r in refs)==2
    assert any('albucino' in r for r in refs)
    assert not any('intel-qwen' in r for r in refs)
    assert metadata['id']=='kunalsinghh25/arc-hydra-duck-swift'
    assert metadata['enable_internet'] is False
    assert provenance['public_runtime_seconds']==7200
    assert len(provenance['model_manifest']['files'])==95
    with pytest.raises(ValueError,match='separately'):
        build(model_variant='swift-1.5',agent_variant='rolling-summary')


def test_missing_model_part_is_rejected_before_creating_a_view():
    destination=Path(__file__).resolve().parents[1]/'test-artifacts'/('swift-'+uuid4().hex)
    with pytest.raises(ValueError,match='Missing or wrong-sized'):
        prepare({'a':destination/'missing-a','b':destination/'missing-b'},destination,
                {'files':{'model.safetensors':{'part':'a','bytes':1024}}})
    assert not destination.exists()
