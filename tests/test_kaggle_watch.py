from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from requests import Response
from requests.exceptions import HTTPError, Timeout

from scripts.kaggle_watch import observe


KERNEL='owner/exact-kernel/6'


def status(name):
    return SimpleNamespace(status=SimpleNamespace(name=name))


def http_error(code):
    response=Response()
    response.status_code=code
    return HTTPError(response=response)


def test_server_error_reconnects_same_version_until_authoritative_completion():
    api=Mock(spec=['kernels_logs_cli','kernels_status'])
    api.kernels_logs_cli.side_effect=[http_error(500),None]
    api.kernels_status.side_effect=[status('RUNNING'),status('COMPLETE')]
    sleep=Mock()
    assert observe(api,KERNEL,sleep=sleep).name=='COMPLETE'
    assert all(call.args==(KERNEL,) for call in api.kernels_logs_cli.call_args_list)
    assert all(call.args==(KERNEL,) for call in api.kernels_status.call_args_list)
    sleep.assert_called_once_with(15)


@pytest.mark.parametrize('code',[401,403,404])
def test_nontransient_http_error_is_not_retried(code):
    api=Mock(spec=['kernels_logs_cli','kernels_status'])
    api.kernels_logs_cli.side_effect=http_error(code)
    with pytest.raises(HTTPError):
        observe(api,KERNEL,sleep=Mock())
    api.kernels_logs_cli.assert_called_once()
    api.kernels_status.assert_not_called()


def test_transient_status_timeout_does_not_claim_cloud_failure():
    api=Mock(spec=['kernels_logs_cli','kernels_status'])
    api.kernels_status.side_effect=[Timeout(),status('ERROR')]
    assert observe(api,KERNEL,sleep=Mock()).name=='ERROR'
    assert api.kernels_logs_cli.call_count==2


def test_retry_exhaustion_keeps_cloud_termination_unproven():
    api=Mock(spec=['kernels_logs_cli','kernels_status'])
    api.kernels_status.return_value=status('RUNNING')
    with pytest.raises(RuntimeError,match='termination unproven'):
        observe(api,KERNEL,attempts=2,sleep=Mock())
    assert api.kernels_status.call_count==2
