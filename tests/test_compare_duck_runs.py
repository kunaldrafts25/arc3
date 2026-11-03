import json
from pathlib import Path
from uuid import uuid4

import pytest

from scripts.compare_duck_runs import compare


def make_run(score=10, game='public-a', duration=7200, tokens=17, state='cancelled'):
    path = Path(__file__).resolve().parents[1] / 'test-artifacts' / ('compare-' + uuid4().hex)
    path.mkdir(parents=True)
    run = dict(game_id=game, state=state, levels_completed=1, number_of_levels=3,
               actions_per_level=[2, 0, 0], final_score=score,
               history=[dict(generated_tokens=tokens), dict(generated_tokens=3)],
               final_generated_tokens=5)
    raw = dict(n_passes=1, start_time='2026-10-27T00:00:00',
               end_time='2026-10-27T02:00:00' if duration == 7200 else '2026-10-27T00:15:00',
               game_weights=None, game_runs=[run])
    (path / 'benchmark.json').write_text(json.dumps(raw), encoding='utf-8')
    return path


def test_comparison_uses_raw_gameplay_and_includes_terminal_generation():
    result = compare(make_run(), make_run(score=20, tokens=20), expected_games=1)
    assert result['delta']['mean_public_score'] == 10
    assert result['delta']['generated_tokens'] == 3
    assert result['control']['summary']['generated_tokens'] == 25
    assert result['games_improved'] == 1
    assert result['per_game'][0]['delta']['score'] == 10
    assert len(result['control']['sha256']) == 64
    assert 'post-readiness' in result['boundary']


@pytest.mark.parametrize('changed, message', [
    ({'game': 'different'}, 'Game sets differ'),
    ({'duration': 900}, 'durations differ'),
    ({'state': 'crashed'}, 'Substantive gameplay missing'),
])
def test_invalid_comparisons_are_rejected(changed, message):
    with pytest.raises(ValueError, match=message):
        compare(make_run(), make_run(**changed), expected_games=1)


def test_small_pilot_cannot_pass_full_game_scope_by_default():
    with pytest.raises(ValueError, match='expected number'):
        compare(make_run(), make_run())
