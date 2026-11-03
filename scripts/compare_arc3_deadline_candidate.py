"""Compare the deadline screen with frozen real-game trajectory prefixes."""
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean

from scripts.compare_arc3_prediction_runs import checkpoint, usage
from scripts.run_arc3_deadline_candidate import ROOT, OUTPUT, DIRECTORY, validate


def aggregate(rows):
    return dict(score=mean(v['score'] for v in rows.values()),
        levels=sum(v['levels'] for v in rows.values()),
        actions=sum(v['actions'] for v in rows.values()),
        generation_charges=sum(v['generated_tokens'] for v in rows.values()))


def compare():
    manifest=validate()
    state=json.loads((DIRECTORY/'state.json').read_text())
    launch=json.loads((OUTPUT/'launch.json').read_text())
    if (state['phase']!='evaluation_complete' or state['kernel_status']!='COMPLETE'
            or launch['phase']!='accepted' or launch['files']!=manifest['files']
            or launch['hard_session_timeout_seconds']!=7200
            or not state['analysis']['model_gameplay_verified'] or state['analysis']['games']!=25):
        raise ValueError('Completed, frozen, substantive 25-game screen required')
    paths=dict(candidate=OUTPUT/'benchmark.json',
        memory=ROOT/'reports/kaggle/general-learner-v1/benchmark.json',
        prediction=ROOT/'reports/kaggle/prediction-matched-prediction-v1/benchmark.json')
    runs={name:json.loads(path.read_text(encoding='utf-8')) for name,path in paths.items()}
    durations={name:(datetime.fromisoformat(run['end_time'])-datetime.fromisoformat(run['start_time'])).total_seconds()
               for name,run in runs.items()}
    seconds=min(durations.values())
    rows={name:checkpoint(run,seconds) for name,run in runs.items()}
    if not all(set(v)==set(rows['candidate']) for v in rows.values()):
        raise ValueError('Game identities differ')
    summary={name:aggregate(v) for name,v in rows.items()}
    notes=[]
    for path in OUTPUT.rglob('*.study.events.jsonl'):
        events=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        notes.append(dict(game=path.name.split('_p0_')[0],changes=len(events)))
    if not notes:
        raise ValueError('No actual memory telemetry; inspect completed agent before promotion')
    adoption=json.loads((OUTPUT/'prediction-adoption.json').read_text())
    if adoption['audit_errors'] or adoption['source_origin']!='model':
        raise ValueError('Prediction telemetry audit failed')
    # A conservative deadline choice, not a statistical significance claim.
    favorable=(summary['candidate']['score']>=summary['memory']['score']
        and summary['candidate']['levels']>=summary['memory']['levels']
        and summary['candidate']['score']>=summary['prediction']['score'])
    per_game=[]
    for game in sorted(rows['candidate']):
        per_game.append(dict(game=game,**{name:v[game] for name,v in rows.items()}))
    result=dict(common_gameplay_seconds=seconds,durations_seconds=durations,
        common_time=summary,candidate_full_screen=state['analysis'],
        memory_games=len(notes),memory_changes=sum(v['changes'] for v in notes),
        tool_usage=usage(OUTPUT),prediction_adoption=adoption,
        qualifies_for_deadline_submission=favorable,
        decision='Submit the new validated FlashNext composition' if favorable else 'Hold for explicit review; screen did not beat both retained alternatives',
        decision_basis='Candidate must match/exceed historical memory completion and score, and exceed/equal historical prediction score, at their common actual gameplay duration. All25 substantive games, successful lifecycle, exact executed package/extensions and actual memory events are prerequisite checks.',
        limitations='One stochastic public draw, different scheduling horizons, and already inspected games. No causal isolation, unseen-game guarantee, or official-score prediction. Zero prediction use must not be credited as a mechanism improvement.',
        hashes={name:sha256(path.read_bytes()).hexdigest() for name,path in paths.items()},
        per_game=per_game)
    (DIRECTORY/'comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    result=compare()
    print(json.dumps({k:v for k,v in result.items() if k not in ('per_game','tool_usage','prediction_adoption')},indent=2))
