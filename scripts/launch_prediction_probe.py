"""Journal one private CPU gate; never starts a GPU or submits to competition."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', type=int, default=1)
    parser.add_argument('--study-combination',action='store_true')
    args = parser.parse_args()
    package = ROOT/('notebooks/prediction_cpu_probe' if args.revision == 1 else f'notebooks/prediction_cpu_probe_v{args.revision}')
    expected_kernel = 'kunalsinghh25/arc-hydra-prediction-cpu-probe'
    if args.study_combination:
        if args.revision != 1:
            raise ValueError('Study composition gate has its own first revision')
        package = ROOT/'notebooks/prediction_study_cpu_probe'
        expected_kernel = 'kunalsinghh25/arc-hydra-prediction-study-cpu-probe'
    metadata = json.loads((package/'kernel-metadata.json').read_text())
    if (metadata['id'] != expected_kernel
            or any(metadata[k] is not False for k in ('enable_gpu','enable_tpu','enable_internet'))
            or metadata.get('machine_shape')
            or metadata['is_private'] is not True or metadata['competition_sources'] or metadata['model_sources']):
        raise ValueError('Only the private offline model-free CPU probe is authorized by this launcher')
    manifest = json.loads((package/'source-manifest.json').read_text())
    for group in ('files','prediction_files')+ (('study_files',) if args.study_combination else ()):
        for name, digest in manifest[group].items():
            if sha256((ROOT/name).read_bytes()).hexdigest() != digest:
                raise ValueError('Probe source changed: '+name)
    token = ROOT/'.kaggle/access_token'
    os.environ['KAGGLE_API_TOKEN'] = token.read_text(encoding='utf-8-sig').strip()
    os.environ['KAGGLE_CONFIG_DIR'] = str(token.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    quota = api.quota_view().gpu_quota
    if quota.is_pay_to_scale_enabled:
        raise RuntimeError('Paid scaling must remain disabled')
    shared = api.kernels_status('kunalsinghh25/arc-hydra-arc2-inference-hybrid')
    directory = ROOT/f'reports/kaggle/prediction-cpu-probe-v{args.revision}'
    if args.study_combination:
        directory = ROOT/'reports/kaggle/prediction-study-cpu-probe-v1'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/'launch.json'
    state = dict(phase='launching', checked_at=datetime.now(timezone.utc).isoformat(),
                 kernel=metadata['id'], cpu_only=True,
                 shared_arc2_development_status=shared.status.name,
                 available_gpu_seconds=(quota.total_time_allowed-quota.time_used-quota.time_reserved).total_seconds(),
                 files={name:sha256((package/name).read_bytes()).hexdigest()
                        for name in ('kernel-metadata.json','probe.ipynb','source-manifest.json')})
    with path.open('x', encoding='utf-8') as stream:
        json.dump(state,stream,indent=2)
    try:
        response = api.kernels_push(str(package),timeout='1800')
        state.update(phase='accepted',response=response.to_dict())
    except Exception as exc:
        state.update(phase='outcome_unconfirmed',error_type=type(exc).__name__)
    path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(state,indent=2))


if __name__ == '__main__':
    main()
