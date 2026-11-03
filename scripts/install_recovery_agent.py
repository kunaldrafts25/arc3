"""Wrap the tested study host with an advisory cross-decision recovery monitor."""
from hashlib import sha256
import json
from pathlib import Path

WRAPPER='''
# ARC_HYDRA_RECOVERY_ADVISORY
from inference.agent.hydra_recovery import RecoveryMonitor as _HydraRecoveryMonitor, render_notice as _hydra_render_recovery
_hydra_recovery_original_ensure = ToolAgent._ensure_session
_hydra_recovery_original_prompt = ToolAgent._build_user_prompt

def _hydra_recovery_ensure(self, state_path):
    result = _hydra_recovery_original_ensure(self, state_path)
    key = str(state_path.resolve())
    if getattr(self, '_hydra_recovery_path', None) != key:
        self._hydra_recovery_path = key
        self._hydra_recovery_monitor = _HydraRecoveryMonitor()
    return result

def _hydra_recovery_prompt(self, *args, **kwargs):
    original = _hydra_recovery_original_prompt(self, *args, **kwargs)
    monitor = getattr(self, '_hydra_recovery_monitor', None)
    if monitor is None:
        monitor = self._hydra_recovery_monitor = _HydraRecoveryMonitor()
    evidence = monitor.observe(kwargs.get('current_frame'), kwargs.get('history_entries') or [])
    if evidence is not None and getattr(self, '_hydra_recovery_path', None):
        try:
            with Path(self._hydra_recovery_path).with_suffix('.recovery.events.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(evidence, sort_keys=True) + '\\n')
        except OSError as exc:
            log.warning('Recovery evidence persistence failed: %s', type(exc).__name__)
    return original + _hydra_render_recovery(evidence)

ToolAgent._ensure_session = _hydra_recovery_ensure
ToolAgent._build_user_prompt = _hydra_recovery_prompt
'''


def install(bundle,library):
    directory=Path(bundle)/'src/ARC3-Inference/inference/agent'
    path=directory/'tool_agent.py';before=path.read_text(encoding='utf-8')
    if 'ARC_HYDRA_RECOVERY_ADVISORY' in before:raise ValueError('Recovery already installed')
    if 'from inference.agent.hydra_study import' not in before:raise ValueError('Study host must be installed first')
    after=before+'\n'+WRAPPER
    compile(library,'recovery-monitor','exec');compile(after,'recovery-host','exec')
    (directory/'hydra_recovery.py').write_text(library,encoding='utf-8');path.write_text(after,encoding='utf-8')
    report=dict(extension='recovery-advisory-v1',library_sha256=sha256(library.encode()).hexdigest(),
        before_sha256=sha256(before.encode()).hexdigest(),after_sha256=sha256(after.encode()).hexdigest(),
        action_gating=False)
    print('ARC_HYDRA_RECOVERY_INSTALLED',json.dumps(report,sort_keys=True),flush=True)
    return report
