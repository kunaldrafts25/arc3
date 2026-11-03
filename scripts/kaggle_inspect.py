"""Read competition pages and inspect the attached framework via official SDK."""
import json
import os
from zipfile import ZipFile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["KAGGLE_API_TOKEN"] = (ROOT/".kaggle/access_token").read_text(encoding="utf-8-sig").strip()
os.environ["KAGGLE_CONFIG_DIR"] = str(ROOT/".kaggle")
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()
competition = "arc-prize-2026-arc-agi-3"
pages = api.competition_list_pages(competition)
destination = ROOT / "reference/kaggle"
destination.mkdir(parents=True, exist_ok=True)
data = [{"name": page.name, "content": page.content} for page in pages]
(destination/"pages.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
print(json.dumps([{"name": p["name"], "characters": len(p["content"] or "")} for p in data]))
files = api.competition_list_files(competition, page_size=1000)
names = [entry.name for entry in files.files]
(destination/"file-names.json").write_text(json.dumps(names, indent=2), encoding="utf-8")
print("WHEELS", json.dumps([name for name in names if name.endswith(".whl")]))
api.competition_download_file(competition, "ARC-AGI-3-Agents/agents/agent.py", path=str(destination), quiet=True)
print("Downloaded attached framework agent interface for inspection")
wheel_name = "arc_agi_3_wheels/arc_agi-0.9.8-py3-none-any.whl"
api.competition_download_file(competition, wheel_name, path=str(destination), quiet=True)
wheel_path = destination / wheel_name
with ZipFile(wheel_path) as wheel:
    scorer = wheel.read("arc_agi/scorecard.py").decode("utf-8")
print("ATTACHED_SCORER_CAP", [line.strip() for line in scorer.splitlines() if "score = min(score" in line])
