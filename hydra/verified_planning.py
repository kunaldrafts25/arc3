"""Prediction-checked action execution, embedded in the existing Python sandbox.

This checks a model's observable predictions; it is not a proof of its mechanics
or a security boundary against adversarial Python introspection.
"""
import copy
import json
import re


def _value(value):
    return json.loads(json.dumps(value, allow_nan=False, sort_keys=True))


def _difference(expected, observed, path=()):
    if type(expected) is not type(observed):
        return dict(path=list(path), expected=repr(expected)[:160], observed=repr(observed)[:160])
    if isinstance(expected, dict):
        if expected.keys() != observed.keys():
            return dict(path=list(path), expected_keys=sorted(expected), observed_keys=sorted(observed))
        pairs=((key, expected[key], observed[key]) for key in sorted(expected))
    elif isinstance(expected, list):
        if len(expected) != len(observed):
            return dict(path=list(path), expected_length=len(expected), observed_length=len(observed))
        pairs=((i, a, b) for i, (a, b) in enumerate(zip(expected, observed)))
    else:
        return None if expected == observed else dict(path=list(path), expected=expected, observed=observed)
    for key, a, b in pairs:
        difference=_difference(a, b, path+(key,))
        if difference is not None:
            return difference
    return None


def _historical_action(text):
    text=str(text).strip().upper()
    mouse=re.fullmatch(r'MOUSE\(ROW=(\d+),\s*COL=(\d+)\)', text)
    if mouse:
        return dict(action='MOUSE', row=int(mouse[1]), col=int(mouse[2]))
    if re.fullmatch(r'[A-Z][A-Z0-9_]*', text):
        return dict(action=text)
    raise ValueError('Unrecognized historical action: '+text[:100])


def install(namespace, normalize, enforce_probes=True):
    """Expose helpers in a single tool call; host history remains authoritative."""
    raw_action=namespace['action']
    checking=[False]
    probes=[0]
    events=[]

    def emit(kind, report):
        if len(events)<128:
            events.append(dict(event=kind,report=_value(report)))
        print('HYDRA_'+kind.upper(),json.dumps(report,sort_keys=True))

    def frame():
        current=namespace.get('current_frame')
        if current is None:
            raise ValueError('No current observation')
        return current

    def evaluate(predict, encode, grid, action):
        if checking[0]:
            raise RuntimeError('Nested model evaluation is not supported')
        checking[0]=True
        try:
            state=_value(encode(copy.deepcopy(grid))) if encode else _value(grid)
            predicted=predict(copy.deepcopy(state), copy.deepcopy(action))
            return None if predicted is None else _value(predicted)
        finally:
            checking[0]=False

    def observed(encode, grid):
        checking[0]=True
        try:
            return _value(encode(copy.deepcopy(grid))) if encode else _value(grid)
        finally:
            checking[0]=False

    def verify_model(predict, encode=None, max_checks=512):
        if checking[0]:
            raise RuntimeError('Models cannot call the verifier recursively')
        if type(max_checks) is not int or not 1 <= max_checks <= 4096:
            raise ValueError('max_checks must be between 1 and 4096')
        current=frame()
        eligible=[]
        excluded=0
        for transition in namespace.get('transitions',[]):
            before, after=transition.before_frame, transition.after_frame
            if (before is None or after is None or before.level != current.level
                    or after.level != current.level or transition.result.get('automatic')
                    or str(transition.action).upper()=='RESET'):
                excluded+=1
                continue
            eligible.append(transition)
        report=dict(verified=False, scope='abstract-state' if encode else 'full-grid',
                    eligible=len(eligible), checked=0, abstained=0, excluded=excluded,
                    truncated=len(eligible)>max_checks, encoded_changes=0,
                    counterexample=None, error=None)
        for transition in eligible[:max_checks]:
            try:
                action=_historical_action(transition.action)
                prediction=evaluate(predict, encode, transition.before_frame._grid, action)
                if prediction is None:
                    report['abstained']+=1
                    continue
                report['checked']+=1
                target=observed(encode, transition.after_frame._grid)
                if encode and observed(encode, transition.before_frame._grid) != target:
                    report['encoded_changes']+=1
                difference=_difference(prediction, target)
                if difference is not None:
                    report['counterexample']=dict(before_step=transition.before_frame.step,
                        after_step=transition.after_frame.step, action=action, difference=difference)
                    break
            except Exception as error:
                report['error']=type(error).__name__+': '+str(error)[:240]
                break
        if encode and report['checked'] and not report['encoded_changes'] and not report['error']:
            report['error']='Representation has no observed state changes; use a richer encode or gather evidence'
        report['verified']=bool(report['checked'] and not report['abstained']
            and not report['truncated'] and not report['counterexample'] and not report['error'])
        emit('verify',report)
        return report

    def action(actions):
        if checking[0]:
            raise RuntimeError('Prediction and encoding functions cannot spend real actions')
        commands=normalize(actions)
        if not enforce_probes:
            # Preserve the original host's batching and guards. Prediction
            # callbacks still cannot spend actions, and execute_plan is checked.
            return raw_action(commands)
        if len(commands)!=1 or probes[0]>=1:
            raise RuntimeError('One exploratory action per tool call. Use execute_plan(actions, predict, encode=None) for checked batches.')
        probes[0]+=1
        result=raw_action(commands)
        emit('probe',dict(action=commands[0],executed=bool(result.get('executed'))))
        return result

    def execute_plan(actions, predict, encode=None, max_steps=12, max_checks=512):
        if checking[0]:
            raise RuntimeError('Prediction and encoding functions cannot execute plans')
        if type(max_steps) is not int or not 1 <= max_steps <= 16:
            raise ValueError('max_steps must be between 1 and 16')
        commands=normalize(actions)
        report=verify_model(predict, encode, max_checks)
        result=dict(executed=0, planned=len(commands), stop_reason='unverified_model', verification=report)
        if not report['verified']:
            emit('plan',result)
            return result
        for command in commands[:max_steps]:
            before=frame()
            prediction=evaluate(predict, encode, before._grid, command)
            if prediction is None:
                result['stop_reason']='unknown_prediction'
                break
            outcome=raw_action([command])
            # A raw single action can be refused by the existing host guards.
            if not outcome.get('executed'):
                result['stop_reason']='host_refusal'
                break
            result['executed']+=1
            if any(outcome.get(flag) for flag in ('level_completed','game_over','done','run_complete')):
                result['stop_reason']='terminal_or_level_boundary'
                break
            after=frame()
            if after.level != before.level:
                result['stop_reason']='level_boundary'
                break
            difference=_difference(prediction, observed(encode, after._grid))
            if difference is not None:
                result.update(stop_reason='prediction_mismatch', counterexample=dict(
                    action=command, before_step=before.step, after_step=after.step, difference=difference))
                break
            if outcome.get('gameplay_changed') is False:
                result['stop_reason']='no_gameplay_change'
                break
        else:
            result['stop_reason']='complete' if len(commands)<=max_steps else 'step_cap'
        emit('plan',result)
        return result

    namespace.update(action=action, verify_model=verify_model, execute_plan=execute_plan)
    return events
