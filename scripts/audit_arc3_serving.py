"""Audit saved public SGLang timing logs without launching any inference."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

PATTERN = re.compile(r'ReqTimeStats\(rid=([^,]+), input_len=(\d+), cached_input_len=(\d+), '
    r'output_len=(\d+),.*?queue_duration=([\d.]+)ms, initial_prefill_elapsed=([\d.]+)ms, '
    r'post_prefill_elapsed=([\d.]+)ms, forward_duration=([\d.]+)ms, entry_time=([\d.]+)')


def quantiles(values):
    values = sorted(values)
    if not values:
        return None
    return {name:values[round((len(values)-1)*q)] for name,q in [('p50',.5),('p90',.9),('p99',.99),('max',1)]}


def union_seconds(intervals):
    intervals = sorted(intervals)
    total = 0.0
    end = float('-inf')
    for start,stop in intervals:
        total += max(0.0,stop-max(start,end))
        end = max(end,stop)
    return total


def summarize(calls,begin,end):
    prompt = sum(c['input'] for c in calls)
    cached = sum(c['cached'] for c in calls)
    generated = sum(c['output'] for c in calls)
    long = [c for c in calls if c['input']>62000]
    return dict(completed_requests=len(calls),prompt_tokens=prompt,cached_tokens=cached,
        weighted_cache_fraction=cached/prompt if prompt else None,completed_response_tokens=generated,
        prompt_length_tokens=quantiles([c['input'] for c in calls]),
        response_length_tokens=quantiles([c['output'] for c in calls]),
        server_queue_ms=quantiles([c['queue_ms'] for c in calls]),
        initial_prefill_ms=quantiles([c['prefill_ms'] for c in calls]),
        long_prompt_requests=len(long),long_prompt_low_cache_requests=sum(c['cached']<10000 for c in long),
        completed_response_tokens_per_window_second=generated/(end-begin),
        # This is logged request-interval coverage, not measured GPU utilization.
        initial_prefill_interval_coverage_seconds=union_seconds([
            (max(begin,c['entry']+c['queue_ms']/1000),
             min(end,c['entry']+(c['queue_ms']+c['prefill_ms'])/1000))
            for c in calls if c['prefill_ms']>0 and c['entry']<end
            and c['entry']+(c['queue_ms']+c['prefill_ms'])/1000>begin]))


def audit(log_path,benchmark_path):
    benchmark = json.loads(benchmark_path.read_text(encoding='utf-8'))
    begin = datetime.fromisoformat(benchmark['start_time']).replace(tzinfo=timezone.utc).timestamp()
    end = max(datetime.fromisoformat(g['started_at']).replace(tzinfo=timezone.utc).timestamp()
              +g['final_wallclock_seconds'] for g in benchmark['game_runs'])
    calls = []
    total_timing_lines = 0
    parse_failures = 0
    running, queued, throughput, acceptance = [], [], [], []
    with log_path.open(encoding='utf-8') as stream:
        for line in stream:
            if 'ReqTimeStats(' in line:
                total_timing_lines += 1
                match = PATTERN.search(line)
                if not match:
                    parse_failures += 1
                    continue
                rid,prompt,cached,output,queue,prefill,post,forward,entry = match.groups()
                entry = float(entry)
                if not begin <= entry <= end:
                    continue
                calls.append(dict(id=rid,input=int(prompt),cached=int(cached),output=int(output),
                    queue_ms=float(queue),prefill_ms=float(prefill),post_ms=float(post),
                    forward_ms=float(forward),entry=entry))
            if 'Decode batch,' in line:
                for field,target in [('#running-req',running),('#queue-req',queued),
                                     ('gen throughput \\(token/s\\)',throughput),('accept len',acceptance)]:
                    match = re.search(field+r': ([\d.]+)',line)
                    if match:
                        target.append(float(match[1]))
    report = summarize(calls,begin,end)
    report.update(checked_at=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha256(log_path.read_bytes()).hexdigest(),
        benchmark_sha256=sha256(benchmark_path.read_bytes()).hexdigest(),
        timing_lines=total_timing_lines,unparsed_timing_lines=parse_failures,
        unique_request_ids=len({c['id'] for c in calls}),
        gameplay_window_seconds=end-begin,
        benchmark_generated_tokens=sum(sum(a['generated_tokens'] for a in g['history'])+g['final_generated_tokens'] for g in benchmark['game_runs']),
        decode_log_samples=len(running),decode_running_requests_sample_quantiles=quantiles(running),
        decode_server_queue_requests_sample_quantiles=quantiles(queued),
        decode_token_throughput_sample_quantiles=quantiles(throughput),
        speculative_accept_length_sample_quantiles=quantiles(acceptance),
        by_two_hour_entry_window=[dict(start_seconds=t,end_seconds=min(t+7200,end-begin),
            **summarize([c for c in calls if begin+t<=c['entry']<min(begin+t+7200,end)],
                        begin+t,min(begin+t+7200,end)))
            for t in range(0,int(end-begin),7200)],
        boundary='Saved public development log. Server queue excludes harness admission waiting. Decode sample quantiles are event-weighted, not time-weighted GPU utilization. Initial-prefill interval coverage uses logged queue/prefill elapsed fields and is not precise device busy time. Response tokens are assigned to request-entry windows, so generation can cross window boundaries. Completed-response totals can differ from benchmark action charges due to retries, cancellation or accounting; no unmeasured cause is assigned. Public/model configuration differs from other authors runs; not a matched throughput ablation or hidden failure diagnosis.')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path)
    parser.add_argument('benchmark',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = audit(args.log,args.benchmark)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='by_two_hour_entry_window'},indent=2))
