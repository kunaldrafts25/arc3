from itertools import product
from types import SimpleNamespace as NS

import pytest

from hydra.grid_inspection import install


def context(text='BBwwBB\nRRYRYY',step=2,level=1):
    rows=text.splitlines()
    frame=NS(ascii=text,step=step,level=level,shape=(len(rows),len(rows[0])))
    ns=dict(current_frame=frame,history=[]);events=install(ns)
    return ns,events


def test_runs_partition_all_small_binary_rows_and_preserve_absolute_crop_coordinates():
    # Exhaustive independent reconstruction catches boundary arithmetic errors,
    # including the endpoint defect seen in the actual model-written parser.
    for length in range(1,9):
        for letters in product('BW',repeat=length):
            ns,_=context(''.join(letters))
            for start,stop in ((0,length),(length//2,length)):
                result=ns['row_runs'](0,cols=(start,stop))
                recovered=[];position=start
                for run in result['runs']:
                    assert run['col_start']==position<run['col_stop']<=stop
                    recovered.extend([run['color']]*(run['col_stop']-position));position=run['col_stop']
                assert position==stop and recovered==list(letters[start:stop])


def test_exact_cells_disambiguate_row_col_and_reject_negative_or_bool_indices():
    ns,_=context();result=ns['read_cells']([(1,2),(0,4)])
    assert [x['color'] for x in result['cells']]==['Y','B']
    for point in ((-1,0),(0,-1),(True,0),(0,6),(2,0)):
        with pytest.raises(ValueError):ns['read_cells']([point])


def test_region_sample_labels_raw_coordinates_without_claiming_tile_semantics():
    ns,_=context('BWRY\nYRBW\nWRYB\nRYBW')
    result=ns['read_region']((1,4,0,4),stride=(2,2))
    assert result['row_coordinates']==[1,3] and result['col_coordinates']==[0,2]
    assert result['colors']==['YB','RB'] and result['stop_exclusive']
    assert result['sampling']=='exact pixels, not cell aggregation'


def test_past_steps_are_exact_and_future_or_ambiguous_steps_are_rejected():
    ns,_=context();old,_=context('YY\nBB',step=0)
    ns['history']=[NS(frame=old['current_frame'])]
    assert ns['read_cells']([(0,0)],step=0)['cells'][0]['color']=='Y'
    with pytest.raises(ValueError,match='not in supplied'):ns['read_cells']([(0,0)],step=900)
    other,_=context('BB\nYY',step=0)
    ns['history'].append(NS(frame=other['current_frame']))
    with pytest.raises(ValueError,match='ambiguous'):ns['row_runs'](0,step=0)


def test_frame_lookup_tracks_namespace_after_an_action_refresh():
    ns,events=context();other,_=context('YY\nBB',step=3)
    ns['current_frame']=other['current_frame']
    result=ns['read_cells']([(0,0)])
    assert result['step']==3 and result['cells'][0]['color']=='Y'
    assert events==[dict(tool='read_cells',step=3,level=1,returned_cells=1)]


def test_outputs_and_usage_telemetry_are_bounded():
    ns,events=context('\n'.join(['B'*64]*64))
    with pytest.raises(ValueError,match='256'):ns['read_region']((0,64,0,64))
    assert len(ns['read_region']((2,64,2,64),stride=(4,4))['colors'])==16
    for _ in range(100):ns['read_cells']([(0,0)])
    assert len(events)==64
    assert events[-1]['additional_calls_not_logged']==37


def test_ragged_or_inconsistent_frames_are_not_silently_interpreted():
    ns,_=context('BBB\nB')
    with pytest.raises(ValueError,match='rectangular'):ns['read_cells']([(0,0)])
    ns,_=context();ns['current_frame'].shape=(1,1)
    with pytest.raises(ValueError,match='dimensions'):ns['row_runs'](0)


def test_explicit_frame_must_belong_to_current_game_observations():
    ns,_=context();other,_=context()
    assert ns['read_cells']([(0,0)],frame=ns['current_frame'])['cells'][0]['color']=='B'
    with pytest.raises(ValueError,match='not in supplied'):
        ns['read_cells']([(0,0)],frame=other['current_frame'])


def test_actual_composed_child_returns_inspection_results_and_adoption_events(monkeypatch):
    import json,subprocess,sys
    from pathlib import Path
    from uuid import uuid4
    from scripts.install_verified_agent import patched_sources as base_patch
    from scripts.install_inspection_agent import patched_sources
    root=Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root/'vendor/duck-m2/ARC3-Inference'))
    source=root/'vendor/duck-m2/ARC3-Inference/inference/agent'
    sandbox,agent=base_patch((source/'python_tool_sandbox.py').read_text(),(source/'tool_agent.py').read_text(),
        (root/'hydra/verified_planning.py').read_text(),enforce_probes=False)
    sandbox,agent=patched_sources(sandbox,agent,(root/'hydra/grid_inspection.py').read_text())
    module={'__name__':'inspection_sandbox_test'};exec(compile(sandbox,'inspection-sandbox','exec'),module)
    assert len(module['_SANDBOX_BOOTSTRAP'].encode())<120000
    folder=root/'test-artifacts';folder.mkdir(exist_ok=True)
    path=folder/('inspection-bootstrap-'+uuid4().hex+'.py');path.write_text(module['_SANDBOX_BOOTSTRAP'])
    old=dict(grid=[[11,11],[5,5]],ascii='YY\nBB',shape=[2,2],step=0,level=1)
    now=dict(grid=[[5,5,1,1,5,5]],ascii='BBwwBB',shape=[1,6],step=1,level=1)
    request=dict(code="result=[read_cells([(0,1)],step=0),row_runs(0)]",timeout_seconds=5,
        color_chars='WwgGcBMPRbSYOrNp',state=dict(current_frame=now,history=[dict(action='',frame=old)],valid_actions=['RIGHT']))
    process=subprocess.run([sys.executable,'-I','-S',str(path)],input=json.dumps(request)+'\n',text=True,capture_output=True,timeout=10)
    messages=[json.loads(line) for line in process.stdout.splitlines() if line.startswith('{')]
    assert messages,(process.stdout,process.stderr)
    result=messages[-1];assert not result.get('error'),result
    assert result['result'][0]['cells'][0]['color']=='Y'
    assert result['result'][1]['runs'][1]==dict(col_start=2,col_stop=4,color='w')
    assert [e['tool'] for e in result['hydra_inspection_events']]==['read_cells','row_runs']
