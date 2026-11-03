"""Journal one capped deadline screen; observe exact accepted version without relaunching."""
import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

from scripts.run_prediction_ablation import read_with_retry, launch_development, save, download_and_analyze

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT/'notebooks/arc3_deadline_candidate'
DIRECTORY = ROOT/'reports/arc3/deadline-candidate'
OUTPUT = ROOT/'reports/kaggle/deadline-candidate-v1'
TERMINAL = {'COMPLETE','ERROR','CANCEL_ACKNOWLEDGED'}


def validate():
    manifest = json.loads((PACKAGE/'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        if sha256((PACKAGE/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen candidate changed: '+name)
    meta = json.loads((PACKAGE/'kernel-metadata.json').read_text())
    expected_models = [
        'dfranzen/albucino-qwen3-8-flash-next-drafter/Transformers/default/1',
        'dfranzen/intel-qwen3.8-flash-next-w4a16-autoround/Transformers/default/1']
    if (meta['id'] != manifest['kernel'] or manifest['development_wall_seconds'] != 7200
            or manifest['official_wall_seconds'] != 32400 or meta['enable_internet'] is not False
            or meta['enable_gpu'] is not True or meta['enable_tpu'] is not False
            or meta['is_private'] is not True or meta['machine_shape'] != 'NvidiaRtxPro6000'
            or meta['competition_sources'] != ['arc-prize-2026-arc-agi-3']
            or meta['model_sources'] != expected_models):
        raise ValueError('Unexpected deadline package or resource configuration')
    return manifest


def resources(api, development=True):
    gpu = read_with_retry(api.quota_view).gpu_quota
    active, scanned = [], []
    cutoff = datetime.now(timezone.utc)-timedelta(days=2)
    known_cpu = 'kunalsinghh25/arc-hydra-flashnext-training-cpu-probe'
    cpu_launch = json.loads((ROOT/'reports/kaggle/flashnext-training-cpu-probe-v2/launch.json').read_text())
    cpu_package = ROOT/'notebooks/flashnext_training_cpu_probe_v2'
    for name,digest in cpu_launch['files'].items():
        if sha256((cpu_package/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Known CPU package changed')
    cpu_meta = json.loads((cpu_package/'kernel-metadata.json').read_text())
    if (cpu_meta['enable_gpu'] is not False or cpu_meta['enable_tpu'] is not False
            or cpu_meta.get('machine_shape') or not cpu_launch['cpu_only']):
        raise ValueError('Known CPU job is not CPU-only')
    for kernel in read_with_retry(lambda:api.kernels_list(mine=True,page_size=100,sort_by='dateRun')) or []:
        if kernel.last_run_time and kernel.last_run_time.replace(tzinfo=timezone.utc) < cutoff:
            continue
        exact = known_cpu+'/2' if kernel.ref == known_cpu else kernel.ref
        status = read_with_retry(lambda:api.kernels_status(exact)).status.name
        row = dict(kernel=exact,status=status,accelerator='cpu-verified' if kernel.ref == known_cpu else 'unclassified')
        scanned.append(row)
        if status not in TERMINAL and kernel.ref != known_cpu:
            active.append(row)
    available = (gpu.total_time_allowed-gpu.time_used-gpu.time_reserved).total_seconds()
    needed = (7200 if development else 0)+10800+32400
    allowed = not gpu.is_pay_to_scale_enabled and not gpu.time_reserved.total_seconds() and not active and available >= needed
    # Leave substantial time for the official nine-hour run and queue delays.
    allowed = allowed and datetime.now(timezone.utc) < datetime(2026,11,2,8 if development else 12,tzinfo=timezone.utc)
    return dict(allowed=bool(allowed),available_gpu_seconds=available,
        reserved_gpu_seconds=gpu.time_reserved.total_seconds(),pay_to_scale_enabled=gpu.is_pay_to_scale_enabled,
        needed_seconds=needed,arc2_floor_seconds=10800,official_reserve_seconds=32400,
        active_shared_jobs=active,recent_jobs=scanned)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch',action='store_true')
    parser.add_argument('--observe',action='store_true')
    args=parser.parse_args()
    if args.launch and args.observe:raise ValueError('Choose launch or observation')
    manifest=validate()
    token=ROOT/'.kaggle/access_token'
    os.environ['KAGGLE_API_TOKEN']=token.read_text(encoding='utf-8-sig').strip()
    os.environ['KAGGLE_CONFIG_DIR']=str(token.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi();api.authenticate()
    DIRECTORY.mkdir(parents=True,exist_ok=True);OUTPUT.mkdir(parents=True,exist_ok=True)
    journal=OUTPUT/'launch.json'
    if args.observe:
        state=json.loads(journal.read_text())
        if state['phase']!='accepted' or state['files']!=manifest['files']:
            raise RuntimeError('Uncertain or mismatched launch: reconcile, never relaunch')
        exact=state['kernel']+'/'+str(state['response']['versionNumber'])
        status=read_with_retry(lambda:api.kernels_status(exact)).status.name
        observed=dict(phase='observing',exact_kernel=exact,kernel_status=status)
        if status=='COMPLETE':
            analysis=download_and_analyze(api,exact,OUTPUT)
            read_with_retry(lambda:api.kernels_output(exact,str(OUTPUT),
                file_pattern=r'\.study(\.events)?\.jsonl?$',quiet=True))
            actual=json.loads((OUTPUT/'hydra_deadline_provenance.json').read_text())
            expected=json.loads((PACKAGE/'provenance.json').read_text())
            if actual!=expected:raise ValueError('Executed candidate provenance differs')
            for name,field in [('hydra_inspection_extension.json','inspection_extension'),
                               ('hydra_prediction_extension.json','prediction_extension'),
                               ('hydra_study_extension.json','study_extension')]:
                if json.loads((OUTPUT/name).read_text())!=expected[field]:
                    raise ValueError('Executed extension differs: '+name)
            observed.update(phase='evaluation_complete',analysis=analysis,
                promotion='Undecided; compare actual gameplay with incumbent before any submission')
        elif status in TERMINAL:
            observed['phase']='remote_terminal_failure'
        save(DIRECTORY/'state.json',observed)
        print(json.dumps(observed,indent=2));return
    checked=resources(api)
    save(DIRECTORY/'resource-check.json',checked)
    print(json.dumps({k:v for k,v in checked.items() if k!='recent_jobs'},indent=2),flush=True)
    if not args.launch:return
    if not checked['allowed']:raise RuntimeError('Shared quota, job or deadline guard refused launch')
    state=dict(phase='launching',kernel=manifest['kernel'],files=manifest['files'],
        hard_session_timeout_seconds=7200,resources=checked,
        scope='One two-hour real-game FlashNext composition screen. No training or automatic official submission.')
    with journal.open('x',encoding='utf-8') as stream:json.dump(state,stream,indent=2)
    try:response=launch_development(api,PACKAGE,7200)
    except Exception as exc:
        state.update(phase='outcome_unconfirmed',error_type=type(exc).__name__);save(journal,state)
        raise RuntimeError('Uncertain launch: reconcile instead of retrying') from exc
    state.update(phase='accepted',response=response.to_dict());save(journal,state)
    print(json.dumps(dict(phase=state['phase'],kernel=state['kernel'],response=state['response']),indent=2))


if __name__=='__main__':main()
