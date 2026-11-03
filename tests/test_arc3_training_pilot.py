"""Protect shared GPU budgets and deployment-compatible adapter placement."""
from collections import Counter
import json
from pathlib import Path
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import threading
from uuid import uuid4

import pytest

from hydra.arc3_lora_trainer import select_lora_targets
from hydra.arc3_lora_gameplay import verify_serving_effect,append_routing_record
from scripts.run_arc3_training_pilot import KNOWN, resource_decision
from scripts.run_arc3_lora_gameplay import resource_decision as gameplay_resources


def test_resource_floor_accounts_for_both_capped_jobs():
    assert resource_decision(25200,0,False,[dict(kernel=KNOWN)])[0]
    assert not resource_decision(25199,0,False,[dict(kernel=KNOWN)])[0]
    assert resource_decision(18000,0,False,[])[0]
    assert not resource_decision(17999,0,False,[])[0]


def test_shared_arc2_and_paid_usage_block_training():
    assert not resource_decision(100000,0,False,[dict(kernel='kunalsinghh25/arc2-active')])[0]
    assert not resource_decision(100000,1,False,[])[0]
    assert not resource_decision(100000,0,True,[])[0]
    assert not resource_decision(100000,0,False,[dict(kernel=KNOWN),dict(kernel='other/notebook')])[0]


def test_gameplay_keeps_final_official_budget_and_arc2_floor():
    assert gameplay_resources(50400,0,False,[])[0]
    assert not gameplay_resources(50399,0,False,[])[0]
    assert gameplay_resources(57600,0,False,[dict(kernel=KNOWN)])[0]
    assert not gameplay_resources(57599,0,False,[dict(kernel=KNOWN)])[0]
    assert not gameplay_resources(100000,0,False,[dict(kernel='arc2/shared-active')])[0]
    assert not gameplay_resources(100000,1,False,[])[0]
    assert not gameplay_resources(100000,0,True,[])[0]


def test_supported_targets_against_executed_native_inventory():
    root=Path(__file__).resolve().parents[1]
    report=json.loads((root/'reports/kaggle/training-environment-cpu-probe-v1/training-environment-probe.json').read_text())
    inventory={r['name']:r for r in report['linear_modules']}
    names=select_lora_targets([*inventory,'model.visual.blocks.0.q_proj','lm_head',
        'model.language_model.layers.0.linear_attn.in_proj_b'])
    assert len(names)==400
    assert sum(16*(inventory[n]['in_features']+inventory[n]['out_features']) for n in names)==108789760
    assert Counter(n.rsplit('.',1)[-1] for n in names)==dict(
        q_proj=16,k_proj=16,v_proj=16,o_proj=16,in_proj_qkv=48,in_proj_z=48,
        out_proj=48,gate_proj=64,up_proj=64,down_proj=64)


@pytest.mark.parametrize('effect',[True,False])
def test_adapter_inventory_and_effect_are_checked(monkeypatch,effect):
    observed=[]
    def opener(request,timeout):
        if isinstance(request,str):
            return BytesIO(json.dumps(dict(data=[dict(id='flashnext'),dict(id='pilot',parent='flashnext')])).encode())
        body=json.loads(request.data);observed.append(body['lora_path'])
        probability=-0.5-(0.01 if effect and body['lora_path']=='pilot' else 0)
        return BytesIO(json.dumps(dict(text='observe',meta_info=dict(output_token_logprobs=[[probability,42,'observe']]))).encode())
    monkeypatch.setattr('hydra.arc3_lora_gameplay.urlopen',opener)
    if effect:
        report=verify_serving_effect(8001,'flashnext')
        assert all(row['changed'] for row in report['probability_probes'])
    else:
        with pytest.raises(ValueError,match='No observed serving effect'):verify_serving_effect(8001,'flashnext')
    assert observed==[None,'pilot']*3


def test_concurrent_game_starts_publish_one_complete_routing_snapshot():
    directory=Path(__file__).resolve().parents[1]/'.tmp'/('arc3-routing-'+uuid4().hex)
    directory.mkdir(parents=True);path=directory/'routing.json';records=[];lock=threading.Lock()
    try:
        with ThreadPoolExecutor(max_workers=8) as workers:
            list(workers.map(lambda i:append_routing_record(path,records,lock,dict(dispatch_index=i,model='flashnext:pilot')),range(50)))
        actual=json.loads(path.read_text())
        assert len(actual)==50 and {r['dispatch_index'] for r in actual}==set(range(50))
        assert not path.with_suffix('.tmp').exists()
    finally:
        for child in directory.iterdir():child.unlink()
        directory.rmdir()
