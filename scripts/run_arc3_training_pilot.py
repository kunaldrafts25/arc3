"""One guarded original-account ARC3 training pilot; never submit or promote."""
import argparse
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import time

from scripts.build_arc3_training_data_offline_probe import BF16
from scripts.build_qwen27_probe import TARGET
from scripts.run_prediction_ablation import inspect_resources,launch_development,read_with_retry,save

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'notebooks/qwen27_lora_pilot'
DIRECTORY=ROOT/'reports/arc3/qwen27-lora-pilot'
OUTPUT=ROOT/'reports/kaggle/qwen27-lora-pilot-v1'
KERNEL='kunalsinghh25/arc-hydra-qwen27-lora-pilot'
KNOWN='kunalsinghh25/arc-hydra-qwen27-fair-capacity'


def resource_decision(available,reserved,paid,active):
    if paid:return False,'Paid scaling enabled'
    if reserved:return False,'Shared GPU reservation exists'
    if any(row['kernel']!=KNOWN for row in active):return False,'Another shared notebook is active'
    needed=7200+10800+(7200 if active else 0)
    if available<needed:return False,f'Need {needed} free seconds including full concurrent budget and ARC2 reserve'
    return True,'One capped training job; only acknowledged capped ARC3 capacity test may overlap; ARC2 floor preserved'


def validate_package():
    manifest=json.loads((PACKAGE/'manifest.json').read_text())
    metadata=json.loads((PACKAGE/'kernel-metadata.json').read_text())
    provenance=json.loads((PACKAGE/'provenance.json').read_text())
    for name,digest in manifest['files'].items():
        if sha256((PACKAGE/name).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen training package changed: '+name)
    if (manifest['kernel']!=KERNEL or manifest['wall_seconds']!=7200 or metadata['id']!=KERNEL
            or metadata['is_private'] is not True or metadata['enable_internet'] is not False
            or metadata['enable_gpu'] is not True or metadata['enable_tpu'] is not False
            or metadata['machine_shape']!='NvidiaRtxPro6000'
            or metadata['competition_sources']!=['arc-prize-2026-arc-agi-3']
            or metadata['model_sources']!=[BF16,TARGET] or metadata['kernel_sources']
            or metadata['dataset_sources']!=['dfranzen/pennyroyal-v253','kunalsinghh25/arc3-training-pilot-inputs-v1']
            or provenance['official_submission_eligible'] is not False
            or provenance['hard_session_timeout_seconds']!=7200 or provenance['internal_total_seconds']!=7200):
        raise ValueError('Unexpected training scope, sources, accelerator or total budget')
    prior=json.loads((ROOT/'reports/kaggle/qwen27-fair-capacity-v1/launch.json').read_text())
    if prior['phase']!='accepted' or prior['kernel']!=KNOWN or prior['hard_session_timeout_seconds']!=7200:
        raise ValueError('Potential concurrent ARC3 job has no acknowledged hard cap')
    return manifest,provenance


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--observe-only',action='store_true')
    args=parser.parse_args()
    if args.run and args.observe_only:raise ValueError('Choose launch or exact-version observation')
    manifest,provenance=validate_package()
    token=ROOT/'.kaggle/access_token';os.environ['KAGGLE_API_TOKEN']=token.read_text(encoding='utf-8-sig').strip();os.environ['KAGGLE_CONFIG_DIR']=str(token.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate();DIRECTORY.mkdir(parents=True,exist_ok=True);OUTPUT.mkdir(parents=True,exist_ok=True)
    journal=OUTPUT/'launch.json'
    if args.observe_only:
        state=json.loads(journal.read_text())
        if state['phase']!='accepted' or state['files']!=manifest['files'] or state['hard_session_timeout_seconds']!=7200:
            raise ValueError('Uncertain or mismatched training launch; reconcile before observing')
        exact=KERNEL+'/'+str(state['response']['versionNumber'])
        state.update(phase='observing',pid=os.getpid(),exact_kernel=exact)
    else:
        plan=json.loads((ROOT/'reports/arc3/prediction-ablation/plan.json').read_text())
        plan['expires']='2026-11-02T06:00:00+00:00'
        resources=inspect_resources(api,plan,1)
        allowed,reason=resource_decision(resources['available_gpu_seconds'],resources['reserved_gpu_seconds'],resources['pay_to_scale_enabled'],resources['active_gpu_jobs'])
        if datetime.now(timezone.utc)>=datetime.fromisoformat(plan['expires']):allowed,reason=False,'Pilot launch window expired'
        resources.update(allowed=allowed,reason=reason);save(DIRECTORY/'resource-check.json',resources);print(json.dumps(resources,indent=2),flush=True)
        if not args.run:return
        if not allowed:raise RuntimeError(reason)
        if read_with_retry(lambda:api.kernels_status(provenance['cpu_data_gate'])).status.name!='COMPLETE':raise RuntimeError('Exact CPU gate is not COMPLETE')
        state=dict(phase='launching',kernel=KERNEL,pid=os.getpid(),files=manifest['files'],hard_session_timeout_seconds=7200,
            resources=resources,scope='One actual ARC3 teacher-adaptation pilot. No automatic serving test, promotion or official submission.')
        with journal.open('x') as stream:json.dump(state,stream,indent=2)
        try:response=launch_development(api,PACKAGE,7200)
        except Exception as exc:
            state.update(phase='outcome_unconfirmed',error_type=type(exc).__name__);save(journal,state)
            raise RuntimeError('Training launch uncertain; never retry blindly') from exc
        state.update(phase='accepted',response=response.to_dict());save(journal,state)
        exact=KERNEL+'/'+str(response.version_number);state.update(phase='observing',exact_kernel=exact)
    save(DIRECTORY/'state.json',state)
    end=datetime.now(timezone.utc)+timedelta(hours=18)
    try:
        while datetime.now(timezone.utc)<end:
            status=read_with_retry(lambda:api.kernels_status(exact)).status.name;state.update(kernel_status=status);save(DIRECTORY/'state.json',state)
            if status in ['COMPLETE','ERROR','CANCEL_ACKNOWLEDGED']:break
            time.sleep(60)
        pattern=r'(^|/)(training-report\.json|training\.log|hydra_training_provenance\.json)$|(^|/)sft-pilot/(adapter|serving-adapter)/(adapter_config\.json|adapter_model\.safetensors|export-report\.json)$'
        if state.get('kernel_status') in ['COMPLETE','ERROR']:
            read_with_retry(lambda:api.kernels_output(exact,str(OUTPUT),file_pattern=pattern,quiet=True))
        if state.get('kernel_status')!='COMPLETE':raise RuntimeError('Training not COMPLETE; inspect the same exact version and its logs')
        report=json.loads((OUTPUT/'sft-pilot/training-report.json').read_text())
        if report['phase']!='complete' or report['optimizer_steps']<1 or report['adapter_output_squared_norm']<=0:
            raise RuntimeError('No complete real-checkpoint training and nonzero saved adapter')
        for name in ['adapter_config.json','adapter_model.safetensors']:
            if sha256((OUTPUT/'sft-pilot/adapter'/name).read_bytes()).hexdigest()!=report['adapter_files'][name]['sha256']:
                raise ValueError('Downloaded saved adapter differs from actual training report')
        for name,record in report['serving_export']['files'].items():
            if sha256((OUTPUT/'sft-pilot/serving-adapter'/name).read_bytes()).hexdigest()!=record['sha256']:
                raise ValueError('Downloaded serving export differs from actual training report')
        state.update(phase='pilot_complete',training_summary={key:report[key] for key in ['optimizer_steps','training_examples','training_epoch_fraction','supervised_tokens','validation_loss_delta','reload_loss_absolute_error']},
            next_action='Actual adapter serving compatibility and held-out gameplay comparison are required. Training loss/reload success is not agent performance.')
        save(DIRECTORY/'state.json',state)
    except Exception as exc:
        state.update(phase='observation_stopped',error_type=type(exc).__name__,reason=str(exc));save(DIRECTORY/'state.json',state);raise


if __name__=='__main__':main()
