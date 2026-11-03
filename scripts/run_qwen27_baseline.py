"""Launch/observe one frozen ARC3 27B baseline; never train or submit officially."""
import argparse
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import time

from scripts.build_qwen27_probe import TARGET,DRAFT
from scripts.run_prediction_ablation import (
    inspect_resources,launch_development,read_with_retry,save,download_and_analyze,
)

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'notebooks/qwen27_matched_baseline'
DIRECTORY=ROOT/'reports/arc3/qwen27-baseline'
OUTPUT=ROOT/'reports/kaggle/qwen27-matched-baseline-v1'
KERNEL='kunalsinghh25/arc-hydra-qwen27-matched-baseline'
TERMINAL={'COMPLETE','ERROR','CANCEL_ACKNOWLEDGED'}


def validate_package(package=PACKAGE):
    manifest=json.loads((package/'manifest.json').read_text())
    metadata=json.loads((package/'kernel-metadata.json').read_text())
    provenance=json.loads((package/'provenance.json').read_text())
    if set(manifest['files'])!={'submission.ipynb','kernel-metadata.json','provenance.json'}:
        raise ValueError('Incomplete frozen package')
    for name,digest in manifest['files'].items():
        if sha256((package/name).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen package changed: '+name)
    if (manifest['kernel']!=KERNEL or manifest['wall_seconds']!=7200
            or metadata['id']!=KERNEL or metadata['enable_internet'] is not False
            or metadata['enable_gpu'] is not True or metadata['enable_tpu'] is not False
            or metadata['is_private'] is not True or metadata['machine_shape']!='NvidiaRtxPro6000'
            or metadata['model_sources']!=[TARGET,DRAFT]
            or metadata['competition_sources']!=['arc-prize-2026-arc-agi-3']
            or metadata['dataset_sources']!=['dfranzen/pennyroyal-v253','dfranzen/taaf-kaggle-source-bundle-copy']
            or metadata['kernel_sources']
            or provenance['official_submission_eligible'] is not False
            or provenance['notebook_wall_budget_seconds']!=7200):
        raise ValueError('Unexpected baseline package, model, accelerator or total budget')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--observe-only',action='store_true')
    args=parser.parse_args()
    if args.run and args.observe_only:raise ValueError('Select launch or read-only reconciliation')
    manifest=validate_package()
    token=ROOT/'.kaggle/access_token'
    os.environ['KAGGLE_API_TOKEN']=token.read_text(encoding='utf-8-sig').strip()
    os.environ['KAGGLE_CONFIG_DIR']=str(token.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    DIRECTORY.mkdir(parents=True,exist_ok=True);OUTPUT.mkdir(parents=True,exist_ok=True)
    journal=OUTPUT/'launch.json'
    if args.observe_only:
        accepted=json.loads(journal.read_text())
        if (accepted['phase']!='accepted' or accepted['kernel']!=KERNEL
                or accepted['files']!=manifest['files'] or accepted['hard_session_timeout_seconds']!=7200):
            raise ValueError('Cannot reconcile an uncertain/mismatched launch')
        exact=KERNEL+'/'+str(accepted['response']['versionNumber'])
        state=dict(accepted,phase='observing',pid=os.getpid(),exact_kernel=exact)
    else:
        plan=json.loads((ROOT/'reports/arc3/prediction-ablation/plan.json').read_text())
        plan['expires']='2026-11-01T18:00:00+00:00'
        resources=inspect_resources(api,plan,1)
        save(DIRECTORY/'resource-check.json',resources);print(json.dumps(resources,indent=2),flush=True)
        if not args.run:return
        if not resources['allowed']:raise RuntimeError(resources['reason'])
        gate=json.loads((ROOT/'reports/kaggle/qwen27-cpu-preflight-v2/verified.json').read_text())
        if read_with_retry(lambda:api.kernels_status(gate['kernel'])).status.name!='COMPLETE':
            raise RuntimeError('Exact CPU gate is no longer confirmed complete')
        state=dict(phase='launching',kernel=KERNEL,files=manifest['files'],
            hard_session_timeout_seconds=7200,pid=os.getpid(),resources=resources,
            scope='One 25-game ARC3 baseline. No training or official submission.')
        with journal.open('x',encoding='utf-8') as stream:json.dump(state,stream,indent=2)
        try:response=launch_development(api,PACKAGE,7200)
        except Exception as exc:
            state.update(phase='outcome_unconfirmed',error_type=type(exc).__name__);save(journal,state)
            raise RuntimeError('Uncertain launch; reconcile without retrying') from exc
        state.update(phase='accepted',response=response.to_dict());save(journal,state)
        exact=KERNEL+'/'+str(response.version_number)
        state.update(phase='observing',exact_kernel=exact)
    save(DIRECTORY/'state.json',state)
    # This observer can outlive a delayed queue. Observation duration is not GPU time.
    end=datetime.now(timezone.utc)+timedelta(hours=18)
    try:
        while datetime.now(timezone.utc)<end:
            status=read_with_retry(lambda:api.kernels_status(exact)).status.name
            state.update(kernel_status=status);save(DIRECTORY/'state.json',state)
            if status in TERMINAL:break
            time.sleep(60)
        if state.get('kernel_status')!='COMPLETE':
            raise RuntimeError('Not COMPLETE; inspect same exact version without relaunching')
        analysis=download_and_analyze(api,exact,OUTPUT)
        state.update(phase='evaluation_complete',analysis=analysis,
            next_action='Inspect serving and gameplay, compare against incumbent; no automatic training, promotion or submission.')
        save(DIRECTORY/'state.json',state)
    except Exception as exc:
        state.update(phase='observation_stopped',error_type=type(exc).__name__,reason=str(exc))
        save(DIRECTORY/'state.json',state);raise


if __name__=='__main__':main()
