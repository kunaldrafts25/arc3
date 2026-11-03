import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from hydra.study_memory import install,load_store,persist_store,render_panel


def namespace(initial=None,level=1):
    ns=dict(current_frame=SimpleNamespace(step=2,level=level),
            history=[SimpleNamespace(frame=SimpleNamespace(step=s)) for s in (0,1,2)])
    export=install(ns,initial)
    return ns,export


def test_notes_cross_calls_without_aliasing_and_keep_goal_separate():
    ns,export=namespace()
    ns['remember']('motion','RIGHT shifts the selected object',kind='control',
                   status='supported',evidence_steps=[0,1],scope='game',condition='object selected')
    ns['remember']('goal','Match two contacts',kind='goal')
    restored,_=namespace(export())
    assert restored['recall']()['notes']['goal']['status']=='hypothesis'
    assert restored['recall']()['notes']['motion']['evidence_steps']==[0,1]
    copy=restored['recall']();copy['notes'].clear()
    assert len(restored['recall']()['notes'])==2


def test_unobserved_evidence_and_oversized_claim_do_not_mutate_store():
    ns,export=namespace()
    for kwargs in (dict(claim='x',evidence_steps=[999]),dict(claim='x'*241),
                   dict(claim='x',status='supported'),dict(claim='x',kind='certified')):
        with pytest.raises(ValueError):ns['remember']('test',**kwargs)
        assert export()==dict(revision=0,notes={})


def test_prior_level_rules_are_rechecked_and_level_notes_hidden():
    ns,export=namespace()
    ns['remember']('global','Reflection follows the selected axis',scope='game')
    ns['remember']('local','Current goal is at the upper edge')
    panel=render_panel(export(),2)
    assert 'RECHECK' in panel and 'global' in panel and 'local' not in panel
    assert render_panel({},1)==''


def test_host_sidecars_are_isolated_and_atomic_with_update_events():
    root=Path(__file__).resolve().parents[1]/'test-artifacts'/('study-'+uuid4().hex)
    root.mkdir(parents=True)
    ns,export=namespace();ns['remember']('rule','Test a mode change',kind='state')
    a,b=root/'a.study.json',root/'b.study.json'
    persist_store(a,export());persist_store(a,export())
    assert len(a.with_suffix('.events.jsonl').read_text().splitlines())==1
    assert load_store(b)['notes']=={}
    a.write_text('broken JSON')
    assert load_store(a)['notes']=={}


def test_bounded_capacity_explicit_removal_and_panel_limit():
    ns,export=namespace()
    for i in range(10):ns['remember']('n'+str(i),'x'*220)
    with pytest.raises(ValueError,match='capacity'):ns['remember']('extra','x')
    assert len(render_panel(export(),1))<=1800
    ns['remember']('n0',None);ns['remember']('extra','x')
    assert len(export()['notes'])==10 and 'n0' not in export()['notes']


def test_composed_real_child_exports_and_restores_notes(monkeypatch):
    import subprocess,sys
    from scripts.install_verified_agent import patched_sources as base_patch
    from scripts.install_study_agent import patched_sources
    from hydra.research_guidance import GUIDANCE
    root=Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root/'vendor/duck-m2/ARC3-Inference'))
    source=root/'vendor/duck-m2/ARC3-Inference/inference/agent'
    sandbox,agent=base_patch((source/'python_tool_sandbox.py').read_text(),(source/'tool_agent.py').read_text(),
        (root/'hydra/verified_planning.py').read_text(),enforce_probes=False)
    sandbox,agent=patched_sources(sandbox,agent,(root/'hydra/study_memory.py').read_text(),GUIDANCE)
    module={'__name__':'study_sandbox_test'};exec(compile(sandbox,'study-sandbox','exec'),module)
    assert len(module['_SANDBOX_BOOTSTRAP'].encode())<120000
    path=root/'test-artifacts'/('study-bootstrap-'+uuid4().hex+'.py');path.write_text(module['_SANDBOX_BOOTSTRAP'])
    state=dict(current_frame=dict(grid=[[1]],step=1,level=1),
               history=[dict(action='',frame=dict(grid=[[0]],step=0,level=1))],valid_actions=['RIGHT'])
    def call(code,memory=None):
        request=dict(code=code,state={**state,'hydra_study':memory},timeout_seconds=5,color_chars='0123456789ABCDEF')
        result=subprocess.run([sys.executable,'-I','-S',str(path)],input=json.dumps(request)+'\n',text=True,capture_output=True,timeout=10)
        messages=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        assert messages,(result.stdout,result.stderr)
        return messages[-1]
    one=call("remember('control','Check the selected mode',kind='control',status='supported',evidence_steps=[0,1],scope='game')")
    assert not one.get('error') and one['hydra_study']['notes']['control']['kind']=='control'
    two=call('result=recall()',one['hydra_study'])
    assert two['hydra_study']==one['hydra_study']
