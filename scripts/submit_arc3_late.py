"""One explicitly requested post-deadline attempt of the already completed final notebook.

This cannot create an on-time competition entry. No notebook/GPU launch or retry.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os

from scripts.run_arc3_deadline_candidate import ROOT, validate, TERMINAL
from scripts.run_prediction_ablation import save

COMPETITION='arc-prize-2026-arc-agi-3'
KERNEL='kunalsinghh25/arc-hydra-deadline-candidate'
DIRECTORY=ROOT/'reports/arc3/late-submission'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    validate()
    token=ROOT/'.kaggle/access_token'
    os.environ['KAGGLE_API_TOKEN']=token.read_text(encoding='utf-8-sig').strip()
    os.environ['KAGGLE_CONFIG_DIR']=str(token.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    path=DIRECTORY/'attempt.json'
    if path.exists():
        state=json.loads(path.read_text())
        print(json.dumps(state,indent=2));return
    gpu=api.quota_view().gpu_quota
    available=(gpu.total_time_allowed-gpu.time_used-gpu.time_reserved).total_seconds()
    active=[]
    cutoff=datetime.now(timezone.utc)-timedelta(days=2)
    for kernel in api.kernels_list(mine=True,page_size=100,sort_by='dateRun') or []:
        if kernel.last_run_time and kernel.last_run_time.replace(tzinfo=timezone.utc)<cutoff:continue
        status=api.kernels_status(kernel.ref).status.name
        if status not in TERMINAL:active.append(dict(kernel=kernel.ref,status=status))
    current=api.competition_submissions(COMPETITION)
    if any(s.status.name not in ('COMPLETE','ERROR') for s in current):
        raise RuntimeError('Another official ARC3 submission is active')
    if active or gpu.time_reserved.total_seconds() or gpu.is_pay_to_scale_enabled or available<43200:
        raise RuntimeError('Shared job/quota guard refused late submission')
    limits=api.competition_get_submission_limits(COMPETITION)
    if limits.num_allowed_now<1:raise RuntimeError('Kaggle reports no remaining submission allowance')
    if api.kernels_status(KERNEL+'/1').status.name!='COMPLETE':
        raise RuntimeError('Exact final notebook is not complete')
    state=dict(phase='checked',kernel=KERNEL+'/1',available_gpu_seconds=available,
        allowed_now=int(limits.num_allowed_now),active_jobs=active,
        known_submissions=[int(s.ref) for s in current],
        reason='User explicitly requested the last notebook after the competition ended. Earlier deadline promotion gate rejected this candidate. This is a post-deadline attempt, not an on-time entry.',
        competition_deadline_utc='2026-11-02T23:59:00+00:00')
    if not args.execute:
        print(json.dumps(state,indent=2));return
    state['phase']='submitting'
    with path.open('x',encoding='utf-8') as stream:json.dump(state,stream,indent=2)
    try:
        response=api.competition_submit_code(file_name='submission.parquet',
            message='Post-deadline requested evaluation of final frozen ARC3 candidate; not an on-time competition entry',
            competition=COMPETITION,kernel=KERNEL,kernel_version=1,quiet=True)
        ref=int(response.ref or 0)
        state.update(phase='accepted' if ref else 'outcome_unconfirmed',submission_ref=ref or None)
    except Exception as exc:
        response=getattr(exc,'response',None)
        state.update(phase='rejected' if response is not None and 400<=response.status_code<500 else 'outcome_unconfirmed',
            error_type=type(exc).__name__,http_status=getattr(response,'status_code',None))
        if response is not None:
            try:
                body=response.json()
                message=body.get('message',body.get('error',''))
                if isinstance(message,str):state['message']=message[:1200]
            except ValueError:pass
    save(path,state)
    print(json.dumps(state,indent=2))


if __name__=='__main__':main()
