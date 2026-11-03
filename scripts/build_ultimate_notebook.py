"""Package optional planning after the strict-planner comparison regressed."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_duck_notebook import build

ROOT = Path(__file__).resolve().parents[1]


def package(mode='benchmark',public_runtime_seconds=None,notebook_budget_seconds=None):
    gate = ROOT / 'reports/kaggle/verified-cpu-probe-v5'
    report = json.loads((gate / 'verified-probe.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT / 'notebooks/verified_cpu_probe/source-manifest.json').read_text(encoding='utf-8'))
    if not report['passed'] or not report['prompt_contract_consistent'] or report['enforce_probes']:
        raise ValueError('CPU validation has not passed')
    # The generated CPU notebook and downloaded installed-source report must
    # correspond to the recorded exact upload, rather than a newer local build.
    upload = json.loads((gate / 'upload.json').read_text(encoding='utf-8'))
    for name in ('probe.ipynb', 'source-manifest.json'):
        actual = sha256((ROOT / 'notebooks/verified_cpu_probe' / name).read_bytes()).hexdigest()
        if actual != upload['files'][name]:
            raise ValueError('CPU package differs from the completed uploaded gate: ' + name)
    for name, expected in manifest['files'].items():
        if sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Source differs from CPU-tested package: ' + name)
    notebook, metadata, provenance = build(mode, agent_variant='planning-assist',public_runtime_seconds=public_runtime_seconds,notebook_budget_seconds=notebook_budget_seconds)
    resolver=(ROOT/'scripts/resolve_kaggle_inputs.py').read_text(encoding='utf-8')
    config=next(c for c in notebook['cells'] if c['source'].startswith('import json\nimport os'))
    anchor='# Apply harness patch'
    assert config['source'].count(anchor)==1
    wheel_path='/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels'
    check=f'COMPETITION_WHEELHOUSE = {wheel_path!r}\n_hydra_inputs_ns = {{}}\nexec({resolver!r}, _hydra_inputs_ns)\n'
    check+='_hydra_inputs = _hydra_inputs_ns["resolve_inputs"](globals())\nglobals().update(_hydra_inputs)\nprint("ARC_HYDRA_INPUT_PATHS", json.dumps(_hydra_inputs, sort_keys=True))\n\n'
    config['source']=config['source'].replace(anchor,check+anchor)
    for cell in notebook['cells']:
        if cell is not config and cell['cell_type']=='code':
            for quoted in (repr(wheel_path),json.dumps(wheel_path)):
                cell['source']=cell['source'].replace(quoted,'COMPETITION_WHEELHOUSE')
    metadata.update(id='kunalsinghh25/arc-hydra-ultimate-candidate',
                    title='ARC Hydra Ultimate Candidate')
    installed = json.loads((gate / 'hydra_extension.json').read_text(encoding='utf-8'))
    provenance.update(candidate='ultimate-candidate',
                      input_resolver_sha256=sha256(resolver.encode()).hexdigest(),
                      cpu_gate=upload['kernel'], extension=installed,
                      validation_scope=report['prompt_contract_scope'],
                      promotion_status='Experimental; no GPU improvement or official score established')
    notebook['cells'].insert(0, dict(cell_type='markdown', metadata={}, source=(
        '# ARC-Hydra Ultimate Candidate\n\n'
        'A separately versioned **experimental candidate**, not a claim of superior scores. '
        'Uses the original Intel AutoRound Qwen3.8-Flash-Next model/draft and v2.5.3 serving stack, '
        'optional mechanical replay/planning tools with original ordinary action batching, '
        'shared backend readiness, lifecycle records and a ten-minute competition finalization reserve. '
        'No model-weight training.\n\n'
        f'Public mode: **{mode}**. Preflight plays five diagnostic games for 900 seconds after readiness; '+
        ('benchmark plays all 25 public games for 7200 seconds after readiness. ' if notebook_budget_seconds is None else
         f'benchmark uses a {notebook_budget_seconds}-second whole-notebook budget including startup and a finalization reserve. ')+
        'Official reruns retain the nine-hour competition budget with startup/finalization included. '
        'No public score is a hidden-score estimate.\n\n'
        'Offline CPU probe v5 passed eight sandbox cases and 16 rendered user-prompt combinations. '
        'The preceding matched 25-game comparison scored 45.02 for the original agent and '
        '33.18 for the strict planner. This candidate retains ordinary action flexibility '
        'while testing whether optional checking helps. '
        'GPU gameplay and hidden performance still require evaluation. '
        'Original agent: Daniel Franzen / Jeroen Cottaar / Tufa Labs; original attribution and notices follow.'
    )))
    return notebook, metadata, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('preflight', 'benchmark'), default='benchmark')
    args = parser.parse_args()
    notebook, metadata, provenance = package(args.mode)
    output = ROOT / 'notebooks/ultimate_candidate'
    output.mkdir(exist_ok=True)
    for name, data in (('submission.ipynb', notebook), ('kernel-metadata.json', metadata),
                       ('provenance.json', provenance)):
        (output / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(output=str(output), kernel=metadata['id'], mode=args.mode,
                          public_seconds=provenance['public_runtime_seconds'],
                          cpu_gate=provenance['cpu_gate']), indent=2))


if __name__ == '__main__':
    main()
