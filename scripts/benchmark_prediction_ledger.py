"""Synthetic active-identification diagnostic with explicitly supplied models.

Tests a narrow learning-loop component, not perception, LLM induction, goal
discovery, unseen-game solving, ARC scoring or a trained policy. No Kaggle/GPU.
"""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import random
from statistics import mean
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hydra.prediction_ledger import PredictionLedger, rank_probes


def episode(seed, family, policy):
    rng = random.Random(seed)
    names = [f'action_{n}' for n in rng.sample(range(100, 999), 4)]
    meanings = dict(zip(names, (0, 1, 2, 'arm')))
    names.sort()
    colors = rng.sample(range(16), 3)
    truth = rng.randrange(8)
    models = [f'model_{i}' for i in range(8)]
    ledger = PredictionLedger(models)
    armed = family == 'direct'
    steps = 0
    while steps < 64 and len(ledger.active()) > 1:
        forecasts = {}
        for action in names:
            kind = meanings[action]
            forecasts[action] = {model: {'signal': colors[(i >> kind) & 1] if armed and kind != 'arm' else colors[2]}
                                 for i, model in enumerate(models)}
        proposal = ledger.commit(step=steps, level=1, forecasts=forecasts)
        if policy == 'random':
            chosen = rng.choice(names)
        elif proposal['suggested_probe'] is not None:
            chosen = proposal['suggested_probe']
        elif policy == 'depth_two' and not armed:
            # Score two-step questions under the supplied candidate programs.
            # Execute only their FIRST real action, then measure and replan.
            arm = next(a for a in names if meanings[a] == 'arm')
            virtual = {arm + ';' + a: {model: {'signal': colors[(i >> meanings[a]) & 1]}
                                      for i, model in enumerate(models)}
                       for a in names if meanings[a] != 'arm'}
            question = rank_probes(virtual, ledger.active(), {a: 2 for a in virtual})[0]
            chosen = question['action'].split(';')[0] if question['score'] > 0 else None
        else:
            chosen = None
        if chosen is None:
            ledger.discard(proposal['ticket'])
            break
        kind = meanings[chosen]
        signal = colors[(truth >> kind) & 1] if armed and kind != 'arm' else colors[2]
        if kind == 'arm':
            armed = True
        steps += 1
        ledger.resolve(proposal['ticket'], action=chosen, step=steps, level=1,
                       observed={'signal': signal, 'irrelevant_counter': steps})
    active = list(ledger.active())
    return dict(seed=seed, family=family, policy=policy, probes=steps,
                identified=active == [models[truth]], surviving_models=len(active))


def main():
    start = time.monotonic()
    results = [episode(seed, family, policy) for family in ('direct', 'prerequisite')
               for policy in ('random', 'greedy_disagreement', 'depth_two') for seed in range(128)]
    groups = defaultdict(list)
    for row in results:
        groups[(row['family'], row['policy'])].append(row)
    summaries = [dict(family=f, policy=p, episodes=len(rows), identified=sum(r['identified'] for r in rows),
                      mean_probes=mean(r['probes'] for r in rows),
                      mean_probes_on_identified=mean(r['probes'] for r in rows if r['identified'])
                      if any(r['identified'] for r in rows) else None)
                 for (f, p), rows in groups.items()]
    report = dict(elapsed_seconds=time.monotonic()-start,
                  source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  ledger_sha256=sha256((ROOT/'hydra/prediction_ledger.py').read_bytes()).hexdigest(),
                  summaries=summaries, episodes=results,
                  boundary='Hand-designed finite deterministic model discrimination. Eight candidate programs are explicitly supplied, including the true program. Randomized control labels, signal colors and hidden hypothesis index do not constitute held-out mechanics families. Features are supplied exactly; there is no pixel perception, LLM hypothesis generation, unknown-goal learning or ARC score. Two-step lookahead assumes the prerequisite is already in the model class. No game-agent integration or official improvement established.')
    output = ROOT/'reports/research/active-identification'
    output.mkdir(parents=True, exist_ok=True)
    (output/'diagnostic.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(elapsed_seconds=report['elapsed_seconds'], summaries=summaries), indent=2))


if __name__ == '__main__':
    main()
