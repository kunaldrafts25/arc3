"""Stage the CPU-gated prediction experiment; never launch or submit a notebook."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from scripts.build_inspection_notebook import package as inspection_package

ROOT = Path(__file__).resolve().parents[1]


def package(wall_seconds=32400, public_gameplay_seconds=None):
    gate = ROOT/'reports/kaggle/prediction-cpu-probe-v3'
    report = json.loads((gate/'prediction-probe.json').read_text(encoding='utf-8'))
    upload = json.loads((gate/'upload.json').read_text(encoding='utf-8'))
    if not report['passed'] or len(report['cases']) != 12 or report['event_format'] != 2 or upload['status'] != 'COMPLETE':
        raise ValueError('Completed prediction CPU integration gate required')
    cpu = ROOT/'notebooks/prediction_cpu_probe_v3'
    for name, digest in upload['files'].items():
        if sha256((cpu/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Prediction gate upload changed: '+name)
    manifest = json.loads((cpu/'source-manifest.json').read_text(encoding='utf-8'))
    for group in ('files','prediction_files'):
        for name, digest in manifest[group].items():
            if sha256((ROOT/name).read_bytes()).hexdigest() != digest:
                raise ValueError('Prediction gate source changed: '+name)
    notebook, metadata, provenance = inspection_package(wall_seconds)
    setup = next(c for c in notebook['cells'] if c['source'].startswith('# Each bundled repo exposes'))
    inspection = json.loads((gate/'hydra_inspection_extension.json').read_text(encoding='utf-8'))
    expected = json.loads((gate/'hydra_prediction_extension.json').read_text(encoding='utf-8'))
    installer = (ROOT/'scripts/install_prediction_agent.py').read_text(encoding='utf-8')
    libraries = {name:(ROOT/('hydra/prediction_'+file+'.py')).read_text(encoding='utf-8')
                 for name,file in [('host','host'),('tools','tools'),('ledger','ledger')]}
    setup['source'] += f'\nassert _hydra_inspection_report == {inspection!r}, "Inspection differs from prediction gate"\n'
    setup['source'] += f'_hydra_prediction_ns={{}}\nexec({installer!r},_hydra_prediction_ns)\n'
    setup['source'] += f'_hydra_prediction_report=_hydra_prediction_ns["install"](BUNDLE_DIR,{libraries!r})\n'
    setup['source'] += f'assert _hydra_prediction_report == {expected!r}, "Prediction differs from completed CPU gate"\n'
    setup['source'] += '(WORKING_DIR/"hydra_prediction_extension.json").write_text(json.dumps(_hydra_prediction_report,indent=2))\n'
    if public_gameplay_seconds is not None:
        if type(public_gameplay_seconds) is not int or not 60 <= public_gameplay_seconds <= wall_seconds-600:
            raise ValueError('Invalid public gameplay window')
        # Keep final competition budget separate from an explicitly short ablation.
        run = next(c for c in notebook['cells'] if c['source'].startswith("print('Starting benchmark...')"))
        anchor = "_hydra_context['games'] = len(bm.games)"
        assert run['source'].count(anchor) == 1
        hook = f'''if not TRUE_SUBMISSION:
    bm.solver.max_runtime_s_per_game = min(bm.solver.max_runtime_s_per_game, {public_gameplay_seconds})
    soft_end = min(soft_end, datetime.now()+timedelta(seconds={public_gameplay_seconds}))
'''
        run['source'] = run['source'].replace(anchor,hook+anchor)
    metadata.update(id='kunalsinghh25/arc-hydra-prediction-candidate-v2',title='ARC Hydra Prediction Candidate V2')
    provenance.update(candidate='prediction-candidate-v2',prediction_cpu_gate=upload['kernel'],
        prediction_extension=expected,prediction_source_manifest=manifest['prediction_files'],
        public_gameplay_seconds=public_gameplay_seconds,
        experiment='Flexible exact-inspection base plus optional host-owned forecasts and measured counterexamples. No recovery/study additions.',
        promotion_status='CPU-gated and staged; no model adoption or gameplay benefit established')
    setup['source'] += f'(WORKING_DIR/"hydra_prediction_provenance.json").write_text(json.dumps({provenance!r},indent=2))\n'
    compile(setup['source'],'prediction-candidate-setup','exec')
    notebook['cells'][0]['source'] = (
        '# ARC3 optional prospective prediction experiment\n\n'
        'Host-owned forecasts over fixed measured features, frozen and logged before an ordinary action. '
        'Automatic scoped counterexamples survive tool resets and post-action timeouts. '
        'Evidence storage failures preserve original action accounting and report an unchecked prediction. '
        'Original ordinary batches, model, draft, serving, scheduler and attribution retained. '
        'Features are pixels, not certified objects, rules or goals. No model-weight training. '
        f'Whole-notebook budget {wall_seconds} seconds, including startup and 600-second finalization reserve. '
        'The official path retains this full budget; any short public ablation is recorded separately. '
        'CPU checks passed; model adoption, gameplay benefit and official performance remain unverified.')
    return notebook,metadata,provenance


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wall-seconds',type=int,default=32400)
    parser.add_argument('--public-gameplay-seconds',type=int)
    args = parser.parse_args()
    notebook, metadata, provenance = package(args.wall_seconds,args.public_gameplay_seconds)
    output = ROOT/'notebooks/prediction_candidate_v2'
    output.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(kernel=metadata['id'],launched=False,wall_seconds=args.wall_seconds)))
