"""Resolve exact attached dataset/model names across Kaggle mount layouts."""
from pathlib import Path


def resolve_inputs(values, input_root='/kaggle/input'):
    root=Path(input_root)
    resolved={}
    markers=dict(WHEELHOUSE_DIR='requirements.lock',
                 ORIG_BUNDLE_DIR='src/ARC3-Inference/inference/agent/tool_agent.py',
                 MODEL_DIR='config.json',DRAFT_MODEL_DIR='config.json',
                 COMPETITION_WHEELHOUSE='arc_agi*.whl')
    for key,marker in markers.items():
        original=Path(values[key])
        parts=original.parts
        # Input values are the pinned builder paths; no task/game file lookup.
        if 'datasets' in parts:
            pos=parts.index('datasets')
            owner,name=parts[pos+1:pos+3]
            candidates=[original,root/name,root/owner/name]
        elif 'models' in parts:
            pos=parts.index('models')
            owner,name=parts[pos+1:pos+3]
            suffix=Path(*parts[pos+3:])
            candidates=[original,root/name/suffix,root/owner/name/suffix]
        elif 'competitions' in parts:
            pos=parts.index('competitions')
            name=parts[pos+1]
            candidates=[original,root/name/Path(*parts[pos+2:])]
        else:
            raise ValueError('Unrecognized pinned input path: '+str(original))
        found=next((path for path in candidates if any(p.is_file() for p in path.glob(marker))),None)
        if found is None:
            visible=sorted(p.name for p in root.iterdir()) if root.is_dir() else []
            raise FileNotFoundError(f'{key} not mounted with required {marker}; tried '
                                    f'{[str(p) for p in candidates]}; input roots={visible}')
        resolved[key]=str(found)
    return resolved
