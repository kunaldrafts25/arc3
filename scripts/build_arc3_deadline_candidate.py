"""Freeze the CPU-gated FlashNext composition with separate development/official budgets."""
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_prediction_study_notebook import package

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'notebooks/arc3_deadline_candidate'
KERNEL = 'kunalsinghh25/arc-hydra-deadline-candidate'


def build():
    notebook, metadata, provenance = package(7200)
    run = next(c for c in notebook['cells'] if c['source'].startswith("print('Starting benchmark...')"))
    old = '    hydra_notebook_budget = min(hydra_notebook_budget, 7200)'
    assert run['source'].count(old) == 1
    run['source'] = run['source'].replace(old, '    hydra_notebook_budget = min(hydra_notebook_budget, 32400)')
    metadata.update(id=KERNEL, title='ARC Hydra Deadline Candidate')
    provenance.update(candidate='deadline-candidate', development_wall_seconds=7200,
        official_wall_seconds=32400, official_finalization_reserve_seconds=600,
        promotion_status='Awaiting actual two-hour gameplay. Official use requires an explicit evidence-based decision.',
        comparison_boundary='Development includes setup and finalization within 7200s. Official branch retains the legal 32400s. Public results cannot predict hidden score.')
    setup = next(c for c in notebook['cells'] if c['source'].startswith('# Each bundled repo exposes'))
    setup['source'] += f'\n(WORKING_DIR/"hydra_deadline_provenance.json").write_text(json.dumps({provenance!r},indent=2))\n'
    notebook['cells'][0]['source'] = (
        '# ARC3 deadline candidate\n\n'
        'Incumbent FlashNext, draft and serving; existing CPU-gated optional planning, exact inspection, '
        'prospective prediction and bounded study memory. No model weight changes. '
        'Development has a hard 7200-second total cap including startup and saving; '
        'the official branch has a 32400-second total limit and 600-second saving reserve. '
        'All public games, no public-game identities or solutions in policy. '
        'Gameplay and explicit promotion decision required before official use. '
        'Original upstream attribution and model/runtime licenses remain below.')
    import ast
    compile(run['source'], 'deadline-gameplay', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    compile(setup['source'], 'deadline-setup', 'exec')
    OUTPUT.mkdir(exist_ok=True)
    for name, value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        path = OUTPUT/name
        content = json.dumps(value,indent=2)+'\n'
        if path.exists() and path.read_text(encoding='utf-8') != content:
            raise RuntimeError('Existing frozen deadline package differs: '+name)
        path.write_text(content,encoding='utf-8')
    manifest = dict(kernel=KERNEL, development_wall_seconds=7200, official_wall_seconds=32400,
        files={name:sha256((OUTPUT/name).read_bytes()).hexdigest()
               for name in ('submission.ipynb','kernel-metadata.json','provenance.json')})
    (OUTPUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    build()
