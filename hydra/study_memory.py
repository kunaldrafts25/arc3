"""Bounded model-authored hypotheses, carried across sandbox calls/context drains.

Observed-step references are checked. They do not certify a causal rule or goal.
This module uses only the supplied public observation history.
"""
import copy
import json
from pathlib import Path

KINDS={'control','state','mechanics','goal','resource'}
STATUSES={'hypothesis','supported','contradicted'}
MAX_NOTES=10
MAX_BYTES=8000


def empty_store():
    return dict(revision=0,notes={})


def validate_store(value):
    value=json.loads(json.dumps(value,allow_nan=False))
    if not isinstance(value,dict) or set(value)!={'revision','notes'}:
        raise ValueError('Invalid study memory schema')
    if type(value['revision']) is not int or value['revision']<0 or not isinstance(value['notes'],dict):
        raise ValueError('Invalid study memory revision/notes')
    if len(value['notes'])>MAX_NOTES or len(json.dumps(value).encode())>MAX_BYTES:
        raise ValueError('Study memory exceeds its bounded capacity')
    for key,note in value['notes'].items():
        if not isinstance(key,str) or not 1<=len(key)<=32 or key.startswith('_'):
            raise ValueError('Use a short non-reserved note key')
        if not isinstance(note,dict) or set(note)!={'claim','kind','status','scope','level','evidence_steps','condition','last_step'}:
            raise ValueError('Invalid study note schema')
        if not isinstance(note['claim'],str) or not 1<=len(note['claim'])<=240:
            raise ValueError('Keep a claim within 240 characters')
        if note['kind'] not in KINDS or note['status'] not in STATUSES or note['scope'] not in ('game','level'):
            raise ValueError('Unknown study note kind/status/scope')
        if not isinstance(note['condition'],str) or len(note['condition'])>100:
            raise ValueError('Keep conditions within 100 characters')
        if type(note['level']) is not int or type(note['last_step']) is not int:
            raise ValueError('Invalid study observation scope')
        steps=note['evidence_steps']
        if not isinstance(steps,list) or len(steps)>6 or any(type(s) is not int or s<0 for s in steps):
            raise ValueError('Use at most six observed integer step references')
        if note['status']!='hypothesis' and not steps:
            raise ValueError('Supported/contradicted claims need observed-step references')
    return value


def load_store(path):
    try:
        return validate_store(json.loads(Path(path).read_text(encoding='utf-8')))
    except (OSError,ValueError,TypeError,KeyError):
        return empty_store()


def persist_store(path,value):
    value=validate_store(value)
    path=Path(path)
    previous=load_store(path)
    if value==previous:
        return value
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,sort_keys=True)+'\n',encoding='utf-8')
    temporary.replace(path)
    with path.with_suffix('.events.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(value,sort_keys=True)+'\n')
    return value


def render_panel(store,current_level,limit=1800):
    try:
        store=validate_store(store)
    except (ValueError,TypeError,KeyError):
        return ''
    notes=store['notes']
    if not notes:return ''
    lines=['\nWorking hypotheses (model-authored, not certified rules/goals):']
    ordered=sorted(notes.items(),key=lambda item:(item[1]['level']!=current_level,-item[1]['last_step']))
    for key,note in ordered:
        prior=note['level']!=current_level
        if prior and note['scope']=='level':continue
        status='prior-level; RECHECK' if prior else note['status']
        text=f"{key} [{note['kind']}; {status}; refs={note['evidence_steps']}]: {note['claim']}"
        if note['condition']:text+=' IF '+note['condition']
        if len('\n'.join(lines))+len(text)+1>limit:
            lines.append('Additional notes available via recall().')
            break
        lines.append(text)
    return '\n'.join(lines)[:limit] if len(lines)>1 else ''


def install(namespace,initial=None):
    store=validate_store(initial) if initial else empty_store()

    def recall():
        return copy.deepcopy(store)

    def remember(key,claim,kind='mechanics',status='hypothesis',evidence_steps=None,scope='level',condition=''):
        current=namespace.get('current_frame')
        if current is None:raise ValueError('No current observation for a study note')
        candidate=copy.deepcopy(store)
        if claim is None:
            candidate['notes'].pop(key,None)
        else:
            observed={current.step}
            for entry in namespace.get('history',[]):
                frame=getattr(entry,'frame',None)
                if frame is not None:observed.add(frame.step)
            steps=list(evidence_steps or [])
            if any(type(s) is not int or s not in observed for s in steps):
                raise ValueError('Evidence step not present in supplied observation history')
            candidate['notes'][key]=dict(claim=claim,kind=kind,status=status,scope=scope,
                level=current.level,evidence_steps=steps,condition=condition,last_step=current.step)
        candidate['revision']+=1
        validated=validate_store(candidate)
        store.clear();store.update(validated)
        return dict(revision=store['revision'],notes=len(store['notes']),status='model-authored')

    namespace.update(remember=remember,recall=recall)
    return recall
