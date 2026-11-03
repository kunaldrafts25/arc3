import json
import pytest
from scripts.profile_duck_requests import profile


def test_history_repetition_does_not_multiply_tool_failures():
    message=dict(role='tool',tool_call_id='same-call',content=json.dumps(dict(error='Python syntax error: invalid syntax')))
    record=dict(event='response',messages=[message],usage=dict(completion_tokens=20,prompt_tokens=100,
                 prompt_tokens_details=dict(cached_tokens=80)),finish_reason='tool_calls')
    result=profile([dict(event='request'),record,record])
    assert result['completed_responses']==2
    assert result['completed_response_tokens']==40
    assert result['distinct_visible_tool_results']==1
    assert result['ordinary_tool_errors']==1
    assert result['weighted_cache_fraction']==pytest.approx(0.8)


def test_expected_guard_stop_is_separate_from_python_failure():
    records=[dict(event='response',messages=[
        dict(role='tool',tool_call_id='a',content=json.dumps(dict(error='Traceback (most recent call last):\nStaleStateActionError: prevented stale action'))),
        dict(role='tool',tool_call_id='terminal',content=json.dumps(dict(error='TerminalStateActionError: prevented action after game_over'))),
        dict(role='tool',tool_call_id='b',content=json.dumps(dict(error='Traceback (most recent call last):\nValueError: empty list')))])]
    result=profile(records)
    assert result['ordinary_tool_errors']==1
    assert result['observed_stale_state_guard_stops']==1
    assert result['observed_terminal_state_guard_stops']==1
    assert result['weighted_cache_fraction'] is None
