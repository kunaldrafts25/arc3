import json
from collections import Counter
from io import StringIO

from scripts.prepare_arc3_teacher_pilot import paired_replies,python_reply,request_level


def records():
    messages=[dict(role='system',content='Interface'),dict(role='user',content='Observed state')]
    assistant=dict(role='assistant',reasoning_content='Use the observed position.',tool_calls=[
        dict(id='call1',type='function',function=dict(name='python',arguments=json.dumps(dict(code="action({'action':'RIGHT'})"))))])
    tool=dict(role='tool',tool_call_id='call1',content='{"executed":true}')
    return [dict(event='request',messages=messages,analysis_step=1,request_index_within_turn=0,action=1),
        dict(event='response',messages=messages,analysis_step=1,request_index_within_turn=0,finish_reason='tool_calls'),
        dict(event='request',messages=messages+[assistant,tool,dict(role='user',content='FUTURE OBSERVATION')],analysis_step=2,action=2)]


def run(rows):
    class MemoryTrace:
        def open(self,**kwargs):return StringIO(''.join(json.dumps(r)+'\n' for r in rows))
    counts=Counter();return list(paired_replies(MemoryTrace(),counts)),counts


def test_recovers_exact_input_and_reply_without_future_observation():
    pairs,_=run(records());assert len(pairs)==1
    pair=pairs[0]
    assert 'FUTURE OBSERVATION' not in json.dumps(pair['request'])
    assert pair['assistant']['tool_calls'][0]['id']=='call1'
    assert python_reply(pair['assistant'],pair['results'])


def test_context_rewrite_and_unpaired_response_are_rejected():
    rows=records();rows[-1]['messages'][1]=dict(role='user',content='Rewritten history')
    pairs,counts=run(rows);assert not pairs and counts['context_changed_or_pruned']==1
    rows=records();rows[1]['request_index_within_turn']=9
    pairs,counts=run(rows);assert not pairs and counts['missing_matching_response']==1


def test_failed_tool_and_malformed_python_are_rejected():
    rows=records();assistant=rows[-1]['messages'][2]
    failed=[dict(role='tool',tool_call_id='call1',content='{"error":"NameError: missing state"}')]
    assert not python_reply(assistant,failed)
    assistant['tool_calls'][0]['function']['arguments']=json.dumps(dict(code='def broken('))
    assert not python_reply(assistant,[])


def test_real_completion_boundary_uses_one_based_next_action_number():
    assert request_level(13,[4,13,27])==1
    assert request_level(14,[4,13,27])==2
    assert request_level(28,[4,13,27]) is None
