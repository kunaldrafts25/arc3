"""Prevent an unvalidated or uncertain deadline mutation from consuming another entry."""
from types import SimpleNamespace

import pytest

from scripts import watch_arc3_deadline as watcher


def test_failed_gameplay_gate_cannot_submit(tmp_path):
    def forbidden(*args,**kwargs):raise AssertionError('API must not be called')
    api=SimpleNamespace(competition_submit_code=forbidden)
    with pytest.raises(ValueError,match='gameplay'):
        watcher.submit_once(api,dict(qualifies_for_deadline_submission=False),tmp_path/'intent.json')


def test_new_submission_prevents_deadline_mutation(tmp_path,monkeypatch):
    monkeypatch.setattr(watcher,'validate',lambda:None)
    api=SimpleNamespace(competition_submissions=lambda c:[SimpleNamespace(ref=12345)])
    with pytest.raises(RuntimeError,match='changed'):
        watcher.submit_once(api,dict(qualifies_for_deadline_submission=True),tmp_path/'intent.json')
    assert not (tmp_path/'intent.json').exists()


def test_uncertain_submission_is_journaled_and_never_retried(tmp_path,monkeypatch):
    monkeypatch.setattr(watcher,'validate',lambda:None)
    monkeypatch.setattr(watcher,'resources',lambda *a,**k:dict(allowed=True))
    monkeypatch.setattr(watcher,'DIRECTORY',tmp_path)
    (tmp_path/'comparison.json').write_text('{}')
    calls=[]
    def uncertain(**kwargs):
        calls.append(kwargs)
        assert (tmp_path/'intent.json').exists()
        raise TimeoutError('Accepted or not: outcome unknown')
    api=SimpleNamespace(
        competition_submissions=lambda c:[SimpleNamespace(ref=ref,status=SimpleNamespace(name='COMPLETE')) for ref in watcher.KNOWN_REFS],
        competition_get_submission_limits=lambda c:SimpleNamespace(num_allowed_now=1),
        kernels_status=lambda k:SimpleNamespace(status=SimpleNamespace(name='COMPLETE')),
        competition_leaderboard_view=lambda *a,**k:[SimpleNamespace(team_name='competitor',score='75.56')],
        competition_submit_code=uncertain)
    comparison=dict(qualifies_for_deadline_submission=True,decision='validated',limitations='one public draw')
    result=watcher.submit_once(api,comparison,tmp_path/'intent.json')
    assert result['phase']=='outcome_unconfirmed'
    assert len(calls)==1 and calls[0]['kernel_version']==1
    with pytest.raises(FileExistsError):
        watcher.submit_once(api,comparison,tmp_path/'intent.json')
    assert len(calls)==1


def test_active_shared_job_waits_without_mutation(tmp_path,monkeypatch):
    monkeypatch.setattr(watcher,'validate',lambda:None)
    monkeypatch.setattr(watcher,'DIRECTORY',tmp_path)
    monkeypatch.setattr(watcher,'resources',lambda *a,**k:dict(allowed=False,pay_to_scale_enabled=False))
    api=SimpleNamespace(
        competition_submissions=lambda c:[SimpleNamespace(ref=ref,status=SimpleNamespace(name='COMPLETE')) for ref in watcher.KNOWN_REFS],
        competition_get_submission_limits=lambda c:SimpleNamespace(num_allowed_now=1))
    result=watcher.submit_once(api,dict(qualifies_for_deadline_submission=True),tmp_path/'intent.json')
    assert result is None and not (tmp_path/'intent.json').exists()
