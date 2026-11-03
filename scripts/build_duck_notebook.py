"""Package the attributed public Franzen M2 baseline for offline Kaggle runs.

Defaults reproduce the agent. Optional runtime, deadline and memory experiments
are declared separately in provenance and use distinct notebook IDs.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'baselines/duck_m2/upstream.ipynb'
SOURCE_META = SOURCE.with_name('upstream-metadata.json')
PREFIXES = ('ft09', 'ls20', 'r11l', 'vc33', 'bp35')


def build(mode='preflight', contest_reserve_seconds=None, runtime_overlay_dataset=None, runtime_overlay_sha256=None, agent_variant='baseline', model_variant='intel', runtime_overlay_kernel=None, public_runtime_seconds=None, notebook_budget_seconds=None):
    if runtime_overlay_dataset and runtime_overlay_kernel:
        raise ValueError('Select one runtime overlay source')
    runtime_overlay_source=runtime_overlay_dataset or runtime_overlay_kernel
    if mode not in ('preflight', 'benchmark'):
        raise ValueError(mode)
    if agent_variant not in ('baseline','rolling-summary','step-verification','verified-planning','planning-assist'):
        raise ValueError(agent_variant)
    planning=agent_variant in ('verified-planning','planning-assist')
    if planning and contest_reserve_seconds is None:
        contest_reserve_seconds=600
    if notebook_budget_seconds is not None:
        if type(notebook_budget_seconds) is not int or not 1800<=notebook_budget_seconds<=32400:
            raise ValueError('Notebook wall budget must be 1800..32400 seconds')
        if contest_reserve_seconds is None:contest_reserve_seconds=600
        if contest_reserve_seconds>=notebook_budget_seconds:
            raise ValueError('Finalization reserve must be smaller than notebook budget')
    if public_runtime_seconds is not None and (type(public_runtime_seconds) is not int or not 60<=public_runtime_seconds<=31800):
        raise ValueError('Public gameplay limit must be 60..31800 seconds')
    if model_variant not in ('intel','swift-1.5'):
        raise ValueError(model_variant)
    if model_variant!='intel' and (agent_variant!='baseline' or runtime_overlay_source is not None):
        raise ValueError('Evaluate the model change separately from memory/runtime first')
    if agent_variant!='baseline' and runtime_overlay_source is not None:
        raise ValueError('Evaluate memory and runtime changes separately first')
    if contest_reserve_seconds is not None and not 120 <= contest_reserve_seconds < 32400:
        raise ValueError('Contest finalization reserve must be between 120 and 32399 seconds')
    if runtime_overlay_source is not None:
        if runtime_overlay_dataset and not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+',runtime_overlay_dataset):
            raise ValueError('Runtime overlay needs an owner/dataset reference')
        if runtime_overlay_kernel and not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[1-9][0-9]*',runtime_overlay_kernel):
            raise ValueError('Runtime overlay needs an exact owner/kernel/version reference')
        if runtime_overlay_sha256 is None or not re.fullmatch(r'[a-f0-9]{64}',runtime_overlay_sha256):
            raise ValueError('Runtime overlay requires the actual manifest SHA-256')
    elif runtime_overlay_sha256 is not None:
        raise ValueError('Manifest SHA requires a runtime overlay source')
    upstream = json.loads(SOURCE.read_text(encoding='utf-8'))
    notebook = deepcopy(upstream)
    code_digests = []
    for cell in notebook['cells']:
        cell['source'] = ''.join(cell['source'])
        if cell['cell_type'] == 'code':
            code_digests.append(sha256(cell['source'].encode()).hexdigest())
            cell['outputs'] = []
            cell['execution_count'] = None
    provenance = dict(
        source='https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution',
        source_sha256=sha256(SOURCE.read_bytes()).hexdigest(),
        source_code_sha256=code_digests,
        author_repository='https://github.com/da-fr/arc-agi-3-solution',
        inspected_repository_commit='10882e332d883af3e61616df8c8a17d03a328a75',
        authors=['Daniel Franzen', 'Jeroen Cottaar', 'Tufa Labs'],
        license='Apache-2.0; third-party model/runtime licenses also apply',
        mode=mode, public_games=list(PREFIXES) if mode=='preflight' else 'all 25',
        public_runtime_seconds=public_runtime_seconds if public_runtime_seconds is not None else (900 if mode=='preflight' else 7200),
        public_startup_allowance_seconds=3600,
        competition_changes='None to model, prompts, tools, serving or scheduling',
    )
    if contest_reserve_seconds is not None:
        provenance['competition_finalization_reserve_seconds'] = contest_reserve_seconds
        provenance['competition_changes'] = 'Global notebook deadline with finalization reserve; agent/model/prompts/tools/serving/scheduling settings unchanged'
    if notebook_budget_seconds is not None:
        provenance['notebook_wall_budget_seconds']=notebook_budget_seconds
        provenance['public_deadline_includes_startup']=True
    if model_variant=='swift-1.5':
        manifest=json.loads((ROOT/'baselines/swift_15/model.json').read_text())
        helper=(ROOT/'scripts/swift_model_view.py').read_text()
        configuration=next(c for c in notebook['cells'] if '\nos.environ.update({k: str(v) for k,v in setup_env.items()})' in c['source'])
        configuration['source']+='\n# ARC-Hydra Swift split-checkpoint view.\n'
        configuration['source']+=f'hydra_swift_manifest = {manifest!r}\n'
        configuration['source']+=f'hydra_swift_module = {{}}\nexec({helper!r}, hydra_swift_module)\n'
        configuration['source']+='''hydra_swift_parts = {}
for hydra_part in ('a','b'):
    hydra_suffix = f'phuongncn/arc3-qwen38-swift-w4a16-autoround/pytorch/w4a16-{hydra_part}/1'
    hydra_candidates = [Path('/kaggle/input/models') / hydra_suffix, Path('/kaggle/input') / hydra_suffix]
    hydra_swift_parts[hydra_part] = next((p for p in hydra_candidates if p.is_dir()), None)
    if hydra_swift_parts[hydra_part] is None:
        raise RuntimeError(f'Swift checkpoint part {hydra_part} is not mounted')
MODEL_DIR = hydra_swift_module['prepare'](hydra_swift_parts, '/tmp/hydra-swift-model', hydra_swift_manifest)
'''
        provenance.update(model_variant=model_variant,model_manifest=manifest)
        provenance['competition_changes']='Swift 1.5 AutoRound target; original runtime, draft, agent, prompts, tools and scheduler retained'
        if contest_reserve_seconds is not None:
            provenance['competition_changes']+=f'; {contest_reserve_seconds}-second finalization reserve'
    if agent_variant=='rolling-summary':
        overrides=dict(ARC3_SUMMARY_INTERVAL_TOKENS=48*1024,ARC3_SUMMARY_MAX_GEN=4096,
                       ARC3_SUMMARY_TURN_CONTEXT='1',ARC3_DRAIN_STOP_AT_SUMMARIES='1')
        configuration=next(c for c in notebook['cells'] if '\nos.environ.update({k: str(v) for k,v in setup_env.items()})' in c['source'])
        anchor='os.environ.update({k: str(v) for k,v in setup_env.items()})'
        assert configuration['source'].count(anchor)==1
        configuration['source']=configuration['source'].replace(anchor,
            '# ARC-Hydra rolling-summary experiment.\nsetup_env.update('+repr(overrides)+')\n'+anchor)
        provenance.update(agent_variant=agent_variant,agent_environment_overrides=overrides)
        provenance['competition_changes']='Periodic summaries and summary-aware context draining; original model, serving, tools and scheduler retained'
        if contest_reserve_seconds is not None:
            provenance['competition_changes']+=f'; {contest_reserve_seconds}-second finalization reserve'
    if agent_variant=='step-verification':
        overrides=dict(ARC3_STEP_VERIFICATION_HINT='1')
        configuration=next(c for c in notebook['cells'] if '\nos.environ.update({k: str(v) for k,v in setup_env.items()})' in c['source'])
        anchor='os.environ.update({k: str(v) for k,v in setup_env.items()})'
        assert configuration['source'].count(anchor)==1
        configuration['source']=configuration['source'].replace(anchor,
            '# ARC-Hydra step-verification experiment.\nsetup_env.update('+repr(overrides)+')\n'+anchor)
        provenance.update(agent_variant=agent_variant,agent_environment_overrides=overrides)
        provenance['competition_changes']='Existing step-verification prompt guidance enabled; original model, runtime, tools, memory and scheduler retained'
        if contest_reserve_seconds is not None:
            provenance['competition_changes']+=f'; {contest_reserve_seconds}-second finalization reserve'
    if planning:
        library=(ROOT/'hydra/verified_planning.py').read_text(encoding='utf-8')
        installer=(ROOT/'scripts/install_verified_agent.py').read_text(encoding='utf-8')
        setup=next(c for c in notebook['cells'] if c['source'].startswith('# Each bundled repo exposes'))
        setup['source']+='\n# ARC-Hydra: install into the writable notebook-local source copy before pickle imports.\n'
        setup['source']+=f'_hydra_extension_ns = {{}}\nexec({installer!r}, _hydra_extension_ns)\n'
        setup['source']+=f'_hydra_extension_report = _hydra_extension_ns["install"](BUNDLE_DIR, {library!r}, enforce_probes={agent_variant=="verified-planning"!r})\n'
        setup['source']+='(WORKING_DIR / "hydra_extension.json").write_text(json.dumps(_hydra_extension_report, indent=2))\n'
        provenance.update(agent_variant=agent_variant,verified_planning_sha256=sha256(library.encode()).hexdigest(),
                          extension_installer_sha256=sha256(installer.encode()).hexdigest())
        provenance['public_competition_diagnostics']=(mode=='preflight')
        provenance['competition_changes']='Mechanically checked replay/planned actions, one exploratory action per tool call; shared model readiness, lifecycle counters and global finalization reserve. Original model/runtime/scheduler retained.'
        if agent_variant=='planning-assist':
            provenance['competition_changes']='Optional mechanically checked planning; original ordinary action batching and host guards retained. Shared readiness, lifecycle counters and global finalization reserve. Original model/runtime/scheduler retained.'
    if runtime_overlay_source is not None:
        provenance.update(runtime_overlay_dataset=runtime_overlay_dataset,
                          runtime_overlay_kernel=runtime_overlay_kernel,
                          runtime_overlay_manifest_sha256=runtime_overlay_sha256,
                          runtime_source_commit='560edbdca18aedae13f71ae20b3984efa4d22633')
        provenance['competition_changes'] = 'v3 serving overlay; original checkpoints, prompts, tools and agent settings retained'
        if contest_reserve_seconds is not None:
            provenance['competition_changes'] += f'; {contest_reserve_seconds}-second notebook finalization reserve'
        serving=next(c for c in notebook['cells'] if c['source'].startswith('# Paste this entire file into the launcher cell.'))
        anchor='# Report the optional later caching patch. This cell does not modify wheel code.'
        assert serving['source'].count(anchor)==1
        installer=(ROOT/'scripts/serving_v3/install_overlay.py').read_text(encoding='utf-8')
        hook='\n# ARC-Hydra: verified, offline serving overlay in a separate candidate.\n'
        if runtime_overlay_kernel:
            owner,slug,version=runtime_overlay_kernel.split('/')
            hook+=f'hydra_overlay_options = [Path("/kaggle/input/notebooks/{owner}/{slug}/pennyroyal-v3-overlay"), Path("/kaggle/input/{slug}/pennyroyal-v3-overlay")]\n'
        else:
            hook+=f'HYDRA_OVERLAY_DATASET = {runtime_overlay_dataset!r}\n'
            hook+='hydra_overlay_options = [Path("/kaggle/input/datasets") / HYDRA_OVERLAY_DATASET, Path("/kaggle/input") / HYDRA_OVERLAY_DATASET.split("/")[1]]\n'
        hook+='hydra_overlay = next((p for p in hydra_overlay_options if (p / "manifest.json").is_file()), None)\n'
        hook+='if hydra_overlay is None:\n    raise RuntimeError("Runtime overlay source not mounted")\n'
        hook+=f'if sha256(hydra_overlay / "manifest.json") != {runtime_overlay_sha256!r}:\n    raise RuntimeError("Runtime overlay manifest differs from tested build")\n'
        hook+='hydra_installer = Path(PREFIX) / "install_v3_overlay.py"\n'
        hook+=f'hydra_installer.write_text({installer!r})\n'
        hook+='hydra_runtime_env = Path(PREFIX) / "v3_environment.json"\n'
        hook+='run([sys.executable, hydra_installer, "--overlay", hydra_overlay, "--base", WHEELHOUSE_DIR, "--venv", VENV, "--uv", Path(PREFIX) / "bin/uv", "--environment-output", hydra_runtime_env, "--port", SERVED_MODEL_PORT], env=env)\n'
        hook+='env.update(json.loads(hydra_runtime_env.read_text()))\n'
        hook+='CUDA_HOME, CC, CXX = env["CUDA_HOME"], env["CC"], env["CXX"]\n'
        hook+='run([env["CUDACXX"], "--version"], env=env)\n'
        hook+='print("Overlay host compiler:", env["CXX"])\n\n'
        serving['source']=serving['source'].replace(anchor,hook+anchor)
    controls = next(c for c in notebook['cells'] if c['source'].startswith('# Make one-off changes'))
    controls['source'] += '\n\n# ARC-Hydra: bound public evaluation only; retain contest settings.\n'
    controls['source'] += 'if not TRUE_SUBMISSION:\n    bm.n_passes = 1\n'
    controls['source'] += f'    bm.solver.max_runtime_s_per_game = {provenance["public_runtime_seconds"]}\n'
    controls['source'] += '    bm.solver.save_request_logs = True\n    bm.periodic_save_interval_s = 120\n'
    if planning:
        controls['source']+='\n# Lightweight progress is also retained during competition reruns.\nbm.periodic_save_interval_s = 120\n'
    run = next(c for c in notebook['cells'] if c['source'].startswith("print('Starting benchmark...')"))
    needle = 'await bm.run(soft_end_time=soft_end, runtime_environment=target, minimal_diagnostics=TRUE_SUBMISSION)'
    assert run['source'].count(needle) == 1
    evaluation = '\n# ARC-Hydra public reproduction; no hidden game selection.\nif not TRUE_SUBMISSION:\n'
    wait_source = (ROOT/'scripts/wait_local_backend.py').read_text(encoding='utf-8')
    if not planning:
        evaluation += f'    exec({wait_source!r})\n'
        evaluation += '    wait_local_backend(f"http://127.0.0.1:{SERVED_MODEL_PORT}/health", NOTEBOOK_START_TIME + 3600, proc)\n'
    if mode == 'preflight':
        evaluation += f'    hydra_prefixes = {PREFIXES!r}\n'
        evaluation += '    bm.games = [g for g in bm.games if g.env_name.split("-")[0] in hydra_prefixes]\n'
        evaluation += '    if len(bm.games) != len(hydra_prefixes):\n        raise RuntimeError("Public preflight games missing")\n'
    evaluation += '    bm.solver.concurrency = len(bm.games)\n'
    if notebook_budget_seconds is None:
        evaluation += f'    soft_end = datetime.now() + timedelta(seconds={provenance["public_runtime_seconds"]})\n'
    else:
        evaluation += f'    hydra_public_remaining = NOTEBOOK_START_TIME + {notebook_budget_seconds} - {contest_reserve_seconds} - time.time()\n'
        evaluation += '    if hydra_public_remaining <= 0:\n        raise RuntimeError("Startup consumed the notebook gameplay budget")\n'
        evaluation += f'    bm.solver.max_runtime_s_per_game = min({provenance["public_runtime_seconds"]}, hydra_public_remaining)\n'
        evaluation += f'    soft_end = min(datetime.now() + timedelta(seconds={provenance["public_runtime_seconds"]}), datetime.fromtimestamp(NOTEBOOK_START_TIME + {notebook_budget_seconds} - {contest_reserve_seconds}))\n'
    evaluation += '    print("Hydra effective public run:", dict(games=len(bm.games), passes=bm.n_passes, concurrency=bm.solver.concurrency, gameplay_seconds=bm.solver.max_runtime_s_per_game, deadline=soft_end.isoformat()))\n'
    evaluation += f'    Path(WORKING_DIR / "hydra_provenance.json").write_text(json.dumps({provenance!r}, indent=2))\n'
    if contest_reserve_seconds is not None:
        evaluation += '\n# ARC-Hydra bounded competition finalization.\nif TRUE_SUBMISSION:\n'
        evaluation += '    hydra_notebook_budget = float(target.max_runtime_s)\n'
        if notebook_budget_seconds is not None:
            evaluation += f'    hydra_notebook_budget = min(hydra_notebook_budget, {notebook_budget_seconds})\n'
        evaluation += f'    if not {contest_reserve_seconds} < hydra_notebook_budget:\n        raise RuntimeError("Notebook budget is smaller than finalization reserve")\n'
        evaluation += f'    soft_end = datetime.fromtimestamp(NOTEBOOK_START_TIME + hydra_notebook_budget - {contest_reserve_seconds})\n'
        evaluation += '    print("Competition soft deadline:", soft_end.isoformat(), "including notebook startup")\n'
    run['source'] = run['source'].replace(needle, evaluation+'\n'+needle)
    if planning:
        lifecycle=(ROOT/'scripts/agent_lifecycle.py').read_text(encoding='utf-8')
        prelude='\n# ARC-Hydra shared readiness and durable lifecycle evidence.\n'
        prelude+=f'exec({lifecycle!r})\nexec({wait_source!r})\n'
        prelude+='''_hydra_lifecycle_path = WORKING_DIR / "hydra_lifecycle.json"
_hydra_context = dict(competition=bool(TRUE_SUBMISSION), variant='verified-planning')
write_lifecycle(_hydra_lifecycle_path, 'starting', _hydra_context)
try:
    wait_local_backend(f"http://127.0.0.1:{SERVED_MODEL_PORT}/health", NOTEBOOK_START_TIME + 3600, proc)
except BaseException as _hydra_start_error:
    write_lifecycle(_hydra_lifecycle_path, 'startup_failed', _hydra_context, error=type(_hydra_start_error).__name__)
    raise
write_lifecycle(_hydra_lifecycle_path, 'model_ready', _hydra_context)
'''
        prelude=prelude.replace("variant='verified-planning'",f'variant={agent_variant!r}')
        run['source']=run['source'].replace("print('Starting benchmark...')","print('Starting benchmark...')"+prelude,1)
        executed_await=needle
        if mode=='preflight':
            # Exercise competition-style minimal diagnostics on public games.
            executed_await=needle.replace('minimal_diagnostics=TRUE_SUBMISSION','minimal_diagnostics=True')
        wrapped='''_hydra_context['games'] = len(bm.games)
_hydra_finish = start_lifecycle(bm, _hydra_lifecycle_path, _hydra_context)
try:
    '''+executed_await+'''
except BaseException as _hydra_run_error:
    _hydra_finish(type(_hydra_run_error).__name__)
    raise
else:
    _hydra_finish()
'''
        run['source']=run['source'].replace(needle,wrapped)
        if mode=='preflight':
            run['source']+='\nif not TRUE_SUBMISSION:\n    (WORKING_DIR / "benchmark.json").write_text(json.dumps(bm.to_json_dict(), indent=2))\n'
    # Benchmark.run deliberately swallows some solver errors. A completed
    # notebook therefore needs an explicit gameplay/exception check.
    run['source'] += '''

if not TRUE_SUBMISSION:
    hydra_summary = [dict(game_id=r.game_id, state=r.state,
                          levels_completed=r.levels_completed,
                          total_levels=r.number_of_levels,
                          actions=sum(r.actions_per_level),
                          score=r.final_score,
                          generated_tokens=sum(a.generated_tokens for a in r.history)+r.final_generated_tokens,
                          note=r.solver_note) for r in bm.game_runs]
    (WORKING_DIR / 'hydra_model_summary.json').write_text(json.dumps(hydra_summary, indent=2))
    print(json.dumps(hydra_summary, indent=2))
    if not hydra_summary or any(r['state'] in ('crashed', 'not_started') or r['actions'] <= 0 for r in hydra_summary):
        raise RuntimeError('Model gameplay preflight failed; inspect benchmark.json and serve.log')
'''
    configuration_note=('Published serving configuration retained. ' if runtime_overlay_source is None else
                        'Experimental v3 serving overlay; GPU correctness and performance unverified. ')
    configuration_note+=('Original competition time controls retained.' if contest_reserve_seconds is None else
                         f'Contest deadline includes startup and reserves {contest_reserve_seconds} seconds for finalization.')
    if agent_variant=='rolling-summary':
        configuration_note+=' Experimental periodic summaries with summary-aware history draining; benefit unproven.'
    if agent_variant=='step-verification':
        configuration_note+=' Experimental existing step-verification prompt guidance; benefit unproven.'
    if agent_variant=='verified-planning':
        configuration_note+=' Experimental replay verification and prediction-checked action batches; score benefit unproven.'
    if model_variant=='swift-1.5':
        configuration_note+=' Swift 1.5 target-model experiment; model/gameplay compatibility and benefit unverified.'
    notebook['cells'].insert(0, dict(cell_type='markdown', metadata={}, source=(
        '# ARC-Hydra: attributed Duck M2 reproduction\n\n'
        'Original agent and serving code: **Daniel Franzen**, building on '
        '**Jeroen Cottaar and Tufa Labs**. Apache-2.0; model/runtime terms apply.\n\n'
        'This private notebook measures the attributed agent or a declared runtime experiment. '
        f'Public mode: {mode}. {configuration_note} '
        'No score reproduction or score above 71 is claimed.\n\n'
        '[Original notebook](https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution) · '
        '[Author source](https://github.com/da-fr/arc-agi-3-solution)\n')))
    metadata = json.loads(SOURCE_META.read_text())
    for key in ('id_no', 'keywords'):
        metadata.pop(key, None)
    metadata.update(id='kunalsinghh25/arc-hydra-duck-m2-baseline',
                    title='ARC Hydra Duck M2 Baseline', code_file='submission.ipynb',
                    is_private=True, enable_internet=False, machine_shape='NvidiaRtxPro6000')
    if runtime_overlay_source is not None:
        if runtime_overlay_kernel:
            metadata.setdefault('kernel_sources',[]).append(runtime_overlay_kernel)
        else:
            metadata['dataset_sources'].append(runtime_overlay_dataset)
        metadata['id']='kunalsinghh25/arc-hydra-duck-v3-runtime'
        metadata['title']='ARC Hydra Duck V3 Runtime'
    if agent_variant=='rolling-summary':
        metadata.update(id='kunalsinghh25/arc-hydra-duck-summary',title='ARC Hydra Duck Summary')
    if agent_variant=='step-verification':
        metadata.update(id='kunalsinghh25/arc-hydra-duck-verification',title='ARC Hydra Duck Verification')
    if agent_variant=='verified-planning':
        metadata.update(id='kunalsinghh25/arc-hydra-verified-planner',title='ARC Hydra Verified Planner')
    if agent_variant=='planning-assist':
        metadata.update(id='kunalsinghh25/arc-hydra-planning-assist',title='ARC Hydra Planning Assist')
    if model_variant=='swift-1.5':
        metadata.update(id='kunalsinghh25/arc-hydra-duck-swift',title='ARC Hydra Duck Swift')
        metadata['model_sources']=[m for m in metadata['model_sources'] if 'intel-qwen' not in m]+manifest['model_sources']
    return notebook, metadata, provenance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('preflight','benchmark'), default='preflight')
    parser.add_argument('--output')
    parser.add_argument('--contest-reserve-seconds',type=int)
    parser.add_argument('--runtime-overlay-dataset')
    parser.add_argument('--runtime-overlay-kernel')
    parser.add_argument('--runtime-overlay-sha256')
    parser.add_argument('--agent-variant',choices=('baseline','rolling-summary','step-verification','verified-planning','planning-assist'),default='baseline')
    parser.add_argument('--model-variant',choices=('intel','swift-1.5'),default='intel')
    parser.add_argument('--public-runtime-seconds',type=int)
    parser.add_argument('--notebook-budget-seconds',type=int)
    args = parser.parse_args()
    notebook, metadata, provenance = build(args.mode,args.contest_reserve_seconds,args.runtime_overlay_dataset,args.runtime_overlay_sha256,args.agent_variant,args.model_variant,args.runtime_overlay_kernel,args.public_runtime_seconds,args.notebook_budget_seconds)
    output=args.output or ('notebooks/duck_swift' if args.model_variant=='swift-1.5' else
                          'notebooks/duck_summary' if args.agent_variant=='rolling-summary' else
                          'notebooks/duck_verification' if args.agent_variant=='step-verification' else
                          'notebooks/verified_planner' if args.agent_variant=='verified-planning' else
                          'notebooks/planning_assist' if args.agent_variant=='planning-assist' else
                          'notebooks/duck_v3_runtime' if (args.runtime_overlay_dataset or args.runtime_overlay_kernel) else 'notebooks/duck_m2')
    destination = (ROOT/output).resolve()
    if not destination.is_relative_to(ROOT):
        raise ValueError('Notebook output must stay inside the workspace')
    destination.mkdir(parents=True,exist_ok=True)
    for name, value in (('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)):
        (destination/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(provenance,indent=2))


if __name__ == '__main__':
    main()
