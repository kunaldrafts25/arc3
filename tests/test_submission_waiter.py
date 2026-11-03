from types import SimpleNamespace as NS

import pytest

from scripts.submit_flexible_when_available import attempt


class Api:
    def __init__(self,allowed=1,refs=(1,),failure=False):
        self.allowed=allowed;self.refs=refs;self.failure=failure;self.calls=[]
    def competition_submissions(self,*args):return [NS(ref=r) for r in self.refs]
    def competition_get_submission_limits(self,*args):return NS(num_allowed_now=self.allowed)
    def kernels_status(self,*args):return NS(status=NS(name='COMPLETE'))
    def competition_submit_code(self,**kwargs):
        self.calls.append(kwargs)
        if self.failure:raise TimeoutError('response lost')
        return NS(ref=123)


def state():return dict(phase='waiting',known_submission_refs=[1])


def test_no_allowance_never_attempts_mutation():
    api=Api(allowed=0);s=state()
    attempt(api,s,lambda:None,lambda s:None)
    assert s['phase']=='waiting' and not api.calls


def test_exact_version_is_submitted_once_after_intent_is_saved():
    api=Api();s=state();saved=[]
    attempt(api,s,lambda:None,lambda s:saved.append(dict(s)))
    assert saved[0]['phase']=='submitting' and s['submission_ref']==123
    assert api.calls[0]['kernel_version']==3
    attempt(api,s,lambda:None,lambda s:None)
    assert len(api.calls)==1


def test_ambiguous_mutation_is_never_retried():
    api=Api(failure=True);s=state()
    attempt(api,s,lambda:None,lambda s:None)
    assert s['phase']=='submission_outcome_unconfirmed'
    attempt(api,s,lambda:None,lambda s:None)
    assert len(api.calls)==1


def test_new_user_submission_supersedes_waiting_job():
    api=Api(refs=(1,2));s=state()
    attempt(api,s,lambda:None,lambda s:None)
    assert s['phase']=='superseded' and not api.calls


def test_failed_source_or_credential_validation_cannot_submit():
    api=Api();s=state()
    def invalid():raise ValueError('changed source')
    with pytest.raises(ValueError):attempt(api,s,invalid,lambda s:None)
    assert s['phase']=='waiting' and not api.calls


def test_failed_intent_journal_write_prevents_mutation_and_reentry():
    api=Api();s=state()
    def failed_save(s):raise OSError('disk unavailable')
    with pytest.raises(OSError):attempt(api,s,lambda:None,failed_save)
    assert s['phase']=='submitting' and not api.calls
    attempt(api,s,lambda:None,lambda s:None)
    assert not api.calls


def test_nonterminal_notebook_cannot_be_submitted():
    api=Api();s=state()
    api.kernels_status=lambda *args:NS(status=NS(name='RUNNING'))
    attempt(api,s,lambda:None,lambda s:None)
    assert s['phase']=='candidate_not_complete' and not api.calls


def test_lost_acceptance_journal_does_not_allow_a_second_mutation():
    api=Api();s=state();saved=[]
    def save(s):
        if s['phase']=='accepted':raise OSError('write failed')
        saved.append(dict(s))
    with pytest.raises(OSError):attempt(api,s,lambda:None,save)
    assert saved[0]['phase']=='submitting' and len(api.calls)==1
    attempt(api,s,lambda:None,lambda s:None)
    assert len(api.calls)==1
