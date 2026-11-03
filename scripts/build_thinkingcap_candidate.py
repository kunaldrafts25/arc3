"""Stage a capped model-bundle comparison against the frozen inspection control."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    gate=ROOT/'reports/kaggle/model-compatibility-cpu-probe-v1'
    verified=json.loads((gate/'verified.json').read_text())
    if verified['status']!='COMPLETE' or not verified['schema_compatible']:
        raise ValueError('Completed exact CPU checkpoint schema gate required')
    report_path=gate/'model-compatibility.json'
    if sha256(report_path.read_bytes()).hexdigest()!=verified['report_sha256']:
        raise ValueError('CPU report changed')
    report=json.loads(report_path.read_text())
    cpu=ROOT/'notebooks/model_compatibility_cpu_probe'
    if any(sha256((cpu/n).read_bytes()).hexdigest()!=h for n,h in verified['files'].items()):
        raise ValueError('CPU upload changed')
    plan=json.loads((ROOT/'reports/arc3/prediction-ablation/plan.json').read_text())
    control=plan['variants'][0]
    package=ROOT/control['package']
    if any(sha256((package/n).read_bytes()).hexdigest()!=h for n,h in control['files'].items()):
        raise ValueError('Frozen actual-gameplay control changed')
    notebook=deepcopy(json.loads((package/'submission.ipynb').read_text()))
    metadata=json.loads((package/'kernel-metadata.json').read_text())
    provenance=json.loads((package/'provenance.json').read_text())
    base='dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1'
    target='lamdang/thinkingcap-qwen3-8-flash-next-w4a16-autoround/Transformers/default/1'
    old="MODEL_DIR         = '/kaggle/input/models/dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/transformers/default/1'"
    new="MODEL_DIR         = '/kaggle/input/models/lamdang/thinkingcap-qwen3-8-flash-next-w4a16-autoround/transformers/default/1'"
    env=next(c for c in notebook['cells'] if c['cell_type']=='code' and old in c['source'])
    assert env['source'].count(old)==1
    env['source']=env['source'].replace(old,new)
    expected={name:row['sha256'] for name,row in report['candidate_metadata'].items()}
    env['source']+=f'\n_hydra_checkpoint_expected_metadata={expected!r}\n'
    env['source']+='''from hashlib import sha256 as _hydra_checkpoint_sha256
for _hydra_name,_hydra_digest in _hydra_checkpoint_expected_metadata.items():
    if _hydra_checkpoint_sha256((Path(MODEL_DIR)/_hydra_name).read_bytes()).hexdigest()!=_hydra_digest:
        raise ValueError('ThinkingCap checkpoint metadata differs from exact CPU gate: '+_hydra_name)
'''
    # The inherited environment cell contains IPython shell escapes. Validate
    # only the added pure-Python preflight, leaving those original cells intact.
    compile(env['source'][env['source'].index('_hydra_checkpoint_expected_metadata='):],
            'thinkingcap-candidate-preflight','exec')
    metadata['model_sources']=[target if ref==base else ref for ref in metadata['model_sources']]
    metadata.update(id='kunalsinghh25/arc-hydra-thinkingcap-matched-candidate',title='ARC Hydra Thinkingcap Matched Candidate')
    provenance.update(candidate='thinkingcap-matched-candidate',experiment_variant='thinkingcap',
        model_base=base,model_candidate=target,model_cpu_gate=verified['kernel'],
        model_cpu_report_sha256=verified['report_sha256'],notebook_wall_budget_seconds=7200,
        official_submission_eligible=False,
        changed_components=['Target checkpoint including its quantization calibration and file layout; exact metadata hash preflight'],
        retained_components=['Draft checkpoint','Runtime/image','Flexible agent plus exact inspection','Scheduler','All 25 public games','7200-second total development cap'],
        model_attribution=dict(authors='BottleCap AI; Kaggle AutoRound quantization by Lam Dang',
            model_card='https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-Flash-Next',
            kaggle='https://www.kaggle.com/models/lamdang/thinkingcap-qwen3-8-flash-next-w4a16-autoround',
            license='Qwen Community License 1.0; retained upstream licenses/notices apply'),
        promotion_status='CPU metadata/header compatibility only; no serving, draft acceptance, model gameplay or score benefit established.',
        comparison_boundary='Practical checkpoint-bundle comparison, not an isolated post-training effect: quantization calibration and shard layout differ. Same total two-hour notebook budget includes startup and finalization. External timeout must also be 7200 seconds at any future launch. No automatic launch or official submission.')
    env['source']+=f'(WORKING_DIR/"hydra_model_candidate.json").write_text(json.dumps({provenance!r},indent=2))\n'
    compile(env['source'][env['source'].index('_hydra_checkpoint_expected_metadata='):],
            'thinkingcap-candidate-preflight','exec')
    notebook['cells'][0]['source']=('# ARC3 ThinkingCap checkpoint comparison\n\n'
        'Same measured flexible inspection control, with the target replaced by the public ThinkingCap '
        'checkpoint quantized by Lam Dang. Draft, serving settings, scheduler and game tools retained. '
        'Two-hour total development budget includes startup and finalization. '
        'CPU tensor/metadata schema checks passed; real inference and game performance are unverified. '
        'Do not submit this development package. Original authors, licenses and attribution retained.')
    output=ROOT/'notebooks/thinkingcap_matched_candidate';output.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    manifest=dict(kernel=metadata['id'],wall_seconds=7200,launched=False,
        files={n:sha256((output/n).read_bytes()).hexdigest() for n in ('submission.ipynb','kernel-metadata.json','provenance.json')})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':build()
