"""Guarded original-account development comparison; no competition submissions.

Waits for the declared quota refresh, preserves a shared ARC2 quota floor, checks
active original-account GPU jobs, journals before each mutation, observes exact
versions and downloads/analyzes results. Uncertain launches are never retried.
"""
import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
DIRECTORY = ROOT/'reports/arc3/prediction-ablation'
TERMINAL = {'COMPLETE','ERROR','CANCEL_ACKNOWLEDGED'}
MAX_DEVELOPMENT_SECONDS = 7200


def now():
    return datetime.now(timezone.utc)


def read_with_retry(operation, sleep=time.sleep):
    """Bounded retries for observations only; never wrap kernels_push here."""
    from requests.exceptions import ConnectionError, HTTPError, Timeout
    for attempt in range(5):
        try:
            return operation()
        except (ConnectionError,Timeout,HTTPError) as exc:
            retryable = not isinstance(exc,HTTPError) or (exc.response is not None
                and (exc.response.status_code == 429 or exc.response.status_code >= 500))
            if not retryable or attempt == 4:
                raise
            print('Transient read failure:',type(exc).__name__,'attempt',attempt+1,flush=True)
            sleep(60)


def save(path, value):
    value['recorded_at'] = now().isoformat()
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)


def resource_decision(plan, available, reserved, paid, active, remaining_runs, at):
    if paid:
        return False,'paid scaling enabled'
    if at < datetime.fromisoformat(plan['not_before']):
        return False,'waiting for original-account quota refresh'
    if at >= datetime.fromisoformat(plan['expires']):
        return False,'experiment launch window expired'
    if reserved > 0 or active:
        return False,'shared compute reserved or another GPU development job active'
    needed = remaining_runs*plan['whole_notebook_seconds']+plan['arc2_free_seconds_floor']
    if available < needed:
        return False,f'need {needed} free seconds including shared ARC2 floor'
    return True,'free quota and shared-job checks passed'


def validate_packages(plan):
    if type(plan['whole_notebook_seconds']) is not int or not 1800 <= plan['whole_notebook_seconds'] <= MAX_DEVELOPMENT_SECONDS:
        raise ValueError('ARC3 development sessions have a hard two-hour total cap')
    if [v['variant'] for v in plan['variants']] != ['control','prediction']:
        raise ValueError('Only the frozen two-variant ARC3 experiment is allowed')
    for variant in plan['variants']:
        package = (ROOT/variant['package']).resolve()
        if not package.is_relative_to(ROOT/'notebooks/arc3_prediction_ablation_v2'):
            raise ValueError('Package outside ARC3 ablation directory')
        for name,digest in variant['files'].items():
            if sha256((package/name).read_bytes()).hexdigest() != digest:
                raise ValueError('Frozen experiment package changed: '+variant['variant']+'/'+name)
        metadata = json.loads((package/'kernel-metadata.json').read_text())
        if (metadata['id'] != variant['kernel'] or not metadata['id'].startswith('kunalsinghh25/arc-hydra-')
                or metadata['enable_internet'] or not metadata['enable_gpu']
                or not metadata['is_private'] or metadata['competition_sources'] != ['arc-prize-2026-arc-agi-3']
                or metadata['machine_shape'] != 'NvidiaRtxPro6000'
                or re.sub(r'[^a-z0-9]+','-',metadata['title'].lower()).strip('-') != variant['kernel'].split('/')[1]):
            raise ValueError('Unexpected experiment account, privacy, accelerator or competition attachment')
        provenance = json.loads((package/'provenance.json').read_text())
        if provenance['official_submission_eligible'] is not False:
            raise ValueError('Development packages must not be submitted')


def inspect_resources(api, plan, remaining_runs):
    quota = read_with_retry(api.quota_view)
    gpu = quota.gpu_quota
    available = (gpu.total_time_allowed-gpu.time_used-gpu.time_reserved).total_seconds()
    # Avoid an account-wide scan while no launch is possible. At launch time,
    # inspect recent original-account GPU notebook sessions as well as quota.
    active = []
    if now() >= datetime.fromisoformat(plan['not_before']) and available >= plan['whole_notebook_seconds']:
        kernels = read_with_retry(lambda:api.kernels_list(mine=True,page_size=100,sort_by='dateRun')) or []
        cutoff = now()-timedelta(days=2)
        for kernel in kernels:
            stamp = kernel.last_run_time
            # List summaries currently report enable_gpu=False even for our
            # confirmed RTX runs. Never use that default to skip a live shared
            # job; accelerator identity needs exact-version metadata.
            if stamp is not None and stamp.replace(tzinfo=timezone.utc)<cutoff:
                continue
            status = read_with_retry(lambda:api.kernels_status(kernel.ref)).status.name
            if status not in TERMINAL:
                active.append(dict(kernel=kernel.ref,status=status,accelerator='unclassified'))
    allowed,reason = resource_decision(plan,available,gpu.time_reserved.total_seconds(),
        gpu.is_pay_to_scale_enabled,active,remaining_runs,now())
    return dict(allowed=allowed,reason=reason,available_gpu_seconds=available,
                reserved_gpu_seconds=gpu.time_reserved.total_seconds(),
                pay_to_scale_enabled=gpu.is_pay_to_scale_enabled,
                refresh=str(quota.quota_refresh_time),active_gpu_jobs=active,
                arc2_free_seconds_floor=plan['arc2_free_seconds_floor'])


def download_and_analyze(api, kernel, directory):
    from scripts.analyze_duck_run import analyze
    from scripts.audit_arc3_serving import audit
    from scripts.analyze_prediction_adoption import analyze as adoption_audit
    # Excludes giant request/pickle/image archives; includes actual transcripts,
    # per-game prediction stores/events and exact installation/lifecycle evidence.
    pattern = r'(^|/)(benchmark\.json|hydra_.*\.json|serve\.log)$|\.prediction(\.events)?\.jsonl?$|\.inspection\.events\.jsonl$|transcripts/.*\.txt$'
    read_with_retry(lambda:api.kernels_output(kernel,str(directory),file_pattern=pattern,quiet=True))
    analysis = analyze(directory)
    if analysis['games'] != 25 or not analysis['model_gameplay_verified']:
        raise RuntimeError('All 25 games must show substantive actual model gameplay')
    lifecycle = json.loads((directory/'hydra_lifecycle.json').read_text())
    if lifecycle['phase'] != 'run_finished' or lifecycle.get('error'):
        raise RuntimeError('Completed model/game lifecycle required')
    if (directory/'serve.log').exists():
        serving = audit(directory/'serve.log',directory/'benchmark.json')
        (directory/'serving-analysis.json').write_text(json.dumps(serving,indent=2)+'\n',encoding='utf-8')
    adoption = adoption_audit(directory,origin='model')
    (directory/'prediction-adoption.json').write_text(json.dumps(adoption,indent=2)+'\n',encoding='utf-8')
    return analysis


def launch_development(api, package, wall_seconds):
    """Set an external hard limit as well as the notebook's internal deadline."""
    if type(wall_seconds) is not int or not 1800 <= wall_seconds <= MAX_DEVELOPMENT_SECONDS:
        raise ValueError('ARC3 development sessions have a hard two-hour total cap')
    return api.kernels_push(str(package),timeout=str(wall_seconds),acc='NvidiaRtxPro6000')


def accepted_exact(variant, intent):
    """Recover only an acknowledged exact version; never retry a mutation."""
    if (intent.get('phase') != 'accepted' or intent.get('kernel') != variant['kernel']
            or intent.get('files') != variant['files']
            or intent.get('hard_session_timeout_seconds') != MAX_DEVELOPMENT_SECONDS):
        raise RuntimeError('Uncertain or mismatched launch journal; manual reconciliation required')
    version = intent.get('response',{}).get('versionNumber')
    if type(version) is not int or version < 1:
        raise RuntimeError('Accepted launch has no exact version')
    return variant['kernel']+'/'+str(version)


def pid_alive(pid):
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE,wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x00100000,False,pid)
        if not handle:
            return ctypes.get_last_error() != 87  # Access denied is not proof of exit.
        try:
            return kernel.WaitForSingleObject(handle,0) != 0
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid,0)
    except ProcessLookupError:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true',help='Wait and execute the guarded development pair')
    parser.add_argument('--resume',action='store_true',help='Reconcile accepted exact versions after the original local observer exited')
    parser.add_argument('--launch-until',help='Explicit renewed launch window; preserves the frozen packages and original plan')
    args = parser.parse_args()
    plan_path = DIRECTORY/'plan.json'
    plan = json.loads(plan_path.read_text())
    validate_packages(plan)
    if args.launch_until:
        if not args.resume:
            raise ValueError('Renewed window is only for explicit recovery')
        end = datetime.fromisoformat(args.launch_until)
        if end.tzinfo is None or end <= now() or end > datetime(2026,11,2,0,tzinfo=timezone.utc):
            raise ValueError('Recovery launch window must end before the final deadline day')
        plan['expires'] = end.isoformat()
    token_path = ROOT/'.kaggle/access_token'
    token = token_path.read_text(encoding='utf-8-sig').strip()
    token_digest = sha256(token.encode()).digest()
    os.environ['KAGGLE_API_TOKEN'] = token
    os.environ['KAGGLE_CONFIG_DIR'] = str(token_path.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    if not args.run and not args.resume:
        print(json.dumps(inspect_resources(api,plan,2),indent=2))
        return
    lock = DIRECTORY/'runner.lock'
    state_path = DIRECTORY/'runner-state.json'
    if args.resume:
        previous = json.loads(state_path.read_text())
        if pid_alive(previous['pid']):
            raise RuntimeError('Original observer is still live; cannot resume')
        archive = DIRECTORY/('observer-before-recovery-'+now().strftime('%Y%m%dT%H%M%S')+'.json')
        archive.write_text(json.dumps(previous,indent=2)+'\n',encoding='utf-8')
        lock = DIRECTORY/'recovery.lock'
    with lock.open('x') as stream:
        stream.write(str(os.getpid()))
    state = dict(phase='waiting',pid=os.getpid(),plan_sha256=sha256(plan_path.read_bytes()).hexdigest(),
                 scope='Two development notebooks only; no official submission or automatic promotion',
                 variants=[],next_resource_check=None)
    if args.resume:
        state.update(recovery=True,launch_until=plan['expires'],previous_observer_archive=str(archive.relative_to(ROOT)))
    save(state_path,state)
    def validate():
        if (DIRECTORY/'cancel.requested').exists():
            raise RuntimeError('ARC3 experiment cancellation requested')
        if sha256(plan_path.read_bytes()).hexdigest() != state['plan_sha256']:
            raise RuntimeError('Frozen experiment plan changed')
        if sha256(token_path.read_text(encoding='utf-8-sig').strip().encode()).digest() != token_digest:
            raise RuntimeError('Original-account credential changed')
        validate_packages(plan)
    try:
        for index,variant in enumerate(plan['variants']):
            directory = ROOT/f"reports/kaggle/prediction-matched-{variant['variant']}-v1"
            directory.mkdir(parents=True,exist_ok=True)
            journal = directory/'launch.json'
            # Existing/uncertain mutation journals require explicit reconciliation.
            if journal.exists() and not args.resume:
                raise RuntimeError('Existing launch journal; reconcile instead of relaunching')
            if journal.exists():
                exact = accepted_exact(variant,json.loads(journal.read_text()))
                state.update(phase='observing',current_variant=variant['variant'],exact_kernel=exact,next_resource_check=None)
                save(state_path,state)
                status = read_with_retry(lambda:api.kernels_status(exact)).status.name
                if status == 'COMPLETE':
                    analysis = download_and_analyze(api,exact,directory)
                    state['variants'].append(dict(variant=variant['variant'],kernel=exact,analysis=analysis))
                    save(state_path,state)
                    continue
                raise RuntimeError('Recovered exact job is '+status+'; inspect this version without relaunching')
            next_check = 0
            while True:
                validate()
                if now() >= datetime.fromisoformat(plan['expires']):
                    state.update(phase='window_expired');save(state_path,state);return
                if time.monotonic() >= next_check:
                    resources = inspect_resources(api,plan,len(plan['variants'])-index)
                    state.update(phase='waiting',current_variant=variant['variant'],resources=resources,
                                 next_resource_check=(now()+timedelta(minutes=15)).isoformat())
                    save(state_path,state)
                    if resources['pay_to_scale_enabled']:
                        raise RuntimeError('Paid scaling enabled')
                    if resources['allowed']:
                        break
                    next_check = time.monotonic()+900
                time.sleep(60)
            validate()
            intent = dict(phase='launching',variant=variant['variant'],kernel=variant['kernel'],
                          files=variant['files'],resources=resources,
                          hard_session_timeout_seconds=plan['whole_notebook_seconds'])
            with journal.open('x',encoding='utf-8') as stream:
                json.dump(intent,stream,indent=2)
            try:
                response = launch_development(api,ROOT/variant['package'],plan['whole_notebook_seconds'])
            except Exception as exc:
                intent.update(phase='outcome_unconfirmed',error_type=type(exc).__name__)
                save(journal,intent)
                raise RuntimeError('Uncertain launch; will not retry') from exc
            intent.update(phase='accepted',response=response.to_dict())
            save(journal,intent)
            exact = variant['kernel']+'/'+str(response.version_number)
            state.update(phase='observing',exact_kernel=exact,next_resource_check=None)
            save(state_path,state)
            observation_deadline = time.monotonic()+plan['whole_notebook_seconds']+3600
            while time.monotonic() < observation_deadline:
                validate()
                status = read_with_retry(lambda:api.kernels_status(exact)).status.name
                state['kernel_status'] = status
                save(state_path,state)
                if status in TERMINAL:
                    break
                time.sleep(60)
            if state.get('kernel_status') != 'COMPLETE':
                raise RuntimeError('Development job not COMPLETE; inspect same exact version')
            analysis = download_and_analyze(api,exact,directory)
            state['variants'].append(dict(variant=variant['variant'],kernel=exact,analysis=analysis))
            save(state_path,state)
        state.update(phase='comparison_complete',
            next_action='Inspect model-generated hypotheses, adoption, counterexamples, per-game completion/action efficiency and token/time costs before selecting or officially submitting a full-budget candidate.')
        save(state_path,state)
    except Exception as exc:
        state.update(phase='stopped',error_type=type(exc).__name__,reason=str(exc))
        save(state_path,state)
        raise


if __name__ == '__main__':
    main()
