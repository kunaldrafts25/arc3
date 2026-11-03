"""Observe one exact Kaggle version through long, quiet compilation stages."""
import argparse
from contextlib import redirect_stderr, redirect_stdout
import os
from pathlib import Path
import re
import time

from requests.exceptions import ConnectionError, HTTPError, Timeout

ROOT=Path(__file__).resolve().parents[1]


def retryable(exc):
    return isinstance(exc,(ConnectionError,Timeout)) or (
        isinstance(exc,HTTPError) and exc.response is not None
        and exc.response.status_code in (500,502,503,504)
    )


def observe(api,kernel,attempts=30,delay=15,sleep=time.sleep):
    """Retry only observation; never infer cloud termination from stream failure."""
    for attempt in range(attempts):
        try:
            api.kernels_logs_cli(kernel,follow=True)
        except (HTTPError,ConnectionError,Timeout) as exc:
            if not retryable(exc):
                raise
            print('Transient log-stream error:',type(exc).__name__,flush=True)
        try:
            status=api.kernels_status(kernel).status
        except (HTTPError,ConnectionError,Timeout) as exc:
            if not retryable(exc):
                raise
            print('Cloud status temporarily unavailable:',type(exc).__name__,flush=True)
        else:
            print('Authoritative cloud status:',status,flush=True)
            if status.name in ('COMPLETE','ERROR','CANCEL_ACKNOWLEDGED'):
                return status
            if status.name not in ('QUEUED','RUNNING','NEW_SCRIPT','CANCEL_REQUESTED'):
                raise RuntimeError(f'Unrecognized cloud status: {status}')
        if attempt+1<attempts:
            print('Reconnecting observation to the same exact version in',delay,'seconds',flush=True)
            sleep(delay)
    raise RuntimeError('Observation retry limit reached; cloud termination unproven. Recheck the same version.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kernel',help='Exact owner/slug/version; never follows latest')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--token-file',default='access_token')
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[1-9][0-9]*',args.kernel):
        parser.error('An exact owner/slug/version is required')
    output=(ROOT/args.output).resolve()
    if not output.is_relative_to(ROOT):
        parser.error('Observer output must remain in the project')
    token_path=(ROOT/'.kaggle'/args.token_file).resolve()
    if token_path.parent != (ROOT/'.kaggle').resolve():
        parser.error('Select a token file inside the project .kaggle directory')
    os.environ['KAGGLE_API_TOKEN']=token_path.read_text(encoding='utf-8-sig').strip()
    os.environ['KAGGLE_CONFIG_DIR']=str(ROOT/'.kaggle')
    from kaggle.api.kaggle_api_extended import KaggleApi
    api=KaggleApi()
    api.authenticate()
    # Installed CLI 2.2.5 uses these limits to reconnect and deduplicate SSE
    # events. Quiet native compilation can outlast the default five failures.
    # Only observation changes: no save, push, cancellation or submission calls.
    if not hasattr(api,'_LOG_STREAM_MAX_FAILURES'):
        raise RuntimeError('Inspect the installed SDK log-stream API before using this observer')
    api._LOG_STREAM_MAX_FAILURES=120
    api._LOG_STREAM_RECONNECT_DELAY_SEC=5
    output.parent.mkdir(parents=True,exist_ok=True)
    # Retain the encoding of existing PowerShell-captured live logs.
    with output.open('w',encoding='utf-16') as stream, redirect_stdout(stream), redirect_stderr(stream):
        print('Observing exact version:',args.kernel,flush=True)
        try:
            observe(api,args.kernel)
        finally:
            # A returned/failed observer is not a terminal cloud-job result.
            try:
                print('Observer ended; authoritative cloud status:',api.kernels_status(args.kernel).status,flush=True)
            except Exception as exc:
                print('Observer ended; cloud status unavailable:',type(exc).__name__,flush=True)


if __name__=='__main__':
    main()
