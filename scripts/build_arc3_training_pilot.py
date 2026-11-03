"""Build a two-hour actual BF16-LoRA pilot after the native CPU data gate."""
from hashlib import sha256
import ast
import json
from pathlib import Path
import textwrap

from scripts.build_qwen27_probe import TARGET
from scripts.build_arc3_training_data_offline_probe import BF16,EXTRACT

ROOT=Path(__file__).resolve().parents[1]


def build():
    gate=ROOT/'reports/kaggle/training-data-offline-probe-v2'
    verified=json.loads((gate/'verified.json').read_text())
    report_path=gate/'training-data-probe.json'
    if verified['status']!='COMPLETE' or sha256(report_path.read_bytes()).hexdigest()!=verified['report_sha256']:
        raise ValueError('Completed native CPU data gate required')
    cpu_package=ROOT/'notebooks/training_data_offline_probe_v2'
    if any(sha256((cpu_package/name).read_bytes()).hexdigest()!=digest for name,digest in verified['files'].items()):
        raise ValueError('Executed native CPU gate package changed')
    report=json.loads(report_path.read_text())
    if not report['passed'] or report['examples_passed']!=231 or report['errors']:
        raise ValueError('Native processor/tensor/adapter placement gate incomplete')
    data=json.loads((ROOT/'reports/arc3/qwen27-training-pilot/input-package.json').read_text())
    if verified['input_archive_sha256']!=data['archive_sha256']:raise ValueError('CPU-gated training inputs changed')
    expected=json.loads((ROOT/'reports/kaggle/qwen27-cpu-preflight-v2/qwen27-preflight.json').read_text())
    metadata=expected['metadata']['target']
    trainer=(ROOT/'hydra/arc3_lora_trainer.py').read_text()
    compile(trainer,'actual-arc3-lora-trainer','exec')
    exporter=(ROOT/'hydra/arc3_lora_export.py').read_text()
    compile(exporter,'actual-arc3-lora-exporter','exec')
    runtime_source=(ROOT/'reports/research/arc3-training-selection-20261101/serving-source/lora.py').read_text()
    if sha256(runtime_source.encode()).hexdigest()!='368221bec72a8c75e900e46b76fd80c6c15a1adf929b9e069684c159c89bacee':
        raise ValueError('Pinned actual serving adapter loader changed')
    matches=[node for node in ast.walk(ast.parse(runtime_source)) if isinstance(node,ast.FunctionDef) and node.name=='_normalize_in_proj_qkvz']
    if len(matches)!=1:raise ValueError('Pinned GDN normalizer not unique')
    normalizer='import torch\nfrom typing import Dict\n'+textwrap.dedent(ast.get_source_segment(runtime_source,matches[0]))+'\n'
    compile(normalizer,'actual-runtime-gdn-normalizer','exec')
    # The installer/driver setup has actually served the same architecture on
    # this GPU. Stop before target-specific validation or any server launch.
    original=json.loads((ROOT/'notebooks/qwen27_matched_baseline/submission.ipynb').read_text())['cells'][14]['source']
    installer=original[:original.index('# ---- validate the actual CPU-inspected FP8 target')]
    source='''import time,json,os,sys,subprocess,signal
from pathlib import Path
NOTEBOOK_START_TIME=time.time()
WORKING_DIR=Path('/kaggle/working')
MODEL_DIR='/kaggle/input/models/'''+BF16.lower()+"'\n"
    source+="WHEELHOUSE_DIR='/kaggle/input/datasets/dfranzen/pennyroyal-v253'\nSERVED_MODEL_NAME='training-only'\nSERVED_MODEL_PORT=8001\n"
    source+="if os.environ.get('KAGGLE_IS_COMPETITION_RERUN','').lower() in ['1','true']:raise RuntimeError('Development training only')\n"
    source+=installer+"\nuv=[str(Path(PREFIX)/'bin/uv')]\n"
    constants=dict(ARCHIVE_SHA256=data['archive_sha256'],EXPECTED_INPUT_MANIFEST=data['manifest'],
        MODEL_PATH=expected['target_path'],BF16_PATH='/kaggle/input/models/'+BF16.lower(),EXPECTED_TARGET_METADATA=metadata)
    source+='\n'.join(name+'='+repr(value) for name,value in constants.items())+'\n'
    # Extract only explicitly hashed inputs before launching any training process.
    extract=EXTRACT.replace("assets=work/'training-assets'","assets=WORKING_DIR/'training-assets'")
    source+="from hashlib import sha256\nwork=WORKING_DIR\nbundle=WORKING_DIR/'training-dependencies'\nbundle.mkdir(exist_ok=True)\n"+extract
    source+="run([*uv,'pip','install','--python',PYTHON,'--no-index','--no-deps',*sorted(bundle.glob('*.whl'))],env=install_env)\n"
    source+="run([*uv,'pip','check','--python',PYTHON],env=install_env)\n"
    source+=f"(WORKING_DIR/'arc3_lora_trainer.py').write_text({trainer!r})\n"
    source+=f"(WORKING_DIR/'arc3_lora_export.py').write_text({exporter!r})\n"
    source+=f"(WORKING_DIR/'sglang_gdn_normalizer.py').write_text({normalizer!r})\n"
    source+='''training_deadline=NOTEBOOK_START_TIME+7200-900
if time.time()+1200>=training_deadline:raise RuntimeError('Startup left too little actual training time')
training_output=WORKING_DIR/'sft-pilot'
command=[PYTHON,str(WORKING_DIR/'arc3_lora_trainer.py'),'--assets',str(assets),'--model',MODEL_DIR,
    '--processor',MODEL_PATH,'--output',str(training_output),'--deadline',str(training_deadline)]
log=WORKING_DIR/'training.log'
with log.open('w') as stream:
    process=subprocess.Popen(command,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    try:
        while process.poll() is None:
            status_path=training_output/'training-report.json'
            status=json.loads(status_path.read_text()) if status_path.is_file() else {}
            if time.time()>NOTEBOOK_START_TIME+2400 and status.get('optimizer_steps',0)<1:
                raise RuntimeError('No real optimizer step within40minutes including startup; stop the owned training process')
            if time.time()>NOTEBOOK_START_TIME+7200-120:
                raise RuntimeError('Owned training process exceeded finalization reserve')
            time.sleep(10)
        if process.returncode:raise RuntimeError('Actual training child failed; inspect training.log/report')
    finally:
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
report=json.loads((training_output/'training-report.json').read_text())
if report['phase']!='complete' or report['optimizer_steps']<1:raise RuntimeError('No complete actual training result')
print(json.dumps({k:v for k,v in report.items() if k not in ['examples','validation','lora_targets']},indent=2))
'''
    compile(source,'actual-arc3-training-pilot','exec')
    provenance=dict(candidate='qwen27-language-lora-pilot',official_submission_eligible=False,
        hard_session_timeout_seconds=7200,internal_total_seconds=7200,training_reserve_seconds=900,
        model=BF16,processor=TARGET,cpu_data_gate=verified['kernel'],cpu_report_sha256=verified['report_sha256'],
        input_archive_sha256=data['archive_sha256'],trainer_sha256=sha256(trainer.encode()).hexdigest(),
        exporter_sha256=sha256(exporter.encode()).hexdigest(),
        runtime_gdn_normalizer_sha256=sha256(normalizer.encode()).hexdigest(),
        initial_plan='At most one epoch of158 actual teacher examples at16K, rank16 on400 supported language attention/recurrent/feed-forward projections,108789760 adapter parameters, LR1e-5, accumulation4. Save after first update and every8updates. Stop if no update by40minutes. Actual CUDA loss/gradients/optimizer, finite nonzero adapter and independent-slot save/reload checks. No serving/gameplay/official-score claim.',
        cpu_placement_boundary='CPU native inventory covers all400 selected projections; CPU PEFT placement checked64 attention projections only. Actual400-module placement and shapes must be checked on the GPU before training.',
        deployment_boundary='Exact runtime source supports the selected packed LoRA families and DFlash. Enabling LoRA disables a fused GDN projection optimization. Actual saved adapter serving, correct request routing and performance are still required; this training notebook cannot be submitted.')
    provenance_write=f"(WORKING_DIR/'hydra_training_provenance.json').write_text(json.dumps({provenance!r},indent=2))\n"
    source=source.replace("WORKING_DIR=Path('/kaggle/working')\n","WORKING_DIR=Path('/kaggle/working')\n"+provenance_write,1)
    base=json.loads((ROOT/'notebooks/qwen27_matched_baseline/kernel-metadata.json').read_text())
    base.update(id='kunalsinghh25/arc-hydra-qwen27-lora-pilot',title='ARC Hydra Qwen27 Lora Pilot',
        code_file='train.ipynb',dataset_sources=['dfranzen/pennyroyal-v253',data['dataset']],
        model_sources=[BF16,TARGET],kernel_sources=[],competition_sources=['arc-prize-2026-arc-agi-3'],
        enable_gpu=True,enable_tpu=False,enable_internet=False,is_private=True,machine_shape='NvidiaRtxPro6000')
    notebook=dict(nbformat=4,nbformat_minor=4,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3')),
        cells=[dict(cell_type='markdown',metadata={},source='# ARC3 actual teacher-adaptation pilot\n\nStrict7200-second total development session. BF16 frozen original27B with rank16 supported language adapters. Real observed public teacher data, whole-game gradient holdout. This is a research candidate; CPU gates/loss are not gameplay success. No official submission. Qwen, Hugging Face, FLA and original agent authors retain attribution/licenses.'),
            dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None)])
    output=ROOT/'notebooks/qwen27_lora_pilot';output.mkdir(exist_ok=True)
    for name,value in [('train.ipynb',notebook),('kernel-metadata.json',base),('provenance.json',provenance)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n')
    result=dict(kernel=base['id'],wall_seconds=7200,files={name:sha256((output/name).read_bytes()).hexdigest() for name in ['train.ipynb','kernel-metadata.json','provenance.json']})
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':build()
