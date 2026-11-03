from types import SimpleNamespace
from urllib.error import URLError
import pytest
from scripts.wait_local_backend import wait_local_backend


class Clock:
    def __init__(self):
        self.now = 0
    def __call__(self):
        return self.now
    def sleep(self, seconds):
        self.now += seconds


class Response:
    status = 200
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


def test_connection_failures_during_loading_do_not_restart_server():
    clock = Clock()
    process = SimpleNamespace(poll=lambda:None)
    attempts = []
    def open_health(url, timeout):
        attempts.append(clock())
        if clock() < 9:
            raise URLError('loading')
        return Response()
    wait_local_backend('local-health',30,process,clock=clock,sleep=clock.sleep,
                       opener=open_health,report=lambda *a,**k:None)
    assert clock()==9
    assert len(attempts)==4
    # The gameplay deadline belongs to the caller, after this return.
    assert clock()+900==909


def test_dead_server_and_startup_timeout_are_explicit_failures():
    clock = Clock()
    with pytest.raises(RuntimeError,match='exited'):
        wait_local_backend('local-health',30,SimpleNamespace(poll=lambda:1,returncode=1),
                           clock=clock,sleep=clock.sleep)
    def unavailable(*args,**kwargs):
        raise URLError('loading')
    with pytest.raises(TimeoutError):
        wait_local_backend('local-health',7,clock=clock,sleep=clock.sleep,
                           opener=unavailable,report=lambda *a,**k:None)
    assert clock()==7
