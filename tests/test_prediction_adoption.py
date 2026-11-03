import json

from hydra.prediction_host import PredictionSession
from scripts.analyze_prediction_adoption import analyze


def observed_session(tmp_path):
    state = dict(current_frame=dict(ascii='R',shape=[1,1],step=0,level=1))
    path = tmp_path/'game.prediction.json'
    session = PredictionSession(path,lambda:state)
    session.rpc(dict(operation='start',models=['move','stay'],features={'p':['cell',0,0]},question='Does this pixel change?'))
    session.rpc(dict(operation='forecast',probes={'right':dict(action={'action':'RIGHT'},
        predictions={'move':{'p':'B'},'stay':{'p':'R'}})}))
    def handler(actions,**kwargs):
        state['current_frame'] = dict(ascii='B',shape=[1,1],step=1,level=1)
        return dict(action_result={'executed':True},state=state)
    session.wrap_action(handler)([{'action':'RIGHT'}])
    return session,path.with_suffix('.events.jsonl')


def test_v2_audit_checks_frozen_prospective_evidence_without_counting_archives_twice(tmp_path):
    session,path = observed_session(tmp_path)
    session.rpc(dict(operation='start',models=['fresh'],features={'p':['cell',0,0]},question='Revise the scoped explanation'))
    report = analyze(tmp_path,origin='programmatic')
    assert report['frozen_forecast_archive_complete']
    assert report['counts']['hypothesis_versions_observed'] == 2
    assert report['counts']['actual_resolution_events'] == 1
    assert report['counts']['hypothesis_consistent'] == 1
    assert report['counts']['hypothesis_contradicted'] == 1
    assert report['source_origin'] == 'programmatic'


def test_retrospective_forecast_order_is_not_accepted_as_a_prospective_archive(tmp_path):
    session,path = observed_session(tmp_path)
    events = [json.loads(line) for line in path.read_text().splitlines()]
    events[1],events[2] = events[2],events[1]
    path.write_text(''.join(json.dumps(e)+'\n' for e in events))
    report = analyze(tmp_path)
    assert not report['frozen_forecast_archive_complete'] and report['audit_errors']


def test_consistent_label_cannot_hide_disagreement_with_frozen_values(tmp_path):
    session,path = observed_session(tmp_path)
    events = [json.loads(line) for line in path.read_text().splitlines()]
    event = events[-1]
    event['outcome']['verdicts']['stay']['verdict'] = 'consistent'
    event['evidence']['verdicts']['stay']['verdict'] = 'consistent'
    path.write_text(''.join(json.dumps(e)+'\n' for e in events))
    report = analyze(tmp_path)
    assert not report['frozen_forecast_archive_complete']
    assert any('verdict disagrees' in e['reason'] for e in report['audit_errors'])
