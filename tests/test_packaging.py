import ast
import json
from pathlib import Path
from scripts.build_notebook import build


def test_notebook_embeds_all_hydra_sources_and_disables_internet():
    notebook = build()
    assert notebook["metadata"]["kaggle"]["isInternetEnabled"] is False
    cell = next(c["source"] for c in notebook["cells"] if "HYDRA_SOURCES = " in c["source"])
    assignment = ast.parse(cell).body[1]
    sources = ast.literal_eval(assignment.value)
    root = Path(__file__).resolve().parents[1]
    for path in (root / "hydra").rglob("*.py"):
        key = path.relative_to(root).as_posix()
        assert sources[key] == path.read_text(encoding="utf-8")
        compile(sources[key], key, "exec")
    assert any("cp -r /tmp/hydra" in c["source"] for c in notebook["cells"])
    assert "--no-index" in notebook["cells"][1]["source"]
    json.dumps(notebook)


def test_public_smoke_does_not_run_in_competition_rerun(monkeypatch):
    monkeypatch.setenv("KAGGLE_IS_COMPETITION_RERUN", "1")
    smoke = next(c["source"] for c in build()["cells"] if "hydra_public_smoke.json" in c["source"])
    namespace = {}
    exec(compile(smoke, "public_smoke_cell", "exec"), namespace)
    assert "MyAgent" not in namespace
    assert "arcade" not in namespace
