"""Diagnose completed public gameplay; no hidden-game performance inferred."""
from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]


def score(counts,baselines,completed):
    n=len(baselines);den=n*(n+1)/2
    return min(sum((i+1)*min(115,100*(b/counts[i])**2) for i,b in enumerate(baselines) if i<completed and counts[i]>0)/den,
               100*completed*(completed+1)/2/den)


def audit():
    directory=ROOT/'reports/kaggle/general-learner-v1'
    raw=json.loads((directory/'benchmark.json').read_text(encoding='utf-8'))
    previous=json.loads((ROOT/'reports/kaggle/ultimate-candidate-v3/benchmark.json').read_text(encoding='utf-8'))
    before={g['game_id']:g for g in previous['game_runs']}
    start=datetime.fromisoformat(raw['start_time'])
    curve={}
    for t in (1800,3600,7200,14400,21600,28800,32400):
        scores=[];levels=0;tokens=0;actions=0
        for g in raw['game_runs']:
            offset=(datetime.fromisoformat(g['started_at'])-start).total_seconds()
            selected=[a for a in g['history'] if offset+a['wallclock_seconds']<=t]
            offset_action=0;completed=0
            for count in g['actions_per_level'][:g['levels_completed']]:
                offset_action+=count
                if offset_action<=len(selected):completed+=1
            counts=g['actions_per_level']
            scores.append(score(counts,g['base_actions_per_level'],completed))
            levels+=completed;actions+=len(selected)
            tokens+=sum(a['generated_tokens'] for a in selected)
            if offset+g['final_wallclock_seconds']<=t:tokens+=g['final_generated_tokens']
        curve[str(t)]=dict(mean_public_score=mean(scores),levels=levels,actions=actions,generated_tokens=tokens)
    games=[]
    for g in raw['game_runs']:
        assert abs(score(g['actions_per_level'],g['base_actions_per_level'],g['levels_completed'])-g['final_score'])<1e-8
        k=g['levels_completed'];n=g['number_of_levels'];counts=g['actions_per_level']
        ceiling=100*k*(k+1)/(n*(n+1))
        last_completion_index=sum(counts[:k])
        last_progress=g['history'][last_completion_index-1]['wallclock_seconds'] if last_completion_index else 0
        games.append(dict(game_id=g['game_id'],state=g['state'],levels=k,total_levels=n,
            score=g['final_score'],delta_vs_previous=g['final_score']-before[g['game_id']]['final_score'],
            completion_ceiling=ceiling,efficiency_gap=ceiling-g['final_score'],
            actions_on_unsolved_level=counts[k] if k<n and len(counts)>k else 0,
            seconds_since_last_completion=g['final_wallclock_seconds']-last_progress if k<n else 0,
            generated_tokens=sum(a['generated_tokens'] for a in g['history'])+g['final_generated_tokens']))
    memory=[]
    for path in sorted((ROOT/'reference/kaggle/general-learner-v1/artifacts').glob('*.study.events.jsonl')):
        rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        notes=rows[-1]['notes'] if rows else {}
        memory.append(dict(game_id=path.name.split('_p0_')[0],changes=len(rows),final_notes=len(notes),
            statuses=dict(Counter(n['status'] for n in notes.values())),sha256=sha256(path.read_bytes()).hexdigest()))
    result=dict(public_score=mean(g['score'] for g in games),levels=sum(g['levels'] for g in games),
        full_wins=sum(g['levels']==g['total_levels'] for g in games),states=dict(Counter(g['state'] for g in games)),
        mean_completion_ceiling=mean(g['completion_ceiling'] for g in games),
        mean_efficiency_gap=mean(g['efficiency_gap'] for g in games),
        actions_on_unsolved_levels=sum(g['actions_on_unsolved_level'] for g in games),
        games_with_memory=len(memory),memory_changes=sum(m['changes'] for m in memory),
        curve=curve,per_game=games,memory=memory,
        official_submission=dict(ref=57726784,score=28.45,previous_best=24.87,delta=3.58,
            notebook_linkage='User reports submitting this notebook parquet; API does not expose version linkage. Own submission file endpoint returned 403; no hidden episode diagnostics were exposed.'),
        boundary='Descriptive public run audit. Different compute and strategy from predecessor; memory use does not establish memory benefit. Development games are not the separate official evaluation games.')
    (directory/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('per_game','memory')},indent=2))


if __name__=='__main__':audit()
