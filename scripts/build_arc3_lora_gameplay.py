"""Freeze paired five-game evaluation only after a real saved training result."""
import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TRAIN='kunalsinghh25/arc-hydra-qwen27-lora-pilot/1'
KERNEL='kunalsinghh25/arc-hydra-qwen27-lora-gameplay'
HELD_OUT=sorted(['cn04-2fe56bfb','s5i5-18d95033','ar25-0c556536','ls20-9607627b','ka59-38d34dbb'])


def build():
    mount=ROOT/'reports/kaggle/adapter-mount-cpu-probe-v1'
    mount_verified=json.loads((mount/'verified.json').read_text())
    mount_report=mount/'adapter-mount-probe.json'
    if mount_verified['status']!='COMPLETE' or sha256(mount_report.read_bytes()).hexdigest()!=mount_verified['report_sha256']:
        raise ValueError('Completed exact saved-adapter mount CPU gate required')
    mount_actual=json.loads(mount_report.read_text())
    if not mount_actual['passed'] or mount_actual['actual_tensor_count']!=992 or mount_actual['recurrent_groups_checked']!=48:
        raise ValueError('Actual saved adapter mount/header gate failed')
    output=ROOT/'reports/kaggle/qwen27-lora-pilot-v1'
    report_path=output/'sft-pilot/training-report.json'
    report=json.loads(report_path.read_text())
    state=json.loads((ROOT/'reports/arc3/qwen27-lora-pilot/state.json').read_text())
    if (state['phase']!='pilot_complete' or state['exact_kernel']!=TRAIN
            or report['phase']!='complete' or report['optimizer_steps']<1
            or report['adapter_output_squared_norm']<=0 or report['reload_loss_absolute_error']>1e-3
            or not report['export_preflight']['passed'] or len(report['serving_export']['qkv_delta_checks'])!=48):
        raise ValueError('Actual CUDA training, serialization/reload and export gates required')
    if mount_actual['training_report_sha256']!=sha256(report_path.read_bytes()).hexdigest():
        raise ValueError('Mounted training result differs from the completed actual GPU pilot')
    for name,record in report['serving_export']['files'].items():
        if sha256((output/'sft-pilot/serving-adapter'/name).read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Downloaded actual saved serving adapter changed')
    split_path=ROOT/'reports/arc3/qwen27-training-pilot/split.json'
    split=json.loads(split_path.read_text())
    games=sorted(name for name,part in split['games'].items() if part=='test')
    if games!=HELD_OUT:raise ValueError('Frozen whole-game gradient holdout changed')
    inputs=json.loads((ROOT/'reports/arc3/qwen27-training-pilot/input-package.json').read_text())
    if sha256(split_path.read_bytes()).hexdigest()!=inputs['manifest']['files']['split.json']['sha256']:
        raise ValueError('CPU-gated original whole-game split changed')
    package=ROOT/'notebooks/qwen27_fair_capacity'
    manifest=json.loads((package/'manifest.json').read_text())
    if any(sha256((package/name).read_bytes()).hexdigest()!=digest for name,digest in manifest['files'].items()):
        raise ValueError('Accepted capacity package changed')
    notebook=deepcopy(json.loads((package/'submission.ipynb').read_text()))
    metadata=json.loads((package/'kernel-metadata.json').read_text())
    provenance=json.loads((package/'provenance.json').read_text())
    training_provenance=json.loads((output/'hydra_training_provenance.json').read_text())
    if training_provenance['official_submission_eligible'] is not False:raise ValueError('Training source scope changed')
    runtime=(ROOT/'hydra/arc3_lora_gameplay.py').read_text();compile(runtime,'paired-gameplay','exec')
    provenance.update(candidate='qwen27-lora-paired-gameplay',experiment_variant='qwen27-lora',
        training_kernel=TRAIN,training_report_sha256=sha256(report_path.read_bytes()).hexdigest(),
        adapter_mount_gate=mount_verified['kernel'],adapter_mount_report_sha256=mount_verified['report_sha256'],
        training_provenance=training_provenance,serving_export_files=report['serving_export']['files'],
        gradient_holdout_games=games,split_sha256=sha256(split_path.read_bytes()).hexdigest(),
        gameplay_source_sha256=sha256(runtime.encode()).hexdigest(),official_submission_eligible=False,
        comparison_boundary='Paired simultaneous base/adapter arms with five gradient-held-out public games each. Same8-slot FCFS server, DFlash and enabled LoRA runtime. One stochastic draw, shared resource contention, researcher previously studied all public games. No hidden-score estimate or automatic promotion.')
    intake=f'''\n# Only the exact completed training output may provide adapter weights.
from hashlib import sha256 as _adapter_hash
_training_roots=[Path('/kaggle/input/notebooks/kunalsinghh25/arc-hydra-qwen27-lora-pilot/1'),
    Path('/kaggle/input/notebooks/kunalsinghh25/arc-hydra-qwen27-lora-pilot'),
    Path('/kaggle/input/arc-hydra-qwen27-lora-pilot')]
_adapter_hits=set()
for _root in _training_roots:
    if _root.is_dir():_adapter_hits.update(p.parent.resolve() for p in _root.rglob('serving-adapter/adapter_config.json'))
if len(_adapter_hits)!=1:raise ValueError('Exact serving adapter is not uniquely mounted')
LORA_ADAPTER_DIR=str(next(iter(_adapter_hits)))
for _name,_record in {report['serving_export']['files']!r}.items():
    if _adapter_hash(Path(LORA_ADAPTER_DIR,_name).read_bytes()).hexdigest()!=_record['sha256']:
        raise ValueError('Actual saved serving adapter changed: '+_name)
_mounted_report=Path(LORA_ADAPTER_DIR).parent/'training-report.json'
if _adapter_hash(_mounted_report.read_bytes()).hexdigest()!={sha256(report_path.read_bytes()).hexdigest()!r}:
    raise ValueError('Actual training provenance report changed')
(WORKING_DIR/'hydra_lora_gameplay_provenance.json').write_text(json.dumps({provenance!r},indent=2))
'''
    notebook['cells'][6]['source']+=intake
    launcher=notebook['cells'][14]['source'];marker='# ---- launch detached and wait for health ----'
    assert launcher.count(marker)==1
    launcher=launcher.replace(marker,"args+=['--enable-lora','--lora-paths','pilot='+LORA_ADAPTER_DIR,'--max-loras-per-batch','2','--max-lora-rank','16']\n\n"+marker)
    compile(launcher,'paired-adapter-server','exec');notebook['cells'][14]['source']=launcher
    run=notebook['cells'][22]['source']
    # Keep executed readiness, lifecycle definitions and offline environment
    # resolver. Replace the all25 benchmark invocation with the paired test.
    end=run.index('# Outside a real submission, stop')
    run=run[:end]
    run+=f'''\nif TRUE_SUBMISSION:raise RuntimeError('Development paired evaluation only')
_held_out={games!r}
bm.games=[game for game in bm.games if str(game.env_name) in _held_out]
if len(bm.games)!=5:raise ValueError('Five frozen held-out environments were not found')
_lora_ns={{}};exec({runtime!r},_lora_ns)
_serving_check=_lora_ns['verify_serving_effect'](SERVED_MODEL_PORT,SERVED_MODEL_NAME)
(WORKING_DIR/'serving-effect.json').write_text(json.dumps(_serving_check,indent=2))
_deadline=NOTEBOOK_START_TIME+7200-600
if _deadline-time.time()<1800:raise RuntimeError('Insufficient real gameplay time after setup')
await _lora_ns['run_paired_gameplay'](target,WORKING_DIR,BUNDLE_DIR,bm.games,SERVED_MODEL_NAME,_deadline,start_lifecycle)
import pandas as pd
pd.DataFrame([['1_0','1',True,1]],columns=['row_id','game_id','end_of_game','score']).to_parquet(WORKING_DIR/'submission.parquet',index=False)
'''
    # Notebook code includes top-level await; compile with the notebook flag.
    compile(run,'paired-adapter-gameplay','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    notebook['cells'][22]['source']=run
    notebook['cells'][0]['source']='# Saved ARC3 adapter versus unchanged base\n\nActual named saved adapter, shared8-slot FCFS runtime, five whole-game gradient holdouts per arm. Strict7200-second total development cap. Public screening only. No official submission. Original upstream attribution/licenses retained.'
    metadata.update(id=KERNEL,title='ARC Hydra Qwen27 Lora Gameplay',kernel_sources=[TRAIN])
    destination=ROOT/'notebooks/qwen27_lora_gameplay';destination.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (destination/name).write_text(json.dumps(value,indent=2)+'\n')
    result=dict(kernel=KERNEL,wall_seconds=7200,files={name:sha256((destination/name).read_bytes()).hexdigest()
        for name in ['submission.ipynb','kernel-metadata.json','provenance.json']})
    (destination/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':build()
