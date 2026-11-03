"""Wait for local model readiness before starting a public gameplay budget."""
import time
from urllib.request import urlopen


def wait_local_backend(url, deadline_epoch, process=None, *, clock=time.time,
                       sleep=time.sleep, opener=urlopen, report=print):
    """Bound startup separately; never consume a public gameplay deadline.

    A live process plus a transient HTTP failure is still loading, not stopped.
    A process exit or an exhausted startup allowance is an explicit failure.
    """
    started = clock()
    next_report = started
    last_error = 'no successful health response'
    while clock() < deadline_epoch:
        if process is not None and process.poll() is not None:
            raise RuntimeError(f'Model server exited before readiness: {process.returncode}')
        try:
            with opener(url, timeout=5) as response:
                if response.status == 200:
                    report(f'Local model ready after {clock()-started:.1f}s of public readiness wait', flush=True)
                    return
                last_error = f'health HTTP {response.status}'
        except Exception as error:
            last_error = f'{type(error).__name__}: {error}'
        now = clock()
        if now >= next_report:
            report(f'Waiting for local model: {last_error}; {max(0,deadline_epoch-now):.0f}s startup allowance left', flush=True)
            next_report = now+60
        sleep(min(3, max(0, deadline_epoch-clock())))
    raise TimeoutError(f'Local model did not become ready within startup allowance: {last_error}')
