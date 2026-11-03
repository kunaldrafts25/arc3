import json
from pathlib import Path
from uuid import uuid4

import pytest

from scripts.analyze_verified_events import analyze


def directory():
    path=Path(__file__).resolve().parents[1]/'test-artifacts'/('events-'+uuid4().hex)
    path.mkdir(parents=True)
    return path


def test_counts_mechanical_adoption_without_confusing_checks_with_score():
    path=directory()
    events=[dict(event='verify',report=dict(verified=True,checked=3,abstained=0,counterexample=None,error=None,scope='abstract-state')),
            dict(event='plan',report=dict(executed=1,stop_reason='prediction_mismatch')),
            dict(event='probe',report=dict(executed=True))]
    (path/'game.hydra-events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    result=analyze(path)
    assert result['counts']['passed_replays']==1
    assert result['counts']['executed_plan_actions']==1
    assert result['counts']['plan_stop:prediction_mismatch']==1
    assert result['counts']['executed_probe_actions']==1
    assert 'not full-grid' in result['boundary']


def test_missing_events_cannot_silently_pass_adoption_gate():
    with pytest.raises(FileNotFoundError,match='unverified'):
        analyze(directory())
