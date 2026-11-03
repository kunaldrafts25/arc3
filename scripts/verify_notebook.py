"""Validate bundled source in a fresh interpreter outside the source tree.

This does not emulate the Kaggle gateway or certify a competition submission.
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
notebook = json.loads((ROOT / "notebooks/submission.ipynb").read_text(encoding="utf-8"))
stage = ROOT / "test-artifacts/notebook"
stage.mkdir(parents=True, exist_ok=True)
source_cell = next(c["source"] for c in notebook["cells"] if "HYDRA_SOURCES = " in c["source"])
exec(source_cell.replace("Path('/tmp')", f"Path({str(stage)!r})"))
agent_cell = next(c["source"] for c in notebook["cells"] if c["source"].startswith("%%writefile"))
(stage / "my_agent.py").write_text(agent_cell.split("\n", 1)[1], encoding="utf-8")
code = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
sys.path.insert(1, sys.argv[2])
import hydra
import my_agent
from arcengine import FrameData, GameAction, GameState
assert Path(hydra.__file__).is_relative_to(Path(sys.argv[1]))
agent = my_agent.MyAgent(card_id='test',game_id='test',agent_name='test',ROOT_URL='http://localhost',record=False,arc_env=None)
frame = FrameData(game_id='test',state=GameState.NOT_FINISHED,available_actions=[6],frame=[[[1,0],[0,1]]])
action = agent.choose_action([frame],frame)
assert action is GameAction.ACTION6
assert 0 <= action.action_data.x <= 63
print('Bundled Hydra imports and chooses a valid complex action in an isolated interpreter')
"""
subprocess.run([sys.executable, "-I", "-c", code, str(stage),
                str(ROOT / "vendor/ARC-AGI-3-Agents")], cwd=stage, check=True)
