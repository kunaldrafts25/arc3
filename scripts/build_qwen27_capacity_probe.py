"""One bounded real-game counterfactual for observed 27B queue/capacity mismatch."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def build():
    source=ROOT/'notebooks/qwen27_matched_baseline'
    old=json.loads((source/'manifest.json').read_text())
    if any(sha256((source/n).read_bytes()).hexdigest()!=h for n,h in old['files'].items()):raise ValueError('Executed baseline changed')
    analysis=json.loads((ROOT/'reports/kaggle/qwen27-matched-baseline-v1/analysis.json').read_text())
    if not analysis['model_gameplay_verified']:raise ValueError('Completed real baseline required')
    notebook=deepcopy(json.loads((source/'submission.ipynb').read_text()))
    metadata=json.loads((source/'kernel-metadata.json').read_text())
    provenance=json.loads((source/'provenance.json').read_text())
    provenance.update(candidate='qwen27-fair-capacity',experiment_variant='qwen27-capacity',
        changed_components=['Server requests4 to8','Mamba states24 to48','Decode graphs include8','Server LPM toFCFS queue policy'],
        retained_components=['27B FP8 target','DFlash2 draft','Runtime, sampler and agent','128K analyzer context','All25 public games','7200-second total cap'],
        hypothesis='Observed four server slots versus ten harness streams with queue p99 676s; test fairer admission and higher serving capacity.',
        comparison_boundary='Combined deployment-capacity repair, not an isolated queue-policy effect. Potential GPU memory pressure/cache retraction. No training, automatic promotion or official submission.')
    env=notebook['cells'][6]['source']
    old_record=json.loads((source/'provenance.json').read_text())
    expected=f'(WORKING_DIR/"hydra_model_candidate.json").write_text(json.dumps({old_record!r},indent=2))'
    assert env.count(expected)==1
    notebook['cells'][6]['source']=env.replace(expected,f'(WORKING_DIR/"hydra_model_candidate.json").write_text(json.dumps({provenance!r},indent=2))')
    launcher=notebook['cells'][14]['source']
    for before,after in [('MAXREQ=4','MAXREQ=8'),('CUDAGRAPH_MAXBS=4','CUDAGRAPH_MAXBS=8'),('MAMBA_CACHE=24','MAMBA_CACHE=48'),
        ('graph_bs=[1,2,4]','graph_bs=[1,2,4,8]'),("'--max-running-requests','4'","'--max-running-requests','8'"),
        ("'--cuda-graph-max-bs-decode','4'","'--cuda-graph-max-bs-decode','8'"),
        ("'--max-mamba-cache-size','24'","'--max-mamba-cache-size','48'"),
        ("'--schedule-policy','lpm'","'--schedule-policy','fcfs'")]:
        assert launcher.count(before)==1,before
        launcher=launcher.replace(before,after)
    compile(launcher,'27b-fair-capacity-launcher','exec');notebook['cells'][14]['source']=launcher
    notebook['cells'][0]['source']='# ARC3 27B fair-capacity counterfactual\n\nSame untrained weights and agent as the completed27B baseline. Eight server slots,48 Mamba states and FCFS admission. Two-hour total cap, all25games. Tests an observed deployment mismatch, not training quality. No official submission. Upstream attribution retained.'
    metadata.update(id='kunalsinghh25/arc-hydra-qwen27-fair-capacity',title='ARC Hydra Qwen27 Fair Capacity')
    output=ROOT/'notebooks/qwen27_fair_capacity';output.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n')
    result=dict(kernel=metadata['id'],wall_seconds=7200,files={n:sha256((output/n).read_bytes()).hexdigest() for n in old['files']})
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':build()
