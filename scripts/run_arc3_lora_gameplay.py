"""Run one capped saved-adapter screen while reserving ARC2 and a final run."""
import argparse
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import time

from scripts.build_arc3_lora_gameplay import KERNEL,TRAIN,HELD_OUT
from scripts.build_qwen27_probe import TARGET,DRAFT
from scripts.run_prediction_ablation import inspect_resources,launch_development,read_with_retry,save

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'notebooks/qwen27_lora_gameplay'
DIRECTORY=ROOT/'reports/arc3/qwen27-lora-gameplay'
OUTPUT=ROOT/'reports/kaggle/qwen27-lora-gameplay-v1'
KNOWN='kunalsinghh25/arc-hydra-qwen27-fair-capacity'


def resource_decision(available,reserved,paid,active):
    if paid:return False,'Paid scaling enabled'
    if reserved:return False,'Shared GPU reservation exists'
    if any(row['kernel']!=KNOWN for row in active):return False,'Another shared notebook is active'
    needed=7200+10800+32400+(7200 if active else 0)
    if available<needed:return False,'Need full screen/concurrent budgets, three-hour ARC2 floor and nine-hour final-run reserve'
    return True,'One two-hour screen; only acknowledged capped ARC3 capacity job may overlap; ARC2 and final evaluation reserves preserved'


def validate_package():
    manifest=json.loads((PACKAGE/'manifest.json').read_text())
    metadata=json.loads((PACKAGE/'kernel-metadata.json').read_text())
    provenance=json.loads((PACKAGE/'provenance.json').read_text())
    if any(sha256((PACKAGE/name).read_bytes()).hexdigest()!=digest for name,digest in manifest['files'].items()):
        raise ValueError('Frozen evaluation package changed')
    if (manifest['kernel']!=KERNEL or manifest['wall_seconds']!=7200 or metadata['id']!=KERNEL
            or metadata['kernel_sources']!=[TRAIN] or metadata['enable_gpu'] is not True
            or metadata['enable_internet'] is not False or metadata['is_private'] is not True
            or metadata['machine_shape']!='NvidiaRtxPro6000' or metadata.get('enable_tpu',False)
            or metadata['model_sources']!=[TARGET,DRAFT]
            or metadata['dataset_sources']!=['dfranzen/pennyroyal-v253','dfranzen/taaf-kaggle-source-bundle-copy']
            or metadata['competition_sources']!=['arc-prize-2026-arc-agi-3']
            or provenance['official_submission_eligible'] is not False
            or sorted(provenance['gradient_holdout_games'])!=HELD_OUT):
        raise ValueError('Evaluation scope, source or resource cap changed')
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
            raise ValueError('Uncertain or mismatched launch; reconcile without rerunning')
        exact=KERNEL+'/'+str(state['response']['versionNumber'])
        state.update(phase='observing',pid=os.getpid(),exact_kernel=exact)
    else:
        plan=json.loads((ROOT/'reports/arc3/prediction-ablation/plan.json').read_text())
        plan['expires']='2026-11-02T06:00:00+00:00'
        resources=inspect_resources(api,plan,1)
        allowed,reason=resource_decision(resources['available_gpu_seconds'],resources['reserved_gpu_seconds'],resources['pay_to_scale_enabled'],resources['active_gpu_jobs'])
        if datetime.now(timezone.utc)>=datetime.fromisoformat(plan['expires']):allowed,reason=False,'Screening launch window expired'
        resources.update(allowed=allowed,reason=reason,final_official_free_seconds_floor=32400)
        save(DIRECTORY/'resource-check.json',resources);print(json.dumps(resources,indent=2),flush=True)
        if not args.run:return
        if not allowed:raise RuntimeError(reason)
        if read_with_retry(lambda:api.kernels_status(TRAIN)).status.name!='COMPLETE':raise RuntimeError('Actual training version is not COMPLETE')
        if read_with_retry(lambda:api.kernels_status(provenance['adapter_mount_gate'])).status.name!='COMPLETE':raise RuntimeError('Exact saved-adapter mount gate is not COMPLETE')
        state=dict(phase='launching',kernel=KERNEL,pid=os.getpid(),files=manifest['files'],hard_session_timeout_seconds=7200,
            resources=resources,scope='One paired base/adapter real-game screen. No automatic promotion or official submission.')
        with journal.open('x') as stream:json.dump(state,stream,indent=2)
        try:response=launch_development(api,PACKAGE,7200)
        except Exception as error:
            state.update(phase='outcome_unconfirmed',error_type=type(error).__name__);save(journal,state)
            raise RuntimeError('Launch outcome uncertain; never retry blindly') from error
        state.update(phase='accepted',response=response.to_dict());save(journal,state)
        exact=KERNEL+'/'+str(response.version_number);state.update(phase='observing',exact_kernel=exact)
    save(DIRECTORY/'state.json',state)
    end=datetime.now(timezone.utc)+timedelta(hours=18)
    try:
        while datetime.now(timezone.utc)<end:
            status=read_with_retry(lambda:api.kernels_status(exact)).status.name
            state.update(kernel_status=status);save(DIRECTORY/'state.json',state)
            if status in ['COMPLETE','ERROR','CANCEL_ACKNOWLEDGED']:break
            time.sleep(60)
        if state.get('kernel_status') in ['COMPLETE','ERROR']:
            pattern=r'(^|/)(benchmark\.json|hydra_.*\.json|paired-gameplay-report\.json|serving-effect\.json|model-routing\.json|serve\.log)$|transcripts/.*\.txt$'
            read_with_retry(lambda:api.kernels_output(exact,str(OUTPUT),file_pattern=pattern,quiet=True))
        if state.get('kernel_status')!='COMPLETE':raise RuntimeError('Exact paired screen is not COMPLETE; inspect its retained logs')
        from scripts.analyze_duck_run import analyze
        report=json.loads((OUTPUT/'paired-gameplay-report.json').read_text())
        for name in ['base','adapted']:
            analysis=analyze(OUTPUT/name)
            if analysis['games']!=5 or not analysis['model_gameplay_verified']:raise ValueError('All ten actual model-gameplay records required')
            lifecycle=json.loads((OUTPUT/name/'hydra_lifecycle.json').read_text())
            if lifecycle['phase']!='run_finished' or lifecycle.get('error'):raise ValueError('Actual arm lifecycle incomplete')
            routes=json.loads((OUTPUT/name/'model-routing.json').read_text())
            expected='flashnext'+(':pilot' if name=='adapted' else '')
            if len(routes)!=5 or any(row['requested_model']!=expected or row['resolved_model']!=expected for row in routes):
                raise ValueError('Actual agent adapter routing was not verified for all games')
        actual=json.loads((OUTPUT/'hydra_lora_gameplay_provenance.json').read_text())
        if actual!=provenance:raise ValueError('Executed adapter evaluation provenance changed')
        save(DIRECTORY/'comparison.json',report)
        state.update(phase='screen_complete',comparison=report,
            next_action='Assess meaningful actual gameplay gain, then compare with incumbent FlashNext before any official candidate promotion.')
        save(DIRECTORY/'state.json',state)
    except Exception as error:
        state.update(phase='observation_stopped',error_type=type(error).__name__,reason=str(error));save(DIRECTORY/'state.json',state);raise


if __name__=='__main__':main()
