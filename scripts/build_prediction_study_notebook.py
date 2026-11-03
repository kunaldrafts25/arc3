"""Stage the CPU-gated memory/prediction combination; no launch or promotion."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from hydra.research_guidance import GUIDANCE
from scripts.build_prediction_notebook import package as prediction_package

ROOT = Path(__file__).resolve().parents[1]


def package(wall_seconds=7200):
    if type(wall_seconds) is not int or not 1800 <= wall_seconds <= 7200:
        raise ValueError('New development candidates retain the two-hour total cap')
    gate = ROOT/'reports/kaggle/prediction-study-cpu-probe-v1'
    upload = json.loads((gate/'upload.json').read_text(encoding='utf-8'))
    report = json.loads((gate/'prediction-study-probe.json').read_text(encoding='utf-8'))
    if (upload['status'] != 'COMPLETE' or not report['passed'] or len(report['combined_cases']) != 4
            or len(report['prediction_cases']) != 12 or len(report['study_cases']) != 9):
        raise ValueError('Completed CPU composition gate required')
    cpu = ROOT/'notebooks/prediction_study_cpu_probe'
    for name,digest in upload['files'].items():
        if sha256((cpu/name).read_bytes()).hexdigest() != digest:
            raise ValueError('CPU package changed: '+name)
    for name,digest in upload['evidence_files'].items():
        if sha256((gate/name).read_bytes()).hexdigest() != digest:
            raise ValueError('CPU evidence changed: '+name)
    manifest = json.loads((cpu/'source-manifest.json').read_text(encoding='utf-8'))
    for group in ('files','prediction_files','study_files'):
        for name,digest in manifest[group].items():
            if sha256((ROOT/name).read_bytes()).hexdigest() != digest:
                raise ValueError('CPU-tested source changed: '+name)
    notebook,metadata,provenance = prediction_package(wall_seconds,wall_seconds-600)
    prediction = json.loads((gate/'hydra_prediction_extension.json').read_text(encoding='utf-8'))
    expected = json.loads((gate/'hydra_study_extension.json').read_text(encoding='utf-8'))
    setup = next(c for c in notebook['cells'] if c['source'].startswith('# Each bundled repo exposes'))
    installer = (ROOT/'scripts/install_study_agent.py').read_text(encoding='utf-8')
    library = (ROOT/'hydra/study_memory.py').read_text(encoding='utf-8')
    setup['source'] += f'\nassert _hydra_prediction_report == {prediction!r}, "Prediction differs from composition gate"\n'
    setup['source'] += f'_hydra_study_ns={{}}\nexec({installer!r},_hydra_study_ns)\n'
    setup['source'] += f'_hydra_study_report=_hydra_study_ns["install"](BUNDLE_DIR,{library!r},{GUIDANCE!r})\n'
    setup['source'] += f'assert _hydra_study_report == {expected!r}, "Study composition differs from completed CPU gate"\n'
    setup['source'] += '(WORKING_DIR/"hydra_study_extension.json").write_text(json.dumps(_hydra_study_report,indent=2))\n'
    metadata.update(id='kunalsinghh25/arc-hydra-prediction-study-candidate',title='ARC Hydra Prediction Study Candidate')
    provenance.update(candidate='prediction-study-candidate',study_cpu_gate=upload['kernel'],
        study_extension=expected,study_source_manifest=manifest['study_files'],
        official_submission_eligible=False,notebook_wall_budget_seconds=wall_seconds,
        experiment='Existing flexible planning/exact-inspection/prediction host plus existing bounded study memory and general learning protocol.',
        promotion_status='Completed CPU composition gate only. Staged; no combined model gameplay, score improvement or official submission.',
        comparison_boundary='Two-hour total development cap includes startup and finalization. No automatic launch or promotion. More tools and memory do not establish learning or score benefit.')
    setup['source'] += f'(WORKING_DIR/"hydra_prediction_study_provenance.json").write_text(json.dumps({provenance!r},indent=2))\n'
    compile(setup['source'],'prediction-study-setup','exec')
    notebook['cells'][0]['source'] = ('# ARC3 optional prediction plus study-memory experiment\n\n'
        'Composes existing CPU-tested memory/guidance with optional measured forecasts. '
        'Original model weights, draft, runtime, ordinary actions and guards retained. '
        f'Hard total notebook budget {wall_seconds} seconds including startup and 600-second finalization reserve. '
        'Actual host/child composition passed; model gameplay and score benefit remain untested. '
        'Development candidate only; do not submit. Original upstream attribution follows.')
    return notebook,metadata,provenance


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wall-seconds',type=int,default=7200)
    args = parser.parse_args()
    notebook,metadata,provenance = package(args.wall_seconds)
    output = ROOT/'notebooks/prediction_study_candidate';output.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(kernel=metadata['id'],cpu_gate=provenance['study_cpu_gate'],wall_seconds=args.wall_seconds,launched=False)))
