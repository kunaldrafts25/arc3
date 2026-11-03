from datetime import datetime,timedelta
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from scripts.build_duck_notebook import build


def evaluate(competition=False,budget=32400,startup=650):
    notebook,_,provenance=build('benchmark',agent_variant='planning-assist',
        public_runtime_seconds=budget-600,notebook_budget_seconds=budget)
    source=next(c['source'] for c in notebook['cells'] if c['source'].startswith("print('Starting benchmark...')"))
    fragment=source.split('# ARC-Hydra public reproduction; no hidden game selection.\n',1)[1].split("_hydra_context['games']",1)[0]
    root=Path(__file__).resolve().parents[1]/'test-artifacts'/('budget-'+uuid4().hex);root.mkdir(parents=True)
    epoch=1700000000
    now=epoch+startup
    bm=SimpleNamespace(games=[None]*25,n_passes=1,solver=SimpleNamespace(max_runtime_s_per_game=budget-600))
    namespace=dict(TRUE_SUBMISSION=competition,bm=bm,target=SimpleNamespace(max_runtime_s=32400),
        NOTEBOOK_START_TIME=epoch,time=SimpleNamespace(time=lambda:now),
        datetime=SimpleNamespace(now=lambda:datetime.fromtimestamp(now),fromtimestamp=datetime.fromtimestamp),
        timedelta=timedelta,Path=Path,WORKING_DIR=root,json=json)
    exec(compile(fragment,'extended-budget','exec'),namespace)
    return namespace,provenance


def test_full_public_budget_counts_startup_and_has_no_two_hour_cap():
    ns,p=evaluate()
    assert ns['bm'].solver.max_runtime_s_per_game==31150
    assert ns['soft_end']==datetime.fromtimestamp(1700031800)
    assert p['public_deadline_includes_startup']


def test_official_deadline_obeys_smaller_user_budget():
    ns,_=evaluate(competition=True,budget=28800)
    assert ns['soft_end']==datetime.fromtimestamp(1700028200)


def test_startup_cannot_silently_start_gameplay_after_deadline():
    with pytest.raises(RuntimeError,match='Startup consumed'):
        evaluate(startup=32000)


@pytest.mark.parametrize('budget',[0,32401,86400])
def test_invalid_wall_budget_rejected(budget):
    with pytest.raises(ValueError,match='wall budget'):
        build(notebook_budget_seconds=budget)
