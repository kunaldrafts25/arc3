"""Extract causal, outcome-filtered teacher replies; never execute teacher code."""
import ast
import argparse
import base64
from collections import Counter,defaultdict
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import sys

from jinja2.sandbox import ImmutableSandboxedEnvironment
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'reports/research/arc3-training-selection-20261101'
OUT=ROOT/'reports/arc3/qwen27-training-pilot'


def stable(value):return json.dumps(value,sort_keys=True,separators=(',',':'))


def request_level(action,boundaries):
    # The logged request action is the next action's ONE-based number. In the
    # actual ft09 recording, action 13 finishes level 2 (boundaries 4,13,27);
    # action 14 is the first request on level 3.
    return next((i for i,end in enumerate(boundaries) if action<=end),None)


def observed_level(messages):
    text=[]
    for message in messages:
        if message['role']!='user':continue
        content=message.get('content')
        if isinstance(content,str):text.append(content)
        elif isinstance(content,list):text.extend(p.get('text','') for p in content if isinstance(p,dict))
    levels=re.findall(r'Current state: step \d+, level (\d+)\.', '\n'.join(text))
    return int(levels[-1]) if levels else None


def paired_replies(path,counts):
    """Only recover a reply when the next recorded request retains the exact input."""
    previous=response=None
    with path.open(encoding='utf-8') as stream:
        for line_number,line in enumerate(stream,1):
            current=json.loads(line)
            if current.get('event')=='response':
                response=current
                continue
            if current.get('event')!='request':continue
            if previous is not None:
                counts['adjacent_request_pairs']+=1
                messages=previous['messages'];following=current['messages']
                if (not response or response.get('messages')!=messages
                        or response.get('analysis_step')!=previous.get('analysis_step')
                        or response.get('request_index_within_turn')!=previous.get('request_index_within_turn')):
                    counts['missing_matching_response']+=1
                elif following[:len(messages)]!=messages:
                    counts['context_changed_or_pruned']+=1
                elif len(following)<=len(messages) or following[len(messages)].get('role')!='assistant':
                    counts['missing_immediate_assistant']+=1
                else:
                    assistant=following[len(messages)]
                    calls=assistant.get('tool_calls') or []
                    ids={c.get('id') for c in calls}
                    results=[m for m in following[len(messages)+1:] if m.get('role')=='tool' and m.get('tool_call_id') in ids]
                    if response.get('finish_reason')!='tool_calls' or not calls or len(results)!=len(calls):
                        counts['missing_complete_tool_reply']+=1
                    else:
                        yield dict(request=previous,response=response,assistant=assistant,results=results,
                            next_action=current.get('action'),source_reply_visible_at_line=line_number)
            previous=current;response=None


def normalize(messages):
    messages=deepcopy(messages)
    for message in messages:
        for call in message.get('tool_calls') or []:
            function=call.get('function',call)
            if isinstance(function.get('arguments'),str):function['arguments']=json.loads(function['arguments'])
    return messages


def python_reply(assistant,results):
    for call in assistant.get('tool_calls') or []:
        function=call.get('function',call)
        if function.get('name')!='python':return False
        arguments=function['arguments']
        if isinstance(arguments,str):arguments=json.loads(arguments)
        if set(arguments)!={'code'} or not isinstance(arguments['code'],str):return False
        try:ast.parse(arguments['code'])
        except SyntaxError:return False
    for result in results:
        content=result.get('content','')
        try:parsed=json.loads(content)
        except (ValueError,TypeError):parsed=None
        if isinstance(parsed,dict) and parsed.get('error'):return False
        if isinstance(content,str) and content.lstrip().startswith('Traceback ('):return False
    return True


def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context-tokens',type=int,choices=(16384,32768),default=16384)
    args=parser.parse_args()
    if args.context_tokens!=16384:OUT=OUT/('context-'+str(args.context_tokens))
    sys.path.insert(0,str(ROOT/'.tmp/arc3-tokenizer-deps'))
    from tokenizers import Tokenizer
    tokenroot=DIRECTORY/'target-tokenizer'
    manifest=json.loads((tokenroot/'manifest.json').read_text())
    for record in manifest['files']:
        if sha256((tokenroot/record['name']).read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Pinned tokenizer changed')
    tokenizer=Tokenizer.from_file(str(tokenroot/'tokenizer.json'))
    environment=ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True)
    # Match the inspected Transformers 5.12.1 renderer, whose JSON filter
    # deliberately differs from Jinja's HTML-escaping, sorted-key default.
    environment.filters['tojson']=lambda value,ensure_ascii=False,indent=None,separators=None,sort_keys=False: json.dumps(
        value,ensure_ascii=ensure_ascii,indent=indent,separators=separators,sort_keys=sort_keys)
    def fail(message):raise ValueError(message)
    environment.globals['raise_exception']=fail
    template=environment.from_string((tokenroot/'chat_template.jinja').read_text())
    def render(messages,tools,generation):
        return template.render(messages=normalize(messages),tools=tools,add_generation_prompt=generation,
            enable_thinking=True,preserve_thinking=True,add_vision_id=False)
    teacher_benchmark=ROOT/'reports/kaggle/general-learner-v1/benchmark.json'
    master=json.loads(teacher_benchmark.read_text())
    games=sorted([g['game_id'] for g in master['game_runs']],
        key=lambda k:sha256(('arc3-27b-pilot-v1/'+k).encode()).hexdigest())
    split={game:('train' if i<16 else 'validation' if i<20 else 'test') for i,game in enumerate(games)}
    OUT.mkdir(parents=True,exist_ok=True)
    split_report=dict(policy='Whole game hash allocation fixed before the 27B result; gradient holdout, not a claim of researcher blindness.',
        salt='arc3-27b-pilot-v1/',games=split,
        boundary='All games are public development games already studied. Hidden competition games remain the ultimate generalization test. This real-trace pilot replaces the initial synthetic-only data proposal; it does not provide an untouched public test.')
    split_file=OUT/'split.json'
    if split_file.exists() and json.loads(split_file.read_text())!=split_report:raise ValueError('Frozen split changed')
    split_file.write_text(json.dumps(split_report,indent=2)+'\n')
    source_specs=[(DIRECTORY/'teacher-traces',teacher_benchmark),
        (ROOT/'reports/kaggle/duck-m2-benchmark-v2',ROOT/'reports/kaggle/duck-m2-benchmark-v2/benchmark.json'),
        (DIRECTORY/'teacher-prefixes/general',teacher_benchmark),
        (DIRECTORY/'teacher-prefixes/control',ROOT/'reports/kaggle/prediction-matched-control-v1/benchmark.json'),
        (DIRECTORY/'teacher-prefixes/prediction',ROOT/'reports/kaggle/prediction-matched-prediction-v1/benchmark.json')]
    # Use only our own observed completed-level action counts as efficiency filters.
    benchmarks=[teacher_benchmark,ROOT/'reports/kaggle/prediction-matched-control-v1/benchmark.json',
        ROOT/'reports/kaggle/prediction-matched-prediction-v1/benchmark.json']+[b for _,b in source_specs]
    minimum={}
    for path in set(benchmarks):
        if not path.exists():continue
        for game in json.loads(path.read_text())['game_runs']:
            for level,count in enumerate(game['actions_per_level'][:game['levels_completed']]):
                key=(game['game_id'],level)
                minimum[key]=min(minimum.get(key,count),count)
    counts=Counter();seen=set();selected=defaultdict(int);source_hashes={};written=Counter()
    streams={name:(OUT/(name+'.jsonl')).open('w',encoding='utf-8') for name in ['train','validation']}
    try:
        for directory,benchmark in source_specs:
            if not benchmark.exists():continue
            lookup={g['game_id']:g for g in json.loads(benchmark.read_text())['game_runs']}
            for path in sorted(directory.glob('*_p0_requests.jsonl')):
                game_id=path.name.split('_p0_')[0]
                if game_id not in split:raise ValueError('Unknown game in teacher data')
                if split[game_id]=='test':counts['test_files_excluded']+=1;continue
                game=lookup[game_id];source_hashes[str(path.relative_to(ROOT))]=sha256(path.read_bytes()).hexdigest()
                boundaries=[];total=0
                for value in game['actions_per_level'][:game['levels_completed']]:
                    total+=value;boundaries.append(total)
                for pair in paired_replies(path,counts):
                    request=pair['request'];action=request.get('action')
                    if type(action) is not int:counts['missing_action_index']+=1;continue
                    level=request_level(action,boundaries)
                    if level is None:counts['unfinished_level_reply']+=1;continue
                    if observed_level(request['messages'])!=level+1:
                        counts['observed_level_disagrees_with_recording']+=1;continue
                    if game['actions_per_level'][level]>1.5*minimum[(game_id,level)]:
                        counts['inefficient_level_reply']+=1;continue
                    try:valid=python_reply(pair['assistant'],pair['results'])
                    except (ValueError,TypeError,KeyError):valid=False
                    if not valid:counts['invalid_or_failed_python_reply']+=1;continue
                    usage=pair['response'].get('usage') or {}
                    if usage.get('prompt_tokens',10**9)>args.context_tokens:counts['teacher_prompt_too_long']+=1;continue
                    messages=request['messages'];assistant=pair['assistant'];tools=request['tools']
                    try:
                        prefix=render(messages,tools,True);full=render(messages+[assistant],tools,False)
                    except Exception as exc:
                        counts['template_error/'+type(exc).__name__]+=1;continue
                    if not full.startswith(prefix):counts['assistant_prefix_mismatch']+=1;continue
                    encoding=tokenizer.encode(full,add_special_tokens=False)
                    prefix_ids=tokenizer.encode(prefix,add_special_tokens=False).ids
                    if encoding.ids[:len(prefix_ids)]!=prefix_ids:
                        counts['token_boundary_prefix_mismatch']+=1;continue
                    supervised=len(encoding.ids)-len(prefix_ids)
                    if not 16<=supervised<=4096:counts['target_length_rejected']+=1;continue
                    # Reserve one 640x640 image's 400 visual tokens per image.
                    # Actual processor expansion and tensor loss masks remain a GPU gate.
                    images=[];image_extra=0;image_error=False
                    for message in messages:
                        if not isinstance(message.get('content'),list):continue
                        for part in message['content']:
                            if part.get('type')!='image_url':continue
                            url=part['image_url']['url'];images.append(url)
                            if not url.startswith('data:image/png;base64,'):image_error=True;break
                            with Image.open(BytesIO(base64.b64decode(url.split(',',1)[1],validate=True))) as image:
                                w,h=image.size
                            if w%32 or h%32 or not 65536<=w*h<=16777216:image_error=True;break
                            image_extra+=(w//32)*(h//32)-1
                    if image_error:counts['image_requires_unverified_resize']+=1;continue
                    if len(encoding.ids)+image_extra>args.context_tokens:counts['target_context_limit']+=1;continue
                    digest=sha256(stable(dict(messages=messages,assistant=assistant,tools=tools)).encode()).hexdigest()
                    if digest in seen:counts['duplicate_example']+=1;continue
                    seen.add(digest)
                    if selected[(game_id,level)]>=16:counts['game_level_cap']+=1;continue
                    selected[(game_id,level)]+=1
                    record=dict(example_id=digest,messages=normalize(messages+[assistant]),tools=tools,
                        assistant_start_char=len(prefix),rendered_text_sha256=sha256(full.encode()).hexdigest(),
                        assistant_start_text_token=len(prefix_ids),
                        template_kwargs=dict(enable_thinking=True,preserve_thinking=True),
                        text_tokens=len(encoding.ids),visual_expansion_tokens=image_extra,supervised_text_tokens=supervised,
                        metadata=dict(game_id=game_id,level=level+1,split=split[game_id],source=str(path.relative_to(ROOT)),
                            source_sha256=source_hashes[str(path.relative_to(ROOT))],
                            source_reply_visible_at_line=pair['source_reply_visible_at_line'],
                            source_request_action_number=action,source_next_request_action_number=pair['next_action'],
                            request_action_number_basis='One-based next-action number, independently matched to the last recorded user level.',
                            teacher_level_actions=game['actions_per_level'][level],
                            minimum_observed_own_level_actions=minimum[(game_id,level)],
                            efficiency_filter='At most 1.5 times our own minimum observed completed-level count; no human baselines.',
                            alignment='Exact prior recorded request prefix, paired completed response, next recorded assistant and complete tool results. Tool results are used for filtering only, not included after the target.'))
                    streams[split[game_id]].write(json.dumps(record,separators=(',',':'))+'\n');written[split[game_id]]+=1
                    counts['selected_action_replies' if pair['next_action']>action else 'selected_inspection_replies']+=1
    finally:
        for stream in streams.values():stream.close()
    report=dict(max_context_tokens=args.context_tokens,counts=dict(counts),examples=dict(written),source_sha256=source_hashes,
        per_game_level={game+'/L'+str(level+1):n for (game,level),n in selected.items()},
        split_sha256=sha256(split_file.read_bytes()).hexdigest(),
        files={name+'.jsonl':dict(sha256=sha256((OUT/(name+'.jsonl')).read_bytes()).hexdigest(),bytes=(OUT/(name+'.jsonl')).stat().st_size) for name in streams},
        train_ready=False,remaining_gates=['Actual multimodal processor expansion and assistant-only tensor loss mask.',
            'One real backward/optimizer step, finite gradients, checkpoint/reload and serving compatibility.',
            'Freeze a training budget and compare the deployed adapter on gradient-held-out games.'],
        boundary='Outcome-filtered teacher imitation, not verified reasoning, optimal behavior, unfamiliar-game transfer, training completion or a score improvement. No generated Python code was executed. Never copy retrospective level/action metadata into model inputs.')
    (OUT/'dataset-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','per_game_level']},indent=2))


if __name__=='__main__':main()
