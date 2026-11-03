"""Freeze matched public experiments separately from the nine-hour final agent."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_inspection_notebook import package as control_package
from scripts.build_prediction_notebook import package as prediction_package

ROOT = Path(__file__).resolve().parents[1]


def build():
    wall, gameplay = 7200, 6600
    plan = dict(version=3,not_before='2026-10-31T00:00:00+00:00',
        expires='2026-11-01T06:00:00+00:00',
        arc2_free_seconds_floor=10800,whole_notebook_seconds=wall,
        public_gameplay_seconds=gameplay,games=25,variants=[])
    for variant in ('control','prediction'):
        if variant == 'control':
            notebook, metadata, provenance = control_package(wall)
            run = next(c for c in notebook['cells'] if c['source'].startswith("print('Starting benchmark...')"))
            anchor = "_hydra_context['games'] = len(bm.games)"
            assert run['source'].count(anchor) == 1
            hook = f'''if not TRUE_SUBMISSION:
    bm.solver.max_runtime_s_per_game = min(bm.solver.max_runtime_s_per_game, {gameplay})
    soft_end = min(soft_end, datetime.now()+timedelta(seconds={gameplay}))
'''
            run['source'] = run['source'].replace(anchor,hook+anchor)
        else:
            notebook, metadata, provenance = prediction_package(wall,gameplay)
        slug = 'arc-hydra-inspection-matched-control' if variant == 'control' else 'arc-hydra-prediction-matched-candidate'
        title = 'ARC Hydra Inspection Matched Control' if variant == 'control' else 'ARC Hydra Prediction Matched Candidate'
        metadata.update(id='kunalsinghh25/'+slug,title=title)
        provenance.update(experiment_variant=variant,public_gameplay_seconds=gameplay,
            official_submission_eligible=False,
            comparison_boundary='Same original model/draft/runtime/scheduler and all 25 public games. Hard 7200-second total GPU session cap includes startup and 600-second finalization reserve; gameplay uses the remaining time, at most 6600 seconds. Sampling is stochastic, not a paired-seed causal estimate. Development package must not be submitted.')
        notebook['cells'][0]['source'] += ('\n\nDevelopment ablation only: all 25 public games, '
            '7200-second hard total session limit, including startup and 600 seconds reserved for finalization. '
            'Gameplay is limited to the remaining time, at most 6600 seconds. '
            'Not for official submission. Final-agent package remains separately budgeted at nine hours.')
        output = ROOT/'notebooks/arc3_prediction_ablation_v2'/variant
        output.mkdir(parents=True,exist_ok=True)
        for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
            (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
        plan['variants'].append(dict(variant=variant,kernel=metadata['id'],
            package=str(output.relative_to(ROOT)).replace('\\','/'),
            files={p.name:sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}))
    directory = ROOT/'reports/arc3/prediction-ablation'
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(staged=True,launched=False,plan=str(directory/'plan.json'))))


if __name__ == '__main__':
    build()
