"""Observe one frozen screen, submit only on its declared evidence gate, then verify official result.

No GPU launches, training, paid scaling, publication, alternate accounts or mutation retries.
The only optional mutation is one authorized official submission of exact candidate /1.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from scripts.compare_arc3_deadline_candidate import compare
from scripts.run_arc3_deadline_candidate import ROOT, DIRECTORY, OUTPUT, validate, resources, TERMINAL
from scripts.run_prediction_ablation import read_with_retry, save

COMPETITION='arc-prize-2026-arc-agi-3'
KERNEL='kunalsinghh25/arc-hydra-deadline-candidate'
EXACT=KERNEL+'/1'
KNOWN_REFS={57751759,57726784,57686595,57657435,57630597,57601062}


def submit_once(api, comparison, journal):
    """All checks precede exclusive intent persistence; an uncertain mutation never retries."""
    if not comparison['qualifies_for_deadline_submission']:
        raise ValueError('Actual gameplay did not pass the declared deadline choice')
    validate()
    current=read_with_retry(lambda:api.competition_submissions(COMPETITION))
    if {int(s.ref) for s in current}!=KNOWN_REFS:
        raise RuntimeError('ARC3 submissions changed: explicit reconciliation required')
    if any(s.status.name not in ('COMPLETE','ERROR') for s in current):
        raise RuntimeError('Another official ARC3 evaluation is active')
    limits=read_with_retry(lambda:api.competition_get_submission_limits(COMPETITION))
    if int(limits.num_allowed_now)<1:return None
    checked=resources(api,development=False)
    save(DIRECTORY/'official-resource-check.json',checked)
    if not checked['allowed']:
        if checked['pay_to_scale_enabled']:
            raise RuntimeError('Paid scaling enabled; official workflow stopped')
        # A concurrent ARC2 session may finish inside the remaining window.
        # Wait on observations without consuming an entry or reserving a GPU.
        return None
    if read_with_retry(lambda:api.kernels_status(EXACT)).status.name!='COMPLETE':
        raise RuntimeError('Exact validated screen is no longer COMPLETE')
    leaders=read_with_retry(lambda:api.competition_leaderboard_view(COMPETITION,page_size=10))
    state=dict(phase='submitting',kernel=EXACT,started_at=datetime.now(timezone.utc).isoformat(),
        comparison_sha256=sha256((DIRECTORY/'comparison.json').read_bytes()).hexdigest(),
        checked_resources=checked,
        leaders_before=[dict(team=x.team_name,score=x.score) for x in leaders],
        decision=comparison['decision'],limitations=comparison['limitations'])
    with journal.open('x',encoding='utf-8') as stream:json.dump(state,stream,indent=2)
    try:
        response=api.competition_submit_code(file_name='submission.parquet',
            message='ARC3 deadline FlashNext: completed real-game screen; bounded memory plus exact inspection and optional measured predictions; official score unverified',
            competition=COMPETITION,kernel=KERNEL,kernel_version=1,quiet=True)
        ref=int(response.ref or 0)
        state.update(phase='accepted' if ref>0 else 'outcome_unconfirmed',submission_ref=ref or None)
    except Exception as exc:
        state.update(phase='outcome_unconfirmed',error_type=type(exc).__name__)
    save(journal,state)
    return state


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true',help='Monitor and allow one evidence-gated official submission')
    args=parser.parse_args()
    if not args.run:parser.error('Explicit --run required')
    validate()
    launch=json.loads((OUTPUT/'launch.json').read_text())
    if launch['phase']!='accepted' or launch['response']['versionNumber']!=1:
        raise ValueError('Only the accepted exact screen /1 may be observed')
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    with (DIRECTORY/'watcher.lock').open('x',encoding='utf-8') as stream:stream.write(str(os.getpid()))
    token=ROOT/'.kaggle/access_token'
    os.environ['KAGGLE_API_TOKEN']=token.read_text(encoding='utf-8-sig').strip()
    os.environ['KAGGLE_CONFIG_DIR']=str(token.parent)
    token_digest=sha256(os.environ['KAGGLE_API_TOKEN'].encode()).digest()
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    path=DIRECTORY/'watcher-state.json'
    state=dict(phase='screen_observing',pid=os.getpid(),kernel=EXACT,
        scope='One already accepted two-hour development screen and at most one nine-hour official evaluation if its predeclared gameplay gate passes',
        target='Official100 or strictly above the freshly verified competing leader')
    save(path,state)
    journal=DIRECTORY/'official-submission.json'
    try:
        while datetime.now(timezone.utc)<datetime(2026,11,2,12,tzinfo=timezone.utc):
            if (DIRECTORY/'cancel.requested').exists():
                state['phase']='cancelled_before_new_mutation';save(path,state);return
            if sha256(token.read_text(encoding='utf-8-sig').strip().encode()).digest()!=token_digest:
                raise RuntimeError('Original credential changed')
            status=read_with_retry(lambda:api.kernels_status(EXACT)).status.name
            state['kernel_status']=status;save(path,state)
            print(json.dumps(dict(phase=state['phase'],kernel_status=status,at=state['recorded_at'])),flush=True)
            if status=='COMPLETE':break
            if status in TERMINAL:
                state['phase']='screen_failed_no_submission';save(path,state);return
            time.sleep(60)
        if state.get('kernel_status')!='COMPLETE':
            state['phase']='screen_not_complete_before_official_launch_cutoff';save(path,state);return
        subprocess.run([sys.executable,'-X','utf8','-m','scripts.run_arc3_deadline_candidate','--observe'],cwd=ROOT,check=True)
        comparison=compare()
        state.update(phase='screen_compared',comparison={k:comparison[k] for k in
            ('common_gameplay_seconds','common_time','memory_games','memory_changes','qualifies_for_deadline_submission','decision','limitations')})
        save(path,state)
        if not comparison['qualifies_for_deadline_submission']:
            state['phase']='screen_rejected_manual_decision_needed';save(path,state);return
        while datetime.now(timezone.utc)<datetime(2026,11,2,12,tzinfo=timezone.utc):
            if (DIRECTORY/'cancel.requested').exists():
                state['phase']='cancelled_before_submission';save(path,state);return
            result=submit_once(api,comparison,journal)
            if result is not None:break
            state['phase']='waiting_for_official_allowance_or_shared_resources';save(path,state);time.sleep(60)
        else:
            state['phase']='official_launch_window_expired';save(path,state);return
        if result['phase']!='accepted':
            state.update(phase='official_outcome_unconfirmed_no_retry',submission=result);save(path,state);return
        ref=result['submission_ref'];state.update(phase='official_observing',submission_ref=ref);save(path,state)
        while datetime.now(timezone.utc)<datetime(2026,11,3,2,tzinfo=timezone.utc):
            submissions=read_with_retry(lambda:api.competition_submissions(COMPETITION))
            exact=next((s for s in submissions if int(s.ref)==ref),None)
            if exact is not None:
                state.update(official_status=exact.status.name,official_score=exact.public_score)
                save(path,state)
                if exact.status.name in ('COMPLETE','ERROR'):
                    leaders=read_with_retry(lambda:api.competition_leaderboard_view(COMPETITION,page_size=20))
                    own_team=exact.team_name
                    if not own_team:
                        raise RuntimeError('Official submission did not expose our team identity')
                    competing=[x for x in leaders if x.team_name!=own_team]
                    if not competing:raise RuntimeError('No competing leaderboard entries available')
                    top=max(float(x.score) for x in competing)
                    value=float(exact.public_score) if exact.public_score not in (None,'') else None
                    achieved=exact.status.name=='COMPLETE' and value is not None and (value>=100 or value>top)
                    state.update(phase='official_complete_target_met' if achieved else 'official_terminal_target_unmet',
                        freshly_verified_leaders=[dict(team=x.team_name,score=x.score) for x in leaders],
                        verified_own_team=own_team,highest_competing_score=top,target_achieved=achieved)
                    save(path,state);return
            time.sleep(60)
        state['phase']='official_observation_window_expired';save(path,state)
    except Exception as exc:
        state.update(phase='watcher_stopped',error_type=type(exc).__name__,reason=str(exc))
        save(path,state);raise


if __name__=='__main__':main()
