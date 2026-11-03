"""Small, durable gameplay counters for public runs and competition reruns."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import threading


def gameplay_snapshot(benchmark):
    runs=list(benchmark.game_runs)
    model_games=actions=tokens=levels=0
    states=Counter()
    for run in runs:
        count=sum(list(run.actions_per_level))
        generated=sum(a.generated_tokens for a in list(run.history))+run.final_generated_tokens
        actions+=count
        tokens+=generated
        levels+=run.levels_completed
        model_games+=bool(count>1 and generated>0)
        states[str(run.state)]+=1
    return dict(games=len(runs),model_gameplay_games=model_games,actions=actions,
                generated_tokens=tokens,levels_completed=levels,states=dict(states))


def write_lifecycle(path,phase,context,gameplay=None,error=None):
    path=Path(path)
    record=dict(phase=phase,context=context,gameplay=gameplay,error=error,
                checked_at=datetime.now(timezone.utc).isoformat())
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)
    return record


def start_lifecycle(benchmark,path,context,interval=30):
    stop=threading.Event()
    lock=threading.Lock()

    def save(phase,error=None):
        with lock:
            return write_lifecycle(path,phase,context,gameplay_snapshot(benchmark),error)

    def monitor():
        while not stop.wait(interval):
            try:
                save('playing')
            except Exception as error:
                print('ARC-Hydra lifecycle checkpoint failed:',type(error).__name__,flush=True)

    save('playing')
    thread=threading.Thread(target=monitor,daemon=True)
    thread.start()

    def finish(error=None):
        stop.set()
        thread.join(timeout=5)
        record=save('run_failed' if error else 'run_finished',error)
        print('ARC_HYDRA_GAMEPLAY',json.dumps(record['gameplay'],sort_keys=True),flush=True)
        if not error and not record['gameplay']['model_gameplay_games']:
            save('no_model_gameplay','No substantive model-driven gameplay recorded')
            raise RuntimeError('Run ended without substantive model-driven gameplay; inspect lifecycle and serve.log')
        return record

    return finish
