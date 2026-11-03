"""Host-owned prospective evidence over public observations only.

The caller supplies hypotheses and fixed feature queries, never the measured
outcome. No callbacks, action execution, hidden state or calibrated beliefs.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

try:
    from .prediction_ledger import PredictionLedger, frozen
except ImportError:  # Installed alongside the original inference host.
    from inference.agent.hydra_prediction_ledger import PredictionLedger, frozen


def frame_key(frame):
    return sha256(json.dumps(frame, sort_keys=True).encode()).hexdigest()


def measure(frame, features):
    """Exact ASCII pixels; a color's bounding box does not certify an object."""
    rows = frame['ascii'].splitlines()
    if not rows or not rows[0] or len(rows) > 128 or len(rows[0]) > 128:
        raise ValueError('Invalid observed grid')
    height, width = len(rows), len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError('Nonrectangular observed grid')
    if list(frame['shape']) != [height, width]:
        raise ValueError('Observation dimensions disagree')
    if not isinstance(features, dict) or not 1 <= len(features) <= 16:
        raise ValueError('Use 1..16 named fixed feature queries')
    observed = {}
    for name, query in features.items():
        if not isinstance(name, str) or not 1 <= len(name) <= 40:
            raise ValueError('Use short feature names')
        if not isinstance(query, list) or not query:
            raise ValueError('Use JSON-list feature queries')
        kind, *args = query
        if kind == 'cell' and len(args) == 2:
            row, col = args
            if any(type(v) is not int for v in args) or not (0 <= row < height and 0 <= col < width):
                raise ValueError('Cell outside observed grid')
            observed[name] = rows[row][col]
        elif kind in ('count', 'bbox') and len(args) in (1, 5):
            color = args[0]
            if not isinstance(color, str) or len(color) != 1:
                raise ValueError('Color must be one observed ASCII letter')
            bounds = args[1:] if len(args) == 5 else [0, height, 0, width]
            if any(type(v) is not int for v in bounds):
                raise ValueError('Use integer bounds')
            r0, r1, c0, c1 = bounds
            if not (0 <= r0 < r1 <= height and 0 <= c0 < c1 <= width):
                raise ValueError('Feature bounds outside observed grid')
            points = [(r, c) for r in range(r0, r1) for c in range(c0, c1) if rows[r][c] == color]
            if kind == 'count':
                observed[name] = len(points)
            else:
                observed[name] = ([min(p[0] for p in points), max(p[0] for p in points)+1,
                                   min(p[1] for p in points), max(p[1] for p in points)+1]
                                  if points else None)
        else:
            raise ValueError('Queries: cell,row,col; count/color or bbox/color with optional exclusive bounds')
    return observed


def canonical_action(value):
    if not isinstance(value, dict) or 'action' not in value:
        raise ValueError('Use a normalized action dictionary')
    command = value['action']
    simple = {'UP', 'DOWN', 'LEFT', 'RIGHT', 'SPACE', 'RESET', 'UNDO'}
    if command == 'MOUSE':
        if set(value) != {'action', 'row', 'col'} or any(type(value[k]) is not int or not 0 <= value[k] < 128 for k in ('row', 'col')):
            raise ValueError('MOUSE needs raw integer row and col')
    elif command not in simple or set(value) != {'action'}:
        raise ValueError('Unsupported normalized action')
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


class PredictionSession:
    """One durable game session, with separate level-scoped hypothesis versions."""
    def __init__(self, path, state_provider):
        self.path = Path(path)
        self.state_provider = state_provider
        self.disabled_reason = None
        self.data = dict(version=1, revision=0, ledger=None, features={}, question='',
                         probes={}, frozen_frame=None, in_flight=False, last_outcome=None,
                         invalidated=False, start_step=None)
        try:
            if self.path.exists():
                value = json.loads(self.path.read_text(encoding='utf-8'))
                if (not isinstance(value, dict) or set(value) != set(self.data)
                        or value['version'] != 1 or len(json.dumps(value)) > 180000):
                    raise ValueError('Invalid prediction store')
                self.data = value
                if self.data['in_flight']:
                    self._cancel('interrupted action; outcome not certified')
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self._disable('prediction store unavailable', exc)

    def _disable(self, reason, error):
        self.disabled_reason = reason+': '+type(error).__name__
        self.data.update(in_flight=False, frozen_frame=None, probes={}, invalidated=True,
                         last_outcome=dict(checked=False,reason=self.disabled_reason))

    def _event(self, event, **fields):
        record = dict(format=2,event=event,revision=self.data['revision'],**fields)
        with self.path.with_suffix('.events.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(record,sort_keys=True,allow_nan=False)+'\n')

    def _frame(self):
        return frozen(self.state_provider()['current_frame'])

    def _ledger(self):
        value = self.data['ledger']
        if value is None:
            raise ValueError('Call prediction_start first')
        ledger = PredictionLedger(list(value['models']), max_evidence=16)
        ledger.__dict__.update(deepcopy(value))
        return ledger

    def _save(self, ledger=None):
        if ledger is not None:
            self.data['ledger'] = frozen(ledger.__dict__)
        self.data['revision'] += 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.data, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8')
        temporary.replace(self.path)

    def _cancel(self, reason):
        ledger = self._ledger()
        pending = deepcopy(ledger.pending)
        if ledger.pending:
            ledger.discard(ledger.pending['ticket'])
        self.data.update(in_flight=False, frozen_frame=None, probes={},
                         last_outcome=dict(checked=False, reason=reason))
        self._save(ledger)
        self._event('cancel',reason=reason,pending=pending)

    def status(self):
        if self.disabled_reason:
            return dict(disabled=True,reason=self.disabled_reason,models={},pending=None,
                        last_outcome=dict(checked=False,reason=self.disabled_reason),
                        needs_new_hypotheses=True,scope_current=False)
        ledger = self._ledger()
        frame = self._frame()
        return dict(question=self.data['question'], level=ledger.level,
                    current_level=frame['level'], scope_current=(ledger.level == frame['level']
                        and not self.data['invalidated'] and frame['step'] >= self.data['start_step']),
                    models=deepcopy(ledger.models), pending=deepcopy(ledger.pending),
                    last_outcome=deepcopy(self.data['last_outcome']),
                    evidence=deepcopy(ledger.evidence[-4:]),
                    needs_new_hypotheses=not bool(ledger.active()))

    def rpc(self, request):
        snapshot = deepcopy(self.data)
        try:
            operation = request.get('operation') if isinstance(request,dict) else None
            if self.disabled_reason and operation != 'start':
                raise ValueError(self.disabled_reason+'; use prediction_start to retry explicitly')
            result = self._rpc(request)
            if operation == 'start':
                self.disabled_reason = None
            return result
        except OSError as exc:
            self.data = snapshot
            self._disable('prediction persistence unavailable', exc)
            raise ValueError(self.disabled_reason) from exc
        except Exception:
            self.data = snapshot
            raise

    def _rpc(self, request):
        request = frozen(request)
        if not isinstance(request, dict) or len(json.dumps(request)) > 16000:
            raise ValueError('Bound prediction requests to 16000 characters')
        operation = request.get('operation')
        if operation == 'start':
            if set(request) != {'operation', 'models', 'features', 'question'}:
                raise ValueError('Unexpected start fields')
            if not isinstance(request['question'], str) or len(request['question']) > 240:
                raise ValueError('Use a question within 240 characters')
            if not isinstance(request['models'], list) or len(request['models']) > 8:
                raise ValueError('Use 1..8 hypothesis version names')
            ledger = PredictionLedger(request['models'], max_evidence=16)
            frame = self._frame()
            observed = measure(frame, request['features'])
            ledger.level = frame['level']
            # Starting a new version is explicit; prior evidence is retained in events.
            if self.data['ledger'] is not None:
                self._event('superseded',store=self.data)
            self.data.update(features=request['features'], question=request['question'],
                             probes={}, frozen_frame=None, in_flight=False, last_outcome=None,
                             invalidated=False, start_step=frame['step'])
            self._save(ledger)
            self._event('start',models=request['models'],features=request['features'],
                        question=request['question'],step=frame['step'],level=frame['level'],observed=observed)
            return dict(level=frame['level'], step=frame['step'], observed=observed)
        if operation == 'status' and set(request) == {'operation'}:
            return self.status()
        if operation == 'discard' and set(request) == {'operation'}:
            self._cancel('forecast explicitly discarded')
            return self.status()
        if operation != 'forecast' or set(request) != {'operation', 'probes'}:
            raise ValueError('Unknown prediction request')
        ledger = self._ledger()
        frame = self._frame()
        if self.data['invalidated'] or frame['step'] < self.data['start_step']:
            raise ValueError('Start fresh hypotheses after a reset or observation restart')
        measure(frame, self.data['features'])
        probes = request['probes']
        if not isinstance(probes, dict) or not 1 <= len(probes) <= 16:
            raise ValueError('Forecast 1..16 named probes')
        actions, forecasts, costs = {}, {}, {}
        for name, probe in probes.items():
            if not isinstance(name,str) or not 1 <= len(name) <= 40:
                raise ValueError('Use probe names within 40 characters')
            if not isinstance(probe, dict) or set(probe) - {'action', 'predictions', 'cost'}:
                raise ValueError('Probe contains unsupported fields')
            action = canonical_action(probe['action'])
            if action in actions.values():
                raise ValueError('Duplicate action forecasts are ambiguous')
            predictions = probe['predictions']
            if not isinstance(predictions, dict):
                raise ValueError('Use per-hypothesis predictions')
            for values in predictions.values():
                if values is not None and (not isinstance(values, dict) or set(values) - self.data['features'].keys()):
                    raise ValueError('Predict only the declared measured features, or None')
            actions[name] = action
            forecasts[name] = predictions
            costs[name] = probe.get('cost', 1)
        result = ledger.commit(step=frame['step'], level=frame['level'], forecasts=forecasts, costs=costs)
        self.data.update(probes=actions, frozen_frame=frame_key(frame))
        self._save(ledger)  # Durable before any future action can execute.
        self._event('forecast',pending=ledger.pending,probes=probes,features=self.data['features'],
                    frame_sha256=self.data['frozen_frame'])
        return result

    def wrap_action(self, handler):
        """Bookkeeping must not lose an executed action or retry the handler."""
        def wrapped(actions, **kwargs):
            called = False
            returned = False
            reply = None
            original_error = None
            def tracked_handler(*args, **fields):
                nonlocal called, returned, reply, original_error
                called = True
                try:
                    reply = handler(*args, **fields)
                except Exception as exc:
                    original_error = exc
                    raise
                returned = True
                return reply
            try:
                if self.disabled_reason:
                    reply = tracked_handler(actions, **kwargs)
                else:
                    reply = self._tracked_action(tracked_handler)(actions, **kwargs)
            except Exception as exc:
                if called and not returned:
                    raise original_error  # Preserve even if cancellation logging also failed.
                self._disable('prediction bookkeeping unavailable; action unverified', exc)
                if not called:
                    reply = tracked_handler(actions, **kwargs)
            if self.disabled_reason:
                reply['action_result']['hydra_prediction_warning'] = self.disabled_reason
            return reply
        return wrapped

    def _tracked_action(self, handler):
        def wrapped(actions, **kwargs):
            ledger = self._ledger() if self.data['ledger'] is not None else None
            label = None
            if ledger is not None and ledger.pending is not None:
                if len(actions) == 1:
                    try:
                        target = canonical_action(actions[0])
                        label = next((k for k, v in self.data['probes'].items() if v == target), None)
                    except ValueError:
                        pass
                if label is None:
                    self._cancel('next action or batch was not a frozen single probe')
                elif frame_key(self._frame()) != self.data['frozen_frame']:
                    self._cancel('observation changed after forecast')
                    label = None
                else:
                    self.data['in_flight'] = True
                    self._save()
                    self._event('dispatch',pending=ledger.pending,probe=label,action=actions[0])
            try:
                reply = handler(actions, **kwargs)  # Exactly the original one call.
            except Exception:
                if label is not None:
                    self._cancel('action handler failed; outcome not certified')
                raise
            if label is not None:
                outcome = reply.get('action_result') or {}
                frame = (reply.get('state') or {}).get('current_frame')
                if (not outcome.get('executed') or frame is None or actions[0]['action'] == 'RESET'
                        or frame['level'] != ledger.pending['level']
                        or any(outcome.get(k) for k in ('level_completed', 'game_over', 'done', 'run_complete'))):
                    self._cancel('refused action, reset, or terminal boundary')
                else:
                    try:
                        result = ledger.resolve(ledger.pending['ticket'], action=label,
                                                step=frame['step'], level=frame['level'],
                                                observed=measure(frame, self.data['features']))
                    except (ValueError, KeyError, TypeError):
                        self._cancel('nonconsecutive or unavailable observation; outcome not certified')
                    else:
                        self.data.update(in_flight=False, frozen_frame=None, probes={}, last_outcome=result)
                        self._save(ledger)
                        self._event('resolve',question=self.data['question'],level=frame['level'],
                                    step=frame['step'],outcome=result,evidence=ledger.evidence[-1],
                                    frame_sha256=frame_key(frame))
            if ledger is not None and (any(a.get('action') == 'RESET' for a in actions)
                    or any((reply.get('action_result') or {}).get(k) for k in ('level_completed', 'game_over', 'done', 'run_complete'))):
                self.data['invalidated'] = True
                self._save()
            return reply
        return wrapped


def render_panel(path, current_level, limit=1400):
    path = Path(path)
    if not path.exists():
        return ''
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        ledger = data['ledger']
        if ledger is None or ledger['level'] != current_level or data['invalidated']:
            return ''
        panel = dict(question=data['question'], models=ledger['models'], last_outcome=data['last_outcome'])
        if ledger['pending'] is not None:
            panel['pending_forecast'] = dict(step=ledger['pending']['step'],probes=data['probes'])
        return '\nFrozen prediction evidence (scoped measurements, not certified rules/goals):\n' + json.dumps(panel, sort_keys=True)[:limit]
    except (OSError, ValueError, KeyError, TypeError):
        return ''
