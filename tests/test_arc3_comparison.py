from copy import deepcopy
import pytest
from scripts.compare_arc3_prediction_runs import checkpoint


def trace():
    return dict(start_time='2026-11-01T00:00:00',game_runs=[dict(game_id='independent-fixture',
        started_at='2026-11-01T00:00:05',actions_per_level=[2,3],base_actions_per_level=[1,3],
        levels_completed=2,final_score=75,final_generated_tokens=7,final_wallclock_seconds=50,
        history=[dict(wallclock_seconds=t,generated_tokens=10) for t in (10,20,30,35,40)])])


def test_global_time_offset_completion_boundary_and_terminal_generation_charge():
    raw=trace()
    assert checkpoint(raw,24)['independent-fixture']['score']==0
    first=checkpoint(raw,25)['independent-fixture']
    assert first['levels']==1 and first['actions']==2 and first['score']==pytest.approx(25/3)
    final=checkpoint(raw,45)['independent-fixture']
    assert final['levels']==2 and final['score']==75 and final['generated_tokens']==50
    assert checkpoint(raw,55)['independent-fixture']['generated_tokens']==57


def test_invalid_recording_cannot_certify_a_completed_prefix():
    raw=trace();raw['game_runs'][0]['history'][0]['wallclock_seconds']=30
    with pytest.raises(ValueError,match='chronological'):checkpoint(raw,25)
    raw=trace();raw['game_runs'].append(deepcopy(raw['game_runs'][0]))
    with pytest.raises(ValueError,match='Duplicate'):checkpoint(raw,55)
    raw=trace();raw['game_runs'][0]['final_score']=100
    with pytest.raises(ValueError,match='reconcile'):checkpoint(raw,55)
