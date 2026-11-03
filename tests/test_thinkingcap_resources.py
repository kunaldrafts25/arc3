import pytest
from scripts.run_thinkingcap_comparison import PREDICTION,resource_decision,validate_package


@pytest.mark.parametrize('available,reserved,paid,active,status,allowed',[
    (101286,0,False,[dict(kernel=PREDICTION.rsplit('/',1)[0],status='QUEUED')],'QUEUED',True),
    (25199,0,False,[],'QUEUED',False),
    (25200,0,False,[],'QUEUED',True),
    (18000,0,False,[],'COMPLETE',True),
    (17999,0,False,[],'COMPLETE',False),
    (101286,1,False,[],'QUEUED',False),
    (101286,0,True,[],'QUEUED',False),
    (101286,0,False,[dict(kernel='kunalsinghh25/arc2',status='QUEUED')],'QUEUED',False),
    (101286,0,False,[dict(kernel='kunalsinghh25/arc2',status='RUNNING')],'QUEUED',False),
    (101286,0,False,[],'RUNNING',False),
])
def test_explicit_queue_budget_and_shared_job_exclusion(available,reserved,paid,active,status,allowed):
    assert resource_decision(available,reserved,paid,active,status)[0] is allowed


def test_exact_frozen_checkpoint_and_existing_queue_entry():
    result=validate_package()
    assert result['wall_seconds']==7200 and result['launched'] is False
