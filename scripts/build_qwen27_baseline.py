"""Build one capped offline 27B gameplay baseline, gated by actual CPU mounts."""
from copy import deepcopy
from hashlib import sha256
import ast
import json
from pathlib import Path

from scripts.build_qwen27_probe import TARGET,DRAFT

ROOT=Path(__file__).resolve().parents[1]

ARGS=r'''
# ---- validate the actual CPU-inspected FP8 target and DFlash2 draft ----
target_cfg=json.loads(Path(MODEL_DIR,'config.json').read_text())
assert target_cfg['architectures']==['Qwen3_5ForConditionalGeneration']
assert target_cfg['quantization_config']['quant_method']=='fp8'
_,target_shards=indexed_shards(MODEL_DIR)
assert Path(DRAFT_MODEL_DIR,'model.safetensors').is_file()
graph_bs=[1,2,4]
args=[SGLANG,'serve','--model-path',MODEL_DIR,'--load-format','safetensors',
    '--model-loader-extra-config','{"enable_multithread_load":false}',
    '--served-model-name',SERVED_MODEL_NAME,'--host','127.0.0.1',
    '--port',str(SERVED_MODEL_PORT),'--tensor-parallel-size','1',
    '--dtype','bfloat16','--kv-cache-dtype','fp8_e4m3',
    '--mem-fraction-static','0.92','--context-length',str(CFG['CTX']),
    '--page-size','64','--max-running-requests','4',
    '--chunked-prefill-size','2048','--max-prefill-tokens','2048',
    '--cuda-graph-max-bs-decode','4','--cuda-graph-bs-decode',*map(str,graph_bs),
    '--mamba-ssm-dtype','float32','--max-mamba-cache-size','24',
    '--mamba-radix-cache-strategy','extra_buffer_lazy','--mamba-max-states-per-path','5',
    '--mamba-track-interval','256','--mamba-backend','triton',
    '--linear-attn-decode-backend','triton','--linear-attn-prefill-backend','triton',
    '--attention-backend','flashinfer','--decode-attention-backend','trtllm_mha',
    '--mm-feature-transport','cpu','--image-processor-backend','pil',
    '--reasoning-parser','qwen3','--tool-call-parser','qwen3_coder',
    '--default-chat-template-kwargs','{"preserve_thinking":true}',
    '--watchdog-timeout','1800','--schedule-policy','lpm','--warmups','structured_output',
    '--enable-cache-report','--enable-metrics','--enable-request-time-stats-logging',
    '--speculative-algorithm','DFLASH','--speculative-draft-model-path',DRAFT_MODEL_DIR,
    '--speculative-draft-load-format','safetensors',
    '--speculative-draft-model-quantization','unquant',
    '--speculative-num-draft-tokens','8','--speculative-draft-window-size','2048',
    '--speculative-attention-mode','decode',
    '--speculative-draft-attention-backend','flashinfer',
    '--speculative-draft-kv-cache-dtype','fp8_e4m3']
if CFG['PREFETCH_CHECKPOINTS']:args+=['--weight-loader-prefetch-checkpoints']
if CFG['DROP_CACHE_AFTER_LOAD']:args+=['--weight-loader-drop-cache-after-load']
tmpl=Path(MODEL_DIR,'chat_template.jinja')
assert tmpl.is_file(),'Exact target chat template missing'
args+=['--chat-template',str(tmpl)]
'''


def build():
    gate=ROOT/'reports/kaggle/qwen27-cpu-preflight-v2'
    verified=json.loads((gate/'verified.json').read_text())
    report_path=gate/'qwen27-preflight.json'
    if verified['status']!='COMPLETE' or sha256(report_path.read_bytes()).hexdigest()!=verified['report_sha256']:
        raise ValueError('Completed exact CPU gate required')
    report=json.loads(report_path.read_text())
    if not report['passed'] or not all(report['runtime_flags'].values()):raise ValueError('CPU gate failed')
    cpu=ROOT/'notebooks/qwen27_cpu_preflight_v2'
    if any(sha256((cpu/n).read_bytes()).hexdigest()!=h for n,h in verified['files'].items()):
        raise ValueError('Executed CPU probe changed')
    plan=json.loads((ROOT/'reports/arc3/prediction-ablation/plan.json').read_text())
    control=plan['variants'][0];package=ROOT/control['package']
    if any(sha256((package/n).read_bytes()).hexdigest()!=h for n,h in control['files'].items()):
        raise ValueError('Frozen control changed')
    notebook=deepcopy(json.loads((package/'submission.ipynb').read_text()))
    metadata=json.loads((package/'kernel-metadata.json').read_text())
    provenance=json.loads((package/'provenance.json').read_text())
    cell=notebook['cells'][6]
    old="MODEL_DIR         = '/kaggle/input/models/dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/transformers/default/1'"
    old_draft="DRAFT_MODEL_DIR   = '/kaggle/input/models/dfranzen/albucino-qwen3-8-flash-next-drafter/transformers/default/1'"
    assert old in cell['source'] and old_draft in cell['source']
    cell['source']=cell['source'].replace(old,"MODEL_DIR         = '/kaggle/input/models/"+TARGET.lower()+"'")
    cell['source']=cell['source'].replace(old_draft,"DRAFT_MODEL_DIR   = '/kaggle/input/models/"+DRAFT.lower()+"'")
    cell['source']+='\n# Exact small-file hashes from the actual CPU mount check.\n'
    cell['source']+=f'_hydra_qwen27_expected={report["metadata"]!r}\n'
    cell['source']+='''from hashlib import sha256 as _hydra_qwen27_hash
for _label,_root in [('target',Path(MODEL_DIR)),('draft',Path(DRAFT_MODEL_DIR))]:
    for _name,_record in _hydra_qwen27_expected[_label].items():
        if _hydra_qwen27_hash((_root/_name).read_bytes()).hexdigest()!=_record['sha256']:
            raise ValueError('27B metadata differs from CPU gate: '+_label+'/'+_name)
if TRUE_SUBMISSION:raise RuntimeError('This is a development-only 27B baseline')
'''
    launcher=notebook['cells'][14]['source']
    begin=launcher.index('# ---- validate target and create')
    end=launcher.index('# ---- launch detached and wait for health ----')
    launcher=launcher[:begin]+ARGS+'\n'+launcher[end:]
    for old,new in [('MEMFRAC=0.96','MEMFRAC=0.92'),('MAXREQ=10','MAXREQ=4'),
        ('CUDAGRAPH_MAXBS=10','CUDAGRAPH_MAXBS=4'),('MAMBA_CACHE=60','MAMBA_CACHE=24'),
        ('CHUNK=8192','CHUNK=2048'),('MAX_PREFILL=16384','MAX_PREFILL=2048'),
        ('FRSPEC=True','FRSPEC=False'),('LINEAR_BACKEND="flashinfer"','LINEAR_BACKEND="triton"'),
        ('SSM_DTYPE="bfloat16"','SSM_DTYPE="float32"')]:
        assert old in launcher;launcher=launcher.replace(old,new)
    # Remove the unused Flash-Next draft adapter, preserving the known installer.
    begin=launcher.index('def prepare_draft_view(')
    end=launcher.index('# ---- validate notebook inputs',begin)
    launcher=launcher[:begin]+launcher[end:]
    launcher=launcher.replace('        show_log_tail()\n        break',
        '        show_log_tail()\n        raise RuntimeError("27B serving process exited before health readiness")')
    compile(launcher,'qwen27-offline-launcher','exec')
    notebook['cells'][14]['source']=launcher
    provenance.update(candidate='qwen27-matched-baseline',experiment_variant='qwen27',
        model_candidate=TARGET,model_draft=DRAFT,model_cpu_gate=verified['kernel'],
        model_cpu_report_sha256=verified['report_sha256'],official_submission_eligible=False,
        notebook_wall_budget_seconds=7200,
        changed_components=['27B FP8 target','27B DFlash2 draft','27B-specific serving profile, four requests, FP32 SSM and Triton GDN'],
        retained_components=['Pennyroyal v2.5.3 runtime and image','Flexible planning plus exact inspection agent','All 25 public games','Sampling, prompt and scheduler policy','Two-hour total cap including startup and 600-second finalization reserve'],
        comparison_boundary='Practical complete deployment comparison, not isolated model size/training/precision effect. Untrained 27B checkpoint. No automatic promotion or official submission.',
        model_attribution=dict(target='Qwen Team, Apache-2.0; pinned official FP8 mirror by Mike Dan7',draft='Z-Lab DFlash2, Apache-2.0; pinned mirror by Dang Khoa',
            target_source='Qwen/Qwen3.8-27B-FP8@017b9c7af6b5689d5dd426a76e0bc077eb5ca20a',draft_source='z-lab/Qwen3.8-27B-DFlash2@50307d4c4cde6860d4eee73e2547cd786fe8e8a4'))
    cell['source']+=f'(WORKING_DIR/"hydra_model_candidate.json").write_text(json.dumps({provenance!r},indent=2))\n'
    compile(cell['source'][cell['source'].index('_hydra_qwen27_expected='):],'qwen27-metadata-preflight','exec')
    # Correct inherited run provenance so it does not claim unchanged weights/runtime settings.
    run=notebook['cells'][22]['source']
    marker='Path(WORKING_DIR / "hydra_provenance.json").write_text(json.dumps('
    start=run.index(marker)+len(marker);end=run.index(', indent=2))',start)
    actual=ast.literal_eval(run[start:end])
    actual.update(model_candidate=TARGET,model_draft=DRAFT,
        competition_changes='Untrained Qwen3.8-27B FP8/DFlash2 serving profile with existing flexible inspection agent; development only.')
    notebook['cells'][22]['source']=run[:start]+repr(actual)+run[end:]
    metadata.update(id='kunalsinghh25/arc-hydra-qwen27-matched-baseline',title='ARC Hydra Qwen27 Matched Baseline',model_sources=[TARGET,DRAFT])
    notebook['cells'][0]['source']='# ARC3 untrained Qwen3.8-27B offline gameplay baseline\n\nOfficial FP8 target with DFlash2, existing Pennyroyal runtime and flexible inspection agent. Total development cap 7200 seconds, including startup/saving. No official submission. Original upstream authors and licenses retained.'
    out=ROOT/'notebooks/qwen27_matched_baseline';out.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (out/name).write_text(json.dumps(value,indent=2)+'\n')
    manifest=dict(kernel=metadata['id'],wall_seconds=7200,
        files={n:sha256((out/n).read_bytes()).hexdigest() for n in ['submission.ipynb','kernel-metadata.json','provenance.json']})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))

if __name__=='__main__':build()
