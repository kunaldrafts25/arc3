"""Measure completed model calls and distinct visible tool results, read-only."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re


def profile(records):
    responses = prompt_tokens = cached_tokens = completion_tokens = cache_rows = 0
    seen_tools, errors, finishes = set(), [], Counter()
    action_groups, prompt_decreases = [], []
    previous_prompt = None
    for record in records:
        if record.get('event') != 'response':
            continue
        responses += 1
        usage = record.get('usage') or {}
        completion_tokens += usage.get('completion_tokens',0)
        action = record.get('action')
        if action is not None:
            if not action_groups or action_groups[-1]['action'] != action:
                action_groups.append(dict(action=action,responses=0,completion_tokens=0))
            action_groups[-1]['responses'] += 1
            action_groups[-1]['completion_tokens'] += usage.get('completion_tokens',0)
        prompt = usage.get('prompt_tokens')
        if prompt is not None:
            if previous_prompt is not None and previous_prompt-prompt >= 8192:
                prompt_decreases.append(dict(analysis_step=record.get('analysis_step'),
                                             action=action,before=previous_prompt,after=prompt))
            previous_prompt=prompt
        details = usage.get('prompt_tokens_details') or {}
        if 'cached_tokens' in details and usage.get('prompt_tokens',0)>0:
            prompt_tokens += usage['prompt_tokens']
            cached_tokens += details['cached_tokens']
            cache_rows += 1
        finishes[record.get('finish_reason','unknown')] += 1
        # Logs retain conversation history. Counting every tool message in
        # every response would repeatedly count the same failure.
        for message in record.get('messages',[]):
            identity = message.get('tool_call_id')
            if message.get('role') != 'tool' or not identity or identity in seen_tools:
                continue
            seen_tools.add(identity)
            content = message.get('content')
            if not isinstance(content,str):
                continue
            try:
                result = json.loads(content)
            except (ValueError,TypeError):
                continue
            if not isinstance(result,dict) or not result.get('error'):
                continue
            error = str(result['error'])
            matches = re.findall(r'(?m)^([A-Za-z_][A-Za-z_0-9]*(?:Error|Exception)):',error)
            kind = matches[-1] if matches else ('SyntaxError' if error.startswith('Python syntax error') else 'OtherToolError')
            errors.append(dict(tool_call_id=identity,kind=kind,
                               guard_stop=kind in ('StaleStateActionError','TerminalStateActionError'),
                               first_observed_analysis_step=record.get('analysis_step'),
                               message=error.splitlines()[-1][:300]))
    return dict(completed_responses=responses,completed_response_tokens=completion_tokens,
                cache_usage_rows=cache_rows,prompt_tokens_with_cache_usage=prompt_tokens,
                cached_prompt_tokens=cached_tokens,
                weighted_cache_fraction=cached_tokens/prompt_tokens if prompt_tokens else None,
                distinct_visible_tool_results=len(seen_tools),tool_errors=errors,
                ordinary_tool_errors=sum(not e['guard_stop'] for e in errors),
                observed_stale_state_guard_stops=sum(e['kind']=='StaleStateActionError' for e in errors),
                observed_terminal_state_guard_stops=sum(e['kind']=='TerminalStateActionError' for e in errors),
                longest_same_action_response_group=max(action_groups,key=lambda g:g['responses'],default=None),
                most_tokens_at_one_action=max(action_groups,key=lambda g:g['completion_tokens'],default=None),
                large_prompt_token_decreases=prompt_decreases,
                interpretation='Repeated action counters measure computation without a recorded game action; computation may be useful. Prompt decreases do not prove forgetting or establish a causal effect on score.',
                finish_reasons=dict(finishes))


def audit(directory):
    games = {}
    for path in sorted(directory.glob('*_requests.jsonl')):
        digest = sha256()
        def records():
            with path.open('rb') as stream:
                for line in stream:
                    digest.update(line)
                    if line.strip():
                        yield json.loads(line)
        result = profile(records())
        result['source_sha256'] = digest.hexdigest()
        games[path.name] = result
    if not games:
        raise FileNotFoundError('No completed model request logs are cached')
    result = dict(games=games,completed_responses=sum(g['completed_responses'] for g in games.values()),
                  completed_response_tokens=sum(g['completed_response_tokens'] for g in games.values()),
                  ordinary_tool_errors=sum(g['ordinary_tool_errors'] for g in games.values()),
                  observed_stale_state_guard_stops=sum(g['observed_stale_state_guard_stops'] for g in games.values()),
                  observed_terminal_state_guard_stops=sum(g['observed_terminal_state_guard_stops'] for g in games.values()),
                  boundary='Completed-response usage excludes unfinished generation. Tool results are deduplicated by call ID within each game; not every completed response necessarily exposes its final tool result. Cached public-game files may cover only a subset of a run.')
    (directory/'request-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2))
