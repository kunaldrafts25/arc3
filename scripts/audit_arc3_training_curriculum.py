"""CPU inspection of pinned public curriculum samples; does not certify labels or train."""
from collections import Counter, defaultdict
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'reports/research/arc3-training-selection-20261101'
IMAGES = ('support_0_before', 'support_0_after', 'support_1_before',
          'support_1_after', 'query_before')
VISIBLE = (*IMAGES, 'support_0_action_json', 'support_1_action_json',
           'query_action_json', 'candidate_calls_json', 'probe_options_json')


def visible_digest(row):
    # Generator family, hidden parameters, split, seeds, identities and target
    # are deliberately excluded. Hash decoded pixels, not PNG compression.
    digest = sha256()
    for key in VISIBLE:
        if key not in row:
            continue
        value = row[key]
        if key in IMAGES:
            picture = Image.open(BytesIO(value['bytes'])).convert('RGB')
            payload = str(picture.size).encode() + picture.tobytes()
        else:
            payload = json.dumps(json.loads(value), sort_keys=True).encode()
        digest.update(key.encode() + len(payload).to_bytes(8, 'little') + payload)
    return digest.hexdigest()


def main():
    manifest = json.loads((DIRECTORY/'curriculum-sample/manifest.json').read_text())
    reports, identities, visible_sets = {}, {}, {}
    for entry in manifest['files']:
        name = entry['path']
        path = DIRECTORY/'curriculum-sample'/name
        if sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Pinned source changed: '+name)
        if not name.endswith('.parquet'):
            continue
        rows = pq.read_table(path).to_pylist()
        target_key = 'target_decision_json' if 'ambiguity/' in name else 'target_call_json'
        groups = defaultdict(set)
        counts = Counter()
        ids = Counter()
        failures = []
        for index, row in enumerate(rows):
            counts[row['family']] += 1
            ids[row['identity_id']] += 1
            label = json.dumps(json.loads(row[target_key]), sort_keys=True)
            groups[visible_digest(row)].add(label)
            for key in IMAGES:
                with Image.open(BytesIO(row[key]['bytes'])) as picture:
                    if picture.size != (256, 256):
                        failures.append([index, key, 'unexpected image size'])
            for key in ('support_0_action_json', 'support_1_action_json', 'query_action_json'):
                if key not in row:
                    continue
                action = json.loads(row[key])
                if action['action'] == 'ACTION6' and not all(
                        isinstance(action.get(axis), int) and 0 <= action[axis] < 64
                        for axis in ('x', 'y')):
                    failures.append([index, key, 'invalid click'])
        identities[name] = set(ids)
        visible_sets[name] = set(groups)
        reports[name] = dict(rows=len(rows), families=dict(counts),
            structural_identities=len(ids), rows_per_identity=dict(Counter(ids.values())),
            unique_visible_prompts=len(groups),
            visible_prompts_with_conflicting_exact_targets=sum(len(v)>1 for v in groups.values()),
            decode_or_coordinate_failures=failures,
            model_visible_fields=[key for key in VISIBLE if key in rows[0]],
            excluded_metadata_fields=[key for key in rows[0] if key not in VISIBLE and key != target_key],
            target=target_key)
    train, validation = 'data/train-00000.parquet', 'data/validation-00000.parquet'
    report = dict(revision=manifest['revision'], shards=reports,
        sampled_stateful_train_validation_identity_overlap=len(identities[train]&identities[validation]),
        sampled_stateful_train_validation_visible_prompt_overlap=len(visible_sets[train]&visible_sets[validation]),
        scope='Three sampled shards only, not a full dataset split or contamination audit.',
        train_ready=False,
        blockers=[
            'Public repository file listing contains no Python transition registry/verifier; exact labels have not been re-executed.',
            'Targets call a supplied synthetic function library that is absent from our deployed agent. Do not teach unavailable tools.',
            'Forty visual skins per identity require grouped splits and sampling, not random row splits.',
            'Transition induction and selecting among supplied hypotheses do not establish goal discovery or real-game transfer.',
            'Do not put family, parameter_json, structural_seed, identity or targets in the model input.',
        ])
    (DIRECTORY/'curriculum-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
