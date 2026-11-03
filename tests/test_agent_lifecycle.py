import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from scripts.agent_lifecycle import gameplay_snapshot, start_lifecycle


def benchmark(actions=1,tokens=0):
    run=SimpleNamespace(actions_per_level=[actions],history=[SimpleNamespace(generated_tokens=tokens)],
                        final_generated_tokens=7 if tokens else 0,levels_completed=0,state='cancelled')
    return SimpleNamespace(game_runs=[run])


def output():
    directory=Path(__file__).resolve().parents[1]/'test-artifacts'
    directory.mkdir(exist_ok=True)
    return directory/('lifecycle-'+uuid4().hex+'.json')


def test_warmup_reset_does_not_establish_model_gameplay():
    report=gameplay_snapshot(benchmark())
    assert report['model_gameplay_games']==0
    finish=start_lifecycle(benchmark(),output(),dict(competition=True))
    with pytest.raises(RuntimeError,match='without substantive'):
        finish()


def test_final_generation_is_accounted_and_zero_levels_can_be_real_gameplay():
    path=output()
    finish=start_lifecycle(benchmark(4,100),path,dict(competition=True))
    report=finish()
    assert report['phase']=='run_finished'
    assert report['gameplay']['generated_tokens']==107
    assert report['gameplay']['model_gameplay_games']==1
    assert report['gameplay']['levels_completed']==0
    assert json.loads(path.read_text())==report


def test_error_keeps_failure_phase_and_does_not_replace_original_exception():
    path=output()
    finish=start_lifecycle(benchmark(),path,dict(competition=False))
    assert finish('TimeoutError')['phase']=='run_failed'
    assert json.loads(path.read_text())['error']=='TimeoutError'
