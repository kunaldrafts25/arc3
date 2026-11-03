"""One capped independent ARC3 checkpoint evaluation; never submit officially."""
import argparse
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import time

from scripts.run_prediction_ablation import inspect_resources,launch_development,read_with_retry,save,download_and_analyze

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'reports/arc3/thinkingcap-comparison'
OUTPUT=ROOT/'reports/kaggle/thinkingcap-matched-v1'
PACKAGE=ROOT/'notebooks/thinkingcap_matched_candidate'
PREDICTION='kunalsinghh25/arc-hydra-prediction-matched-candidate/1'
TERMINAL={'COMPLETE','ERROR','CANCEL_ACKNOWLEDGED'}


def resource_decision(available,reserved,paid,active,prediction_status):
    if paid:return False,'Paid scaling enabled'
    if reserved>0:return False,'Shared GPU time is reserved'
    expected=PREDICTION.rsplit('/',1)[0]
    if any(row['kernel']!=expected for row in active):
        return False,'Another shared notebook is active'
    if prediction_status not in TERMINAL|{'QUEUED'}:
        return False,'Wait for the current ARC3 GPU run'
    if any(row['status']!='QUEUED' for row in active):
        return False,'Another shared notebook is running'
    # This explicitly permits two independent queued ARC3 jobs, which may later
    # overlap. Both have external 7200-second limits. Reserve their full remaining
    # budgets and the existing three-hour ARC2 floor, with no quota bypass.
    needed=7200+(7200 if prediction_status=='QUEUED' else 0)+10800
    if available<needed:return False,f'Need {needed} free seconds including both jobs and ARC2 floor'
    return True,'Bounded original-account free budget; only the known ARC3 job may already be queued'


def validate_package():
    manifest=json.loads((PACKAGE/'manifest.json').read_text())
    metadata=json.loads((PACKAGE/'kernel-metadata.json').read_text())
    provenance=json.loads((PACKAGE/'provenance.json').read_text())
    for name,digest in manifest['files'].items():
        if sha256((PACKAGE/name).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen checkpoint package changed: '+name)
    if (metadata['id']!='kunalsinghh25/arc-hydra-thinkingcap-matched-candidate'
            or metadata['enable_internet'] or not metadata['enable_gpu'] or not metadata['is_private']
            or metadata['machine_shape']!='NvidiaRtxPro6000'
            or metadata['competition_sources']!=['arc-prize-2026-arc-agi-3']
            or metadata['model_sources']!=[
                'dfranzen/albucino-qwen3-8-flash-next-drafter/Transformers/default/1',
                'lamdang/thinkingcap-qwen3-8-flash-next-w4a16-autoround/Transformers/default/1']
            or provenance['notebook_wall_budget_seconds']!=7200
            or provenance['official_submission_eligible'] is not False):
        raise ValueError('Unexpected checkpoint package, accelerator, offline configuration or budget')
    # The only potentially overlapping job must itself be an acknowledged capped
    # exact version, not an uncertain mutation or inferred notebook identity.
    prior=json.loads((ROOT/'reports/kaggle/prediction-matched-prediction-v1/launch.json').read_text())
    if (prior['phase']!='accepted' or prior['hard_session_timeout_seconds']!=7200
            or prior['kernel']+'/'+str(prior['response']['versionNumber'])!=PREDICTION):
        raise ValueError('Existing ARC3 queue entry is not the acknowledged capped version')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true')
    args=parser.parse_args();manifest=validate_package()
    token=ROOT/'.kaggle/access_token'
    os.environ['KAGGLE_API_TOKEN']=token.read_text(encoding='utf-8-sig').strip()
    os.environ['KAGGLE_CONFIG_DIR']=str(token.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    plan=json.loads((ROOT/'reports/arc3/prediction-ablation/plan.json').read_text())
    plan['expires']='2026-11-01T18:00:00+00:00'
    resources=inspect_resources(api,plan,1)
    prediction_status=read_with_retry(lambda:api.kernels_status(PREDICTION)).status.name
    allowed,reason=resource_decision(resources['available_gpu_seconds'],resources['reserved_gpu_seconds'],
        resources['pay_to_scale_enabled'],resources['active_gpu_jobs'],prediction_status)
    if datetime.now(timezone.utc)>=datetime.fromisoformat(plan['expires']):
        allowed,reason=False,'Checkpoint experiment launch window expired'
    resources.update(allowed=allowed,reason=reason,prediction_exact_status=prediction_status,
        queue_policy='At most two independent ARC3 sessions; each externally capped at 7200 seconds, may overlap; ARC2 floor 10800 seconds')
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    save(DIRECTORY/'resource-check.json',resources)
    print(json.dumps(resources,indent=2),flush=True)
    if not args.run:return
    if not allowed:raise RuntimeError(reason)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    state=dict(phase='launching',pid=os.getpid(),kernel=manifest['kernel'],files=manifest['files'],
        hard_session_timeout_seconds=7200,resources=resources,scope='One ARC3 public development comparison; no official submission')
    journal=OUTPUT/'launch.json'
    with journal.open('x',encoding='utf-8') as stream:json.dump(state,stream,indent=2)
    try:
        response=launch_development(api,PACKAGE,7200)
    except Exception as exc:
        state.update(phase='outcome_unconfirmed',error_type=type(exc).__name__);save(journal,state)
        raise RuntimeError('Uncertain checkpoint launch; do not retry') from exc
    state.update(phase='accepted',response=response.to_dict());save(journal,state)
    exact=manifest['kernel']+'/'+str(response.version_number)
    state.update(phase='observing',exact_kernel=exact)
    save(DIRECTORY/'state.json',state)
    observation_end=datetime.now(timezone.utc)+timedelta(hours=18)
    try:
        while datetime.now(timezone.utc)<observation_end:
            status=read_with_retry(lambda:api.kernels_status(exact)).status.name
            state.update(kernel_status=status);save(DIRECTORY/'state.json',state)
            if status in TERMINAL:break
            time.sleep(60)
        if state.get('kernel_status')!='COMPLETE':
            raise RuntimeError('Checkpoint run is not COMPLETE; inspect the same exact version without relaunching')
        analysis=download_and_analyze(api,exact,OUTPUT)
        state.update(phase='evaluation_complete',analysis=analysis,
            next_action='Compare with the frozen inspection control, inspect model/serving behavior and preserve the best official agent; no automatic promotion.')
        save(DIRECTORY/'state.json',state)
    except Exception as exc:
        state.update(phase='observation_stopped',error_type=type(exc).__name__,reason=str(exc))
        save(DIRECTORY/'state.json',state);raise


if __name__=='__main__':main()
