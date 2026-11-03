"""One journaled attempt to submit the already-validated flexible notebook.

Waits on authoritative daily allowance; never retries an uncertain mutation.
Aborts if another submission appears or the local credential changes.
"""
import argparse
from datetime import datetime,timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
COMPETITION='arc-prize-2026-arc-agi-3'
KERNEL='kunalsinghh25/arc-hydra-ultimate-candidate'
VERSION=3
MESSAGE='ARC Hydra flexible v3 full-budget official comparison; development 48.29 at two hours; official result unverified'


def attempt(api,state,validate,save):
    if state['phase']!='waiting':return state
    current=api.competition_submissions(COMPETITION)
    if {int(s.ref) for s in current}-set(state['known_submission_refs']):
        state.update(phase='superseded',reason='Another submission appeared after this job was armed')
        save(state);return state
    limits=api.competition_get_submission_limits(COMPETITION)
    state['last_allowed_now']=int(limits.num_allowed_now)
    if limits.num_allowed_now<1:
        save(state);return state
    validate()
    status=api.kernels_status(KERNEL+'/'+str(VERSION)).status.name
    if status!='COMPLETE':
        state.update(phase='candidate_not_complete',kernel_status=status);save(state);return state
    # Persist intent BEFORE issuing the non-idempotent API call. A timeout after
    # this point requires reconciliation, never automatic resubmission.
    state.update(phase='submitting',attempt_started_at=datetime.now(timezone.utc).isoformat())
    save(state)
    try:
        response=api.competition_submit_code(file_name='submission.parquet',message=MESSAGE,
            competition=COMPETITION,kernel=KERNEL,kernel_version=VERSION,quiet=True)
    except Exception as exc:
        state.update(phase='submission_outcome_unconfirmed',error_type=type(exc).__name__)
        save(state);return state
    if int(response.ref or 0)>0:
        state.update(phase='accepted',submission_ref=int(response.ref))
    else:state.update(phase='submission_outcome_unconfirmed',reason='API returned no submission reference')
    save(state);return state


def validate_candidate():
    launch=json.loads((ROOT/'reports/kaggle/ultimate-candidate-v3/launch.json').read_text(encoding='utf-8'))
    assert launch['kernel']==KERNEL+'/'+str(VERSION)
    for name,expected in launch['files'].items():
        if sha256((ROOT/'notebooks/ultimate_candidate'/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Frozen candidate source changed: '+name)
    report=json.loads((ROOT/'reports/kaggle/ultimate-candidate-v3/analysis.json').read_text(encoding='utf-8'))
    if not report['model_gameplay_verified'] or report['games']!=25:
        raise ValueError('Candidate gameplay evidence incomplete')
    if abs(report['mean_public_score']-48.2861310586818)>1e-8:
        raise ValueError('Unexpected candidate evidence')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait-until',required=True,help='Timezone-aware latest attempt time; no retry beyond it')
    args=parser.parse_args();until=datetime.fromisoformat(args.wait_until)
    if until.tzinfo is None:parser.error('--wait-until needs timezone')
    if not datetime.now(timezone.utc)<until:parser.error('Attempt window already expired')
    validate_candidate()
    token_path=ROOT/'.kaggle/access_token'
    token=token_path.read_text(encoding='utf-8-sig').strip()
    token_digest=sha256(token.encode()).digest()
    os.environ['KAGGLE_API_TOKEN']=token;os.environ['KAGGLE_CONFIG_DIR']=str(token_path.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    if api.quota_view().gpu_quota.is_pay_to_scale_enabled:
        raise RuntimeError('Paid scaling is enabled; this job is only authorized for free evaluation')
    current=api.competition_submissions(COMPETITION)
    if any(s.status.name not in ('COMPLETE','ERROR') for s in current):
        raise RuntimeError('Another official submission is not terminal')
    directory=ROOT/'reports/kaggle/flexible-official-rerun';directory.mkdir(exist_ok=True)
    lock=directory/'attempt.lock'
    with lock.open('x',encoding='utf-8') as stream:stream.write(str(os.getpid()))
    state=dict(phase='waiting',kernel=KERNEL+'/'+str(VERSION),competition=COMPETITION,
        armed_at=datetime.now(timezone.utc).isoformat(),wait_until=until.isoformat(),
        known_submission_refs=[int(s.ref) for s in current],official_score=None)
    path=directory/'state.json'
    def save(value):
        value['checked_at']=datetime.now(timezone.utc).isoformat()
        temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');temporary.replace(path)
    def validate():
        if (directory/'cancel.requested').exists():raise RuntimeError('Submission job cancelled locally')
        if sha256(token_path.read_text(encoding='utf-8-sig').strip().encode()).digest()!=token_digest:
            raise RuntimeError('Credential changed after job was armed')
        validate_candidate()
        if api.quota_view().gpu_quota.is_pay_to_scale_enabled:raise RuntimeError('Paid scaling enabled after arming')
    save(state);errors=0
    print('Waiting for official allowance for exact',state['kernel'],flush=True)
    while datetime.now(timezone.utc)<until and state['phase']=='waiting':
        try:
            validate()
            attempt(api,state,validate,save)
            errors=0
        except Exception as exc:
            errors+=1
            print('Read/validation stopped this check:',type(exc).__name__,flush=True)
            if state['phase']!='waiting':
                state.update(phase='submission_outcome_unconfirmed',error_type=type(exc).__name__)
                save(state);break
            if isinstance(exc,(RuntimeError,ValueError,AssertionError)) or errors>=5:
                state.update(phase='preflight_failed',error_type=type(exc).__name__);save(state);break
        if state['phase']=='waiting':time.sleep(60)
    if state['phase']=='waiting':state['phase']='window_expired';save(state)
    print(json.dumps(state),flush=True)


if __name__=='__main__':main()
