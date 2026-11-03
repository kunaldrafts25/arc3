from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.build_prediction_notebook import package
from scripts.run_prediction_ablation import accepted_exact, launch_development, pid_alive, read_with_retry, resource_decision, validate_packages

ROOT = Path(__file__).resolve().parents[1]


def plan():
    return json.loads((ROOT/'reports/arc3/prediction-ablation/plan.json').read_text())


@pytest.mark.parametrize('available,reserved,paid,active,at,allowed', [
    (108000,0,False,[],'2026-10-30T23:59:59+00:00',False),
    (402.27,0,False,[],'2026-10-31T00:00:01+00:00',False),
    (108000,120,False,[],'2026-10-31T00:00:01+00:00',False),
    (108000,0,True,[],'2026-10-31T00:00:01+00:00',False),
    (108000,0,False,[{'kernel':'arc2','status':'RUNNING'}],'2026-10-31T00:00:01+00:00',False),
    (25200,0,False,[],'2026-10-31T00:00:01+00:00',True),
    (25199,0,False,[],'2026-10-31T00:00:01+00:00',False),
    (108000,0,False,[],'2026-11-01T06:00:00+00:00',False),
])
def test_free_resource_window_and_shared_compute_guards(available,reserved,paid,active,at,allowed):
    decision, _ = resource_decision(plan(),available,reserved,paid,active,2,datetime.fromisoformat(at))
    assert decision == allowed


def test_short_development_window_does_not_shorten_official_candidate_budget():
    notebook, metadata, provenance = package(32400,7200)
    assert provenance['notebook_wall_budget_seconds'] == 32400
    assert metadata['enable_internet'] is False
    assert metadata['competition_sources'] == ['arc-prize-2026-arc-agi-3']
    run = next(c['source'] for c in notebook['cells'] if c['source'].startswith("print('Starting benchmark...')"))
    end = run.index("_hydra_context['games'] = len(bm.games)")
    start = run.rindex('if not TRUE_SUBMISSION:',0,end)
    hook = run[start:end]
    from datetime import timedelta
    base = datetime(2026,10,31,tzinfo=timezone.utc)
    clock = SimpleNamespace(now=lambda:base)
    for competition in (False,True):
        solver = SimpleNamespace(max_runtime_s_per_game=31800)
        namespace = dict(TRUE_SUBMISSION=competition,bm=SimpleNamespace(solver=solver),
                         soft_end=base+timedelta(seconds=31800),datetime=clock,timedelta=timedelta)
        exec(hook,namespace)
        expected = 31800 if competition else 7200
        assert solver.max_runtime_s_per_game == expected
        assert namespace['soft_end'] == base+timedelta(seconds=expected)


def test_only_exact_frozen_original_account_offline_arc3_packages_pass():
    validate_packages(plan())
    altered = plan()
    altered['variants'][0]['kernel'] = 'another-account/candidate'
    with pytest.raises(ValueError, match='Unexpected'):
        validate_packages(altered)


def test_transient_reads_retry_but_permanent_authorization_failure_does_not():
    from requests import Response
    from requests.exceptions import ConnectionError, HTTPError
    calls, sleeps = [], []
    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError('synthetic')
        return 'COMPLETE'
    assert read_with_retry(flaky,sleep=sleeps.append) == 'COMPLETE'
    assert len(calls) == 3 and sleeps == [60,60]
    response = Response()
    response.status_code = 403
    with pytest.raises(HTTPError):
        read_with_retry(lambda:(_ for _ in ()).throw(HTTPError(response=response)),sleep=sleeps.append)
    assert sleeps == [60,60]


def test_development_launch_has_external_hard_timeout_and_pinned_accelerator():
    calls = []
    def push(*args,**kwargs):
        calls.append((args,kwargs))
        return 'accepted'
    assert launch_development(SimpleNamespace(kernels_push=push),Path('frozen-candidate'),7200) == 'accepted'
    assert len(calls) == 1
    assert calls[0][1] == dict(timeout='7200',acc='NvidiaRtxPro6000')
    with pytest.raises(ValueError,match='two-hour'):
        launch_development(SimpleNamespace(kernels_push=push),Path('frozen-candidate'),7201)
    assert len(calls) == 1


def test_recovery_requires_acknowledged_exact_frozen_version():
    variant = plan()['variants'][0]
    intent = dict(phase='accepted',kernel=variant['kernel'],files=variant['files'],
                  hard_session_timeout_seconds=7200,response={'versionNumber':1})
    assert accepted_exact(variant,intent) == variant['kernel']+'/1'
    for field,value in [('phase','outcome_unconfirmed'),('files',{}),
                        ('hard_session_timeout_seconds',32400),('response',{})]:
        bad = dict(intent,**{field:value})
        with pytest.raises(RuntimeError):
            accepted_exact(variant,bad)


def test_current_process_prevents_duplicate_observer_recovery():
    import os
    assert pid_alive(os.getpid())


def test_false_gpu_summary_cannot_hide_live_arc2_job(monkeypatch):
    from datetime import timedelta
    from scripts import run_prediction_ablation as runner
    at=datetime(2026,10,31,1,tzinfo=timezone.utc)
    monkeypatch.setattr(runner,'now',lambda:at)
    gpu=SimpleNamespace(total_time_allowed=timedelta(hours=30),time_used=timedelta(),
                        time_reserved=timedelta(),is_pay_to_scale_enabled=False)
    calls=[]
    def status(ref):
        calls.append(ref)
        return SimpleNamespace(status=SimpleNamespace(name='RUNNING'))
    api=SimpleNamespace(quota_view=lambda:SimpleNamespace(gpu_quota=gpu,quota_refresh_time='2026-11-07'),
        kernels_list=lambda **kwargs:[SimpleNamespace(ref='kunalsinghh25/arc2-live',enable_gpu=False,last_run_time=at)],
        kernels_status=status)
    result=runner.inspect_resources(api,plan(),2)
    assert calls==['kunalsinghh25/arc2-live']
    assert not result['allowed'] and result['active_gpu_jobs'][0]['kernel']=='kunalsinghh25/arc2-live'


def test_future_cpu_model_probe_drops_overriding_machine_type(tmp_path,monkeypatch):
    from scripts import build_arc3_model_probe as builder
    # Use the real frozen input metadata; only redirect the generated output.
    original=builder.ROOT
    metadata=json.loads((original/'notebooks/arc3_prediction_ablation_v2/control/kernel-metadata.json').read_text())
    source=tmp_path/'notebooks/arc3_prediction_ablation_v2/control'
    source.mkdir(parents=True)
    (source/'kernel-metadata.json').write_text(json.dumps(metadata))
    monkeypatch.setattr(builder,'ROOT',tmp_path)
    builder.build()
    generated=json.loads((tmp_path/'notebooks/model_compatibility_cpu_probe_v2/kernel-metadata.json').read_text())
    assert generated['enable_gpu'] is False and not generated.get('machine_shape')
