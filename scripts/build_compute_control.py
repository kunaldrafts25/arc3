"""Historical public-input experiment builder; rejects unsupported RTX runs.

Official ARC-3 accelerator guidance limits RTX sessions to notebooks attached
to the competition. The two earlier unattached versions failed without a GPU
driver. Keep those uploaded files frozen, but do not generate more such jobs.
"""
from hashlib import sha256
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATASET='kunalsinghh03/arc3-public-development-inputs'


def resolver_source():
    source=(ROOT/'scripts/resolve_kaggle_inputs.py').read_text(encoding='utf-8')
    old='            candidates=[original,root/name,root/owner/name]'
    assert source.count(old)==1
    return source.replace(old,'            suffix=Path(*parts[pos+3:])\n            candidates=[original,root/name/suffix,root/owner/name/suffix]')


def package(kind='control'):
    if kind not in ('control','inspection'):raise ValueError('Unknown compute experiment')
    gate=ROOT/'reports/kaggle/public-inputs-probe-v1'
    report=json.loads((gate/'public-input-probe.json').read_text(encoding='utf-8'))
    if not report['passed'] or report['games']!=25 or report['total_levels']!=183:
        raise ValueError('Public input equivalence gate has not passed')
    upload=json.loads((gate/'upload.json').read_text(encoding='utf-8'))
    for name,expected in upload['files'].items():
        if sha256((ROOT/'notebooks/public_inputs_probe'/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Public CPU package changed: '+name)
    manifest=ROOT/'reference/public-development-inputs/public-input-manifest.json'
    expected_manifest=upload['dataset_manifest_sha256']
    if sha256(manifest.read_bytes()).hexdigest()!=expected_manifest:raise ValueError('Public input manifest changed')
    source=ROOT/'notebooks'/('flexible_extended_control' if kind=='control' else 'inspection_candidate')
    notebook=json.loads((source/'submission.ipynb').read_text(encoding='utf-8'))
    metadata=json.loads((source/'kernel-metadata.json').read_text(encoding='utf-8'))
    if metadata.get('enable_gpu') and metadata.get('machine_shape') == 'NvidiaRtxPro6000':
        raise ValueError('RTX PRO 6000 requires an ARC-AGI-3 competition attachment. '
                         'This public-only builder removes that attachment; use the '
                         'original entered account and competition notebook instead.')
    provenance=json.loads((source/'provenance.json').read_text(encoding='utf-8'))
    config=next(c for c in notebook['cells'] if c['source'].startswith('import json\nimport os'))
    original_resolver=(ROOT/'scripts/resolve_kaggle_inputs.py').read_text(encoding='utf-8')
    invocation=f'exec({original_resolver!r}, _hydra_inputs_ns)'
    assert config['source'].count(invocation)==1
    config['source']=config['source'].replace(invocation,f'exec({resolver_source()!r}, _hydra_inputs_ns)')
    old="COMPETITION_WHEELHOUSE = '/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels'"
    new=f"COMPETITION_WHEELHOUSE = '/kaggle/input/datasets/{DATASET}/arc_agi_3_wheels'"
    assert config['source'].count(old)==1;config['source']=config['source'].replace(old,new)
    line=next(line for line in config['source'].splitlines() if line.startswith('TRUE_SUBMISSION ='))
    config['source']=config['source'].replace(line,line+'\nif TRUE_SUBMISSION:\n    raise RuntimeError("This notebook is public development only; use the original competition account for submissions")')
    marker='# Apply harness patch'
    checks='''from hashlib import sha256 as _hydra_public_sha
_hydra_public_root=Path(COMPETITION_WHEELHOUSE).parent
_hydra_public_manifest_path=_hydra_public_root/'public-input-manifest.json'
'''
    checks+=f'assert _hydra_public_sha(_hydra_public_manifest_path.read_bytes()).hexdigest()=={expected_manifest!r}, "Public input version changed"\n'
    checks+='''_hydra_public_manifest=json.loads(_hydra_public_manifest_path.read_text())
for _hydra_public_item in _hydra_public_manifest['environment_files']:
    assert _hydra_public_sha((_hydra_public_root/_hydra_public_item['file']).read_bytes()).hexdigest()==_hydra_public_item['sha256']
for _hydra_public_item in _hydra_public_manifest['pypi_wheels']:
    assert _hydra_public_sha((Path(COMPETITION_WHEELHOUSE)/_hydra_public_item['file']).read_bytes()).hexdigest()==_hydra_public_item['sha256']
print('ARC_HYDRA_PUBLIC_INPUTS_VERIFIED', len(_hydra_public_manifest['game_ids']), 'public practice games', flush=True)

'''
    assert config['source'].count(marker)==1;config['source']=config['source'].replace(marker,checks+marker)
    slug='arc-hydra-flexible-extended-control' if kind=='control' else 'arc-hydra-exact-inspection-candidate'
    title='ARC Hydra Flexible Extended Control' if kind=='control' else 'ARC Hydra Exact Inspection Candidate'
    metadata.update(id='kunalsinghh03/'+slug,title=title,
        competition_sources=[],dataset_sources=metadata['dataset_sources']+[DATASET])
    provenance.update(development_compute_account='kunalsinghh03',intended_submission_account='kunalsinghh25',
        compute_token_file='access_token2',public_input_cpu_gate=upload['kernel'],public_input_manifest_sha256=expected_manifest,
        input_resolver_sha256=sha256(resolver_source().encode()).hexdigest(),competition_datasource_attached=False,
        account_scope='User requested development compute only. No enrollment, rule acceptance or submission on this account.',
        account_rule_compliance='Not independently established; input-access validation does not certify account-rule compliance.',
        comparison_changes='Same source agent variant/models/runtime; public practice datasource replaces competition datasource, with exact seeded RESET equivalence validated on CPU.')
    setup=next(c for c in notebook['cells'] if c['source'].startswith('# Each bundled repo exposes'))
    setup['source']+=f'\n(WORKING_DIR/"hydra_compute_provenance.json").write_text(json.dumps({provenance!r},indent=2))\n'
    notebook['cells'][0]['source']+='\n\nDevelopment account: kunalsinghh03. Uses validated public-only practice assets; no competition datasource or submission mode. All 25 initial observations matched prior direct public play on the offline CPU gate.'
    return notebook,metadata,provenance


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=('control','inspection'),default='control')
    args=parser.parse_args()
    notebook,metadata,provenance=package(args.kind)
    output=ROOT/'notebooks'/('compute_flexible_control' if args.kind=='control' else 'compute_inspection_candidate');output.mkdir(exist_ok=True)
    for name,value in [('submission.ipynb',notebook),('kernel-metadata.json',metadata),('provenance.json',provenance)]:
        (output/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(kernel=metadata['id'],competition_sources=metadata['competition_sources'],wall_seconds=32400)))
