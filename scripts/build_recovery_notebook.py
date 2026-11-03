"""Package a CPU-gated full-budget recovery candidate and flexible control."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_research_notebook import package as study_package
from scripts.build_ultimate_notebook import package as flexible_package

ROOT=Path(__file__).resolve().parents[1]


def package(control=False,wall_seconds=32400):
    if control:
        notebook,metadata,provenance=flexible_package('benchmark',public_runtime_seconds=wall_seconds-600,
                                                    notebook_budget_seconds=wall_seconds)
        metadata.update(id='kunalsinghh25/arc-hydra-flexible-extended-control',title='ARC Hydra Flexible Extended Control')
        provenance.update(candidate='flexible-extended-control',
            experiment='Extend the preserved 48.29 two-hour flexible agent to the same whole-notebook wall budget as the study/recovery candidates.',
            promotion_status='Experimental control, not launched or gameplay validated')
        notebook['cells'][0]['source']=(
            '# ARC-Hydra Flexible Extended Control\n\n'
            f'Original flexible optional-planning agent with a {wall_seconds}-second whole-notebook budget '
            'including startup and a 600-second finalization reserve. All 25 public games. '
            'No added study memory, research guidance or recovery advisory. '
            'This control tests how much the previous 48.29 result changes with a longer compute budget. '
            'Original model, draft, runtime, attribution and ordinary action behavior are retained. '
            'Not yet launched; no score is claimed.')
        return notebook,metadata,provenance
    gate=ROOT/'reports/kaggle/recovery-cpu-probe-v1'
    report=json.loads((gate/'recovery-probe.json').read_text(encoding='utf-8'))
    if not report['passed'] or report['action_gating'] or len(report['cases'])!=4:
        raise ValueError('Recovery gate has not passed')
    upload=json.loads((gate/'upload.json').read_text(encoding='utf-8'))
    cpu=ROOT/'notebooks/recovery_cpu_probe'
    for name,expected in upload['files'].items():
        if sha256((cpu/name).read_bytes()).hexdigest()!=expected:raise ValueError('CPU upload changed: '+name)
    manifest=json.loads((cpu/'source-manifest.json').read_text(encoding='utf-8'))
    for group in ('files','study_files','recovery_files'):
        for name,expected in manifest[group].items():
            if sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise ValueError('CPU-tested source changed: '+name)
    notebook,metadata,provenance=study_package(wall_seconds)
    installer=(ROOT/'scripts/install_recovery_agent.py').read_text(encoding='utf-8')
    library=(ROOT/'hydra/recovery_monitor.py').read_text(encoding='utf-8')
    expected=json.loads((gate/'hydra_recovery_extension.json').read_text(encoding='utf-8'))
    setup=next(c for c in notebook['cells'] if c['source'].startswith('# Each bundled repo exposes'))
    setup['source']+=f'\n_hydra_recovery_ns={{}}\nexec({installer!r},_hydra_recovery_ns)\n'
    setup['source']+=f'_hydra_recovery_report=_hydra_recovery_ns["install"](BUNDLE_DIR,{library!r})\n'
    setup['source']+=f'assert _hydra_recovery_report == {expected!r}, "Recovery sources differ from completed CPU gate"\n'
    setup['source']+='(WORKING_DIR/"hydra_recovery_extension.json").write_text(json.dumps(_hydra_recovery_report,indent=2))\n'
    provenance.update(candidate='recovery-candidate',recovery_cpu_gate=upload['kernel'],
        recovery_extension=expected,recovery_source_manifest=manifest['recovery_files'],
        promotion_status='CPU-gated experimental candidate; not launched, no score improvement established')
    setup['source']+=f'(WORKING_DIR/"hydra_recovery_provenance.json").write_text(json.dumps({provenance!r},indent=2))\n'
    metadata.update(id='kunalsinghh25/arc-hydra-recovery-candidate',title='ARC Hydra Recovery Candidate')
    notebook['cells'][0]['source']=(
        '# ARC-Hydra Recovery Candidate\n\n'
        'Adds cross-decision advisory evidence to the general learner. Reports a long current-level '
        'observation streak and repeated exact visible transitions, with observed step references. '
        'Prompts goal/rule revision or a discriminating experiment; does not block ordinary actions '
        'or treat identical pixels as proof of unchanged hidden state. '
        'Notices are bounded and separated by at least 32 new environment steps. '
        'Per-game event files record actual notices for an adoption audit.\n\n'
        f'All 25 public games use a {wall_seconds}-second whole-notebook budget, '
        'including startup and a 600-second finalization reserve. No two-hour cap. '
        'Same pretrained target/draft, serving stack, scheduler, study memory and optional planning. '
        'Previous general learner: 62.09 development; user-reported associated official submission: 28.45. '
        'This candidate has passed CPU integration only and has no gameplay score. '
        'Upstream attribution and original notebook follow.')
    for cell in notebook['cells']:
        if cell['cell_type']=='code':
            cell['source']=cell['source'].replace("variant='planning-assist'","variant='recovery-advisory'")
    compile(setup['source'],'recovery-notebook-setup','exec')
    return notebook,metadata,provenance


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control',action='store_true')
    parser.add_argument('--wall-seconds',type=int,default=32400)
    args=parser.parse_args();notebook,metadata,provenance=package(args.control,args.wall_seconds)
    output=ROOT/'notebooks'/('flexible_extended_control' if args.control else 'recovery_candidate')
    output.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(kernel=metadata['id'],wall_seconds=args.wall_seconds,launched=False)))


if __name__=='__main__':main()
