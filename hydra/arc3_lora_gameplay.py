"""Paired real-game screening of a saved adapter and its unchanged base."""
import asyncio
from datetime import datetime
import json
from pathlib import Path
import pickle
import threading
import time
from urllib.request import Request,urlopen


def append_routing_record(path,records,lock,record):
    """Publish a complete routing snapshot while game workers start together."""
    path=Path(path)
    with lock:
        records.append(record)
        temporary=path.with_suffix('.tmp')
        temporary.write_text(json.dumps(records,indent=2)+'\n')
        temporary.replace(path)


def verify_serving_effect(port,base_model):
    """Require loaded named adapter and an observable probability change."""
    base_url=f'http://127.0.0.1:{port}'
    with urlopen(base_url+'/v1/models',timeout=30) as response:
        models=json.load(response)
    ids=[row['id'] for row in models['data']]
    if base_model not in ids or 'pilot' not in ids:
        raise ValueError('Actual model inventory omits the base or trained adapter: '+str(ids))
    results=[]
    for prompt in [
        'Observe a grid. Compare the outcome of one action with your prediction. The next step is',
        'An action leaves the board unchanged. To learn the hidden rule, first',
        'The apparent goal was contradicted by an experiment. Revise the hypothesis by',
    ]:
        pair={}
        for name,adapter in [('base',None),('adapted','pilot')]:
            payload=dict(text=prompt,sampling_params=dict(temperature=0,max_new_tokens=1,sampling_seed=20261101),
                lora_path=adapter,return_logprob=True,top_logprobs_num=5)
            request=Request(base_url+'/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=180) as response:result=json.load(response)
            values=result['meta_info']['output_token_logprobs']
            if not values:raise ValueError('No actual serving probability evidence')
            pair[name]=dict(text=result.get('text',''),output_token_logprobs=values,
                output_top_logprobs=result['meta_info'].get('output_top_logprobs'))
        a=pair['base']['output_token_logprobs'][0];b=pair['adapted']['output_token_logprobs'][0]
        pair['changed']=a[1]!=b[1] or abs(float(a[0])-float(b[0]))>1e-7
        results.append(pair)
    if not any(row['changed'] for row in results):
        raise ValueError('No observed serving effect from the named trained adapter')
    return dict(model_inventory=ids,probability_probes=results,
        boundary='Short non-game routing/effect checks only. Real held-out gameplay determines adaptation value.')


async def run_paired_gameplay(target,working,bundle,games,base_model,deadline,start_lifecycle):
    """Run both five-game arms together on the same model server and deadline.

    Each arm gets five workers. Both share the same8-slot FCFS server, LoRA
    machinery and draft. This is a resource-sharing screening experiment, not
    an isolated full-capacity performance estimate or hidden competition score.
    """
    from inference.agent.tool_agent import ToolAgent
    working=Path(working);bundle=Path(bundle)
    if len(games)!=5:raise ValueError('Exactly five frozen whole-game holdouts required')
    arms={};route_records={'base':[],'adapted':[]}
    route_locks={name:threading.Lock() for name in route_records}
    for name,model_id in [('base',base_model),('adapted',base_model+':pilot')]:
        # Restore pristine benchmark configuration; no state or notes are shared.
        with (bundle/'benchmark_initial.pkl').open('rb') as stream:benchmark=pickle.load(stream)
        benchmark.games=games;benchmark.job_dir=working/name;benchmark.job_dir.mkdir(exist_ok=True)
        benchmark.n_passes=1;benchmark.game_weights=None;benchmark.periodic_save_interval_s=60
        benchmark.solver.model=model_id
        benchmark.solver.concurrency=5
        benchmark.solver.analyzer_timeout=900
        benchmark.solver.max_actions_per_game=None
        benchmark.solver.max_runtime_s_per_game=deadline-time.time()
        benchmark.solver.save_request_logs=True
        (benchmark.job_dir/'git_status.txt').write_text((bundle/'git_status.txt').read_text())
        def factory(game,index,*,arm=name,expected=model_id):
            agent=ToolAgent(model=expected,timeout=900,save_request_logs=True,dispatch_index=index)
            if agent._model.model_id!=expected:raise ValueError('Agent selected an incorrect serving model')
            append_routing_record(working/arm/'model-routing.json',route_records[arm],route_locks[arm],
                dict(dispatch_index=index,requested_model=expected,
                    resolved_model=agent._model.model_id,base_url=agent._model.base_url))
            return agent
        benchmark.solver.analyzer_factory=factory
        arms[name]=benchmark
    async def run_arm(name,benchmark):
        finish=start_lifecycle(benchmark,working/name/'hydra_lifecycle.json',dict(competition=False,variant='lora-'+name,games=5))
        try:
            await benchmark.run(soft_end_time=datetime.fromtimestamp(deadline),runtime_environment=target,minimal_diagnostics=False)
        except BaseException as error:
            finish(type(error).__name__);raise
        else:finish()
        rows=[dict(game_id=r.game_id,state=r.state,levels_completed=r.levels_completed,total_levels=r.number_of_levels,
            actions=sum(r.actions_per_level),score=r.final_score,
            generated_tokens=sum(a.generated_tokens for a in r.history)+r.final_generated_tokens,note=r.solver_note)
            for r in benchmark.game_runs]
        (working/name/'hydra_model_summary.json').write_text(json.dumps(rows,indent=2)+'\n')
        if len(rows)!=5 or any(r['state'] in ['crashed','not_started'] or r['actions']<=1 or r['generated_tokens']<=0 for r in rows):
            raise RuntimeError('Substantive real model gameplay did not complete in both arms')
        if len(route_records[name])!=5:raise ValueError('Incomplete per-game adapter routing evidence')
        return dict(games=5,score=sum(r['score'] for r in rows)/5,levels=sum(r['levels_completed'] for r in rows),
            full_wins=sum(r['total_levels']>0 and r['levels_completed']==r['total_levels'] for r in rows),
            actions=sum(r['actions'] for r in rows),generated_tokens=sum(r['generated_tokens'] for r in rows))
    results=await asyncio.gather(*(run_arm(name,benchmark) for name,benchmark in arms.items()))
    report=dict(phase='complete',arms=dict(zip(arms,results)),finished_at_epoch=time.time(),
        official_submission_eligible=False,
        boundary='Five public whole-game gradient holdouts, previously studied by the researcher. Paired shared-server screening with one stochastic draw; no hidden-score estimate or automatic promotion.')
    report['adapted_minus_base_score']=report['arms']['adapted']['score']-report['arms']['base']['score']
    (working/'paired-gameplay-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    return report
