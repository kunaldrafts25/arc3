"""Read-only observer for the explicitly requested late evaluation; never submits."""
from datetime import datetime, timedelta, timezone
import json
import os
import time

from scripts.submit_arc3_late import ROOT, DIRECTORY, COMPETITION
from scripts.run_prediction_ablation import read_with_retry, save


def main():
    attempt=json.loads((DIRECTORY/'attempt.json').read_text())
    if attempt['phase']!='accepted':raise RuntimeError('No acknowledged late submission to observe')
    with (DIRECTORY/'watcher.lock').open('x',encoding='utf-8') as stream:stream.write(str(os.getpid()))
    ref=int(attempt['submission_ref'])
    token=ROOT/'.kaggle/access_token'
    os.environ['KAGGLE_API_TOKEN']=token.read_text(encoding='utf-8-sig').strip()
    os.environ['KAGGLE_CONFIG_DIR']=str(token.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    path=DIRECTORY/'state.json'
    state=dict(phase='observing',pid=os.getpid(),submission_ref=ref,post_deadline=True,
        competition_standing='Not an on-time final competition entry')
    until=datetime.now(timezone.utc)+timedelta(hours=12)
    save(path,state)
    while datetime.now(timezone.utc)<until:
        rows=read_with_retry(lambda:api.competition_submissions(COMPETITION))
        row=next((x for x in rows if int(x.ref)==ref),None)
        if row is not None:
            state.update(status=row.status.name,score=row.public_score)
            if row.status.name in ('COMPLETE','ERROR'):
                state['phase']='terminal'
                leaders=read_with_retry(lambda:api.competition_leaderboard_view(COMPETITION,page_size=10))
                state['leaders']=[dict(team=x.team_name,score=x.score) for x in leaders]
                save(path,state);return
        save(path,state)
        print(json.dumps(dict(submission_ref=ref,status=state.get('status'),at=state['recorded_at'])),flush=True)
        time.sleep(60)
    state['phase']='observation_window_expired';save(path,state)


if __name__=='__main__':main()
