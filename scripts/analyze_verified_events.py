"""Summarize mechanical verifier events from completed sandbox calls."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


def analyze(directory):
    files=sorted(Path(directory).rglob('*.hydra-events.jsonl'))
    if not files:
        raise FileNotFoundError('No mechanical verification events downloaded; adoption is unverified')
    counts=Counter()
    sources={}
    for path in files:
        sources[path.relative_to(directory).as_posix()]=sha256(path.read_bytes()).hexdigest()
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            event=json.loads(line)
            kind, report=event['event'],event['report']
            if kind not in ('verify','plan','probe') or not isinstance(report,dict):
                raise ValueError('Unknown verifier event schema')
            counts[kind+'_events']+=1
            if kind=='verify':
                counts['passed_replays']+=bool(report['verified'])
                counts['replayed_predictions']+=report['checked']
                counts['abstentions']+=report['abstained']
                counts['replay_counterexamples']+=bool(report['counterexample'])
                counts['replay_errors']+=bool(report['error'])
                counts['abstract_replays']+=report['scope']=='abstract-state'
            elif kind=='plan':
                counts['executed_plan_actions']+=report['executed']
                counts['plan_stop:'+report['stop_reason']]+=1
            else:
                counts['executed_probe_actions']+=bool(report['executed'])
    result=dict(files=sources,counts=dict(counts),boundary=(
        'Mechanical events from completed sandbox calls only; interrupted calls may be absent. '
        'Replay counts include repeated checks of the same history. Abstract-state checks are '
        'not full-grid correctness. Adoption does not establish score improvement.'))
    (Path(directory)/'verified-events-analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    print(json.dumps(analyze(args.directory),indent=2))
