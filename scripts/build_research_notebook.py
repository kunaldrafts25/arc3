"""Package the CPU-gated general learner with a configurable whole-notebook budget."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from hydra.research_guidance import GUIDANCE
from scripts.build_ultimate_notebook import package as base_package

ROOT=Path(__file__).resolve().parents[1]


def package(wall_seconds=32400):
    if not 1800 <= wall_seconds <= 32400:
        raise ValueError('Notebook wall budget must be 1800..32400 seconds')
    gate=ROOT/'reports/kaggle/study-cpu-probe-v2'
    report=json.loads((gate/'study-probe.json').read_text(encoding='utf-8'))
    upload=json.loads((gate/'upload.json').read_text(encoding='utf-8'))
    if not report['passed'] or len(report['study_cases'])!=9:
        raise ValueError('Study integration gate has not passed')
    cpu=ROOT/'notebooks/study_cpu_probe'
    for name,expected in upload['files'].items():
        if sha256((cpu/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('CPU upload changed: '+name)
    manifest=json.loads((cpu/'source-manifest.json').read_text(encoding='utf-8'))
    for group in ('files','study_files'):
        for name,expected in manifest[group].items():
            if sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
                raise ValueError('CPU-tested source changed: '+name)
    expected=json.loads((gate/'hydra_study_extension.json').read_text(encoding='utf-8'))
    notebook,metadata,provenance=base_package('benchmark',public_runtime_seconds=wall_seconds-600,
                                           notebook_budget_seconds=wall_seconds)
    installer=(ROOT/'scripts/install_study_agent.py').read_text(encoding='utf-8')
    library=(ROOT/'hydra/study_memory.py').read_text(encoding='utf-8')
    setup=next(c for c in notebook['cells'] if c['source'].startswith('# Each bundled repo exposes'))
    setup['source']+=f'\n_hydra_study_ns={{}}\nexec({installer!r},_hydra_study_ns)\n'
    setup['source']+=f'_hydra_study_report=_hydra_study_ns["install"](BUNDLE_DIR,{library!r},{GUIDANCE!r})\n'
    setup['source']+=f'assert _hydra_study_report == {expected!r}, "Study sources differ from CPU integration gate"\n'
    base_expected=json.loads((gate/'hydra_extension.json').read_text(encoding='utf-8'))
    setup['source']+=f'assert _hydra_extension_report == {base_expected!r}, "Base sources differ from CPU integration gate"\n'
    setup['source']+='(WORKING_DIR/"hydra_study_extension.json").write_text(json.dumps(_hydra_study_report,indent=2))\n'
    provenance.update(candidate='general-learner',study_cpu_gate=upload['kernel'],study_extension=expected,
        study_source_manifest=manifest['study_files'],notebook_wall_budget_seconds=wall_seconds,
        finalization_reserve_seconds=600,best_prior_public_score=48.2861310586818,
        best_prior_official_score=24.87,
        comparison_boundary='Longer compute and a changed agent; comparison with the two-hour predecessor does not isolate strategy gain.',
        promotion_status='Experimental; GPU gameplay and official performance unverified')
    setup['source']+=f'(WORKING_DIR/"hydra_research_provenance.json").write_text(json.dumps({provenance!r},indent=2))\n'
    metadata.update(id='kunalsinghh25/arc-hydra-general-learner',title='ARC Hydra General Learner')
    notebook['cells'][0]['source']=(
        '# ARC-Hydra General Learner\n\n'
        'Experimental research-derived learning protocol and bounded persistent hypothesis memory. '
        'Distinguishes controls, state, modes, mechanics, goals and resources; chooses informative probes '
        'and applies geometry, permutations, search or constraints when their assumptions fit observations. '
        'Memory references are checked against observed steps; the agent must still validate its claims. '
        'Game-scoped discoveries from an earlier level require rechecking. Ordinary action batching remains available.\n\n'
        f'Whole-notebook budget: **{wall_seconds/3600:g} hours**, including startup and a ten-minute finalization reserve. '
        'All 25 public games share the remaining gameplay window. No two-hour gameplay cap. '
        'Original pretrained model, draft and serving runtime remain unchanged; no weight training. '
        'The offline CPU gate passed eight mechanical cases, 16 prompt combinations and nine memory/host cases.\n\n'
        'Previous best public result: 48.29; best official result: 24.87. This run changes both the strategy '
        'and compute budget, so a score difference will not isolate either contribution. '
        'No public-game identifiers or hand-written solutions are inserted. Original upstream attribution follows.')
    # Upstream includes IPython %%writefile/%%bash cells; validate the Python
    # cell modified here directly, without treating those magics as Python.
    compile(setup['source'],'general-learner-setup','exec')
    return notebook,metadata,provenance


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wall-seconds',type=int,default=32400)
    args=parser.parse_args()
    notebook,metadata,provenance=package(args.wall_seconds)
    output=ROOT/'notebooks/general_learner';output.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(kernel=metadata['id'],wall_seconds=args.wall_seconds,cpu_gate=provenance['study_cpu_gate'])))


if __name__=='__main__':
    main()
