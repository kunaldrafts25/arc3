"""Finite deterministic hypothesis experiments over measured JSON features.

Forecasts are frozen before an observation is accepted. This is a research
component, not a game solver or a calibrated Bayesian posterior. Candidate
generation, feature grounding, goal inference and host integration are external.
"""
from collections import Counter
from copy import deepcopy
import json
import math


def frozen(value):
    return json.loads(json.dumps(value, allow_nan=False, sort_keys=True))


def rank_probes(forecasts, weights, costs=None):
    """Rank coverage-weighted deterministic disagreement per declared cost.

Only common predicted feature keys distinguish outcomes. Abstention reduces
coverage; an unknown prediction is never treated as an extra observed outcome.
This local heuristic does not measure task progress, risk or long-term value.
"""
    total = sum(weights.values())
    ranked = []
    for action, predictions in forecasts.items():
        known = {k: p for k, p in predictions.items() if k in weights and p}
        keys = set.intersection(*(set(p) for p in known.values())) if known else set()
        groups = Counter()
        if keys:
            for key, prediction in known.items():
                signature = json.dumps({k: prediction[k] for k in sorted(keys)}, sort_keys=True, allow_nan=False)
                groups[signature] += weights[key]
        mass = sum(groups.values())
        entropy = -sum(w / mass * math.log2(w / mass) for w in groups.values()) if mass else 0.0
        coverage = mass / total if total else 0.0
        cost = float((costs or {}).get(action, 1))
        if not math.isfinite(cost) or cost <= 0:
            raise ValueError('Probe costs must be positive and finite')
        ranked.append(dict(action=action, disagreement_bits=entropy, coverage=coverage,
                           common_features=sorted(keys), cost=cost, score=entropy * coverage / cost))
    return sorted(ranked, key=lambda row: (-row['score'], row['cost'], row['action']))


class PredictionLedger:
    def __init__(self, models, max_evidence=128):
        if (not isinstance(models, (list, tuple)) or not 1 <= len(models) <= 32
                or any(not isinstance(name, str) or not 1 <= len(name) <= 80 for name in models)
                or len(set(models)) != len(models)):
            raise ValueError('Use 1..32 unique hypothesis version names')
        if type(max_evidence) is not int or not 1 <= max_evidence <= 1024:
            raise ValueError('Evidence capacity must be 1..1024')
        self.models = {name: dict(status='untested', consistent=0, partial=0, abstained=0)
                       for name in models}
        self.evidence = []
        self.evidence_dropped = 0
        self.max_evidence = max_evidence
        self.pending = None
        self.sequence = 0
        self.level = None
        self.last_step = None

    def active(self):
        return {k: 1.0 for k, v in self.models.items() if v['status'] != 'contradicted'}

    def commit(self, *, step, level, forecasts, costs=None):
        if self.pending is not None:
            raise ValueError('Resolve or discard the pending forecast first')
        if type(step) is not int or step < 0 or type(level) is not int or level < 1:
            raise ValueError('Use an observed nonnegative step and positive level')
        if self.level is not None and level != self.level:
            raise ValueError('Start a fresh level-scoped ledger and recheck transferred hypotheses')
        if self.last_step is not None and step < self.last_step:
            raise ValueError('Observation steps went backwards; start a fresh ledger')
        snapshot = frozen(forecasts)
        if not isinstance(snapshot, dict) or not 1 <= len(snapshot) <= 64:
            raise ValueError('Forecast 1..64 candidate actions')
        if len(json.dumps(snapshot)) > 64000:
            raise ValueError('Forecast payload exceeds its bounded capacity')
        for action, predictions in snapshot.items():
            if not isinstance(action, str) or not isinstance(predictions, dict):
                raise ValueError('Use named actions and per-hypothesis predictions')
            for name, prediction in predictions.items():
                if name not in self.models or (prediction is not None and
                                              (not isinstance(prediction, dict) or not prediction)):
                    raise ValueError('Use known models and nonempty feature maps, or None for unknown')
        rankings = rank_probes(snapshot, self.active(), costs)
        self.level = level
        self.sequence += 1
        self.pending = dict(ticket=self.sequence, step=step, level=level, forecasts=snapshot)
        informative = next((row['action'] for row in rankings if row['score'] > 0), None)
        return dict(ticket=self.sequence, suggested_probe=informative, rankings=rankings,
                    needs_new_hypotheses=not bool(self.active()))

    def discard(self, ticket):
        if self.pending is None or self.pending['ticket'] != ticket:
            raise ValueError('Unknown or consumed forecast ticket')
        self.pending = None

    def resolve(self, ticket, *, action, step, level, observed):
        pending = self.pending
        if pending is None or pending['ticket'] != ticket:
            raise ValueError('Unknown or consumed forecast ticket')
        if action not in pending['forecasts']:
            raise ValueError('Action was not forecast before the observation')
        if type(step) is not int or step != pending['step'] + 1:
            raise ValueError('Resolve exactly the next real action, without skipped steps')
        if type(level) is not int or level < 1:
            raise ValueError('Use a positive observed level')
        observation = frozen(observed)
        if not isinstance(observation, dict):
            raise ValueError('Observation must be a measured feature map')
        self.pending = None
        self.last_step = step
        # Cross-level dynamics are not evidence against a level-scoped model.
        if level != pending['level']:
            return dict(checked=False, reason='level boundary', needs_new_hypotheses=not bool(self.active()))
        verdicts = {}
        for name in self.active():
            state = self.models[name]
            prediction = pending['forecasts'][action].get(name)
            if prediction is None:
                state['abstained'] += 1
                verdicts[name] = dict(verdict='unknown')
                continue
            common = prediction.keys() & observation.keys()
            differences = {key: dict(expected=prediction[key], observed=observation[key])
                           for key in sorted(common)
                           if json.dumps(prediction[key], sort_keys=True) != json.dumps(observation[key], sort_keys=True)}
            if differences:
                state['status'] = 'contradicted'
                state['counterexample'] = dict(before_step=pending['step'], after_step=step,
                                               level=level, action=action, differences=deepcopy(differences))
                verdicts[name] = dict(verdict='contradicted', differences=differences)
            elif common == prediction.keys():
                state['consistent'] += 1
                state['status'] = 'consistent_on_observed_predictions'
                verdicts[name] = dict(verdict='consistent', checked_features=sorted(common))
            else:
                state['partial'] += 1
                verdicts[name] = dict(verdict='insufficient_observation', checked_features=sorted(common))
        record = dict(before_step=pending['step'], after_step=step, level=level, action=action,
                      observed=observation, verdicts=verdicts)
        self.evidence.append(record)
        if len(self.evidence) > self.max_evidence:
            self.evidence.pop(0)
            self.evidence_dropped += 1
        return dict(checked=True, verdicts=deepcopy(verdicts), active=list(self.active()),
                    needs_new_hypotheses=not bool(self.active()))
