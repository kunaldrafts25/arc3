"""Validate complete experiments and exclude superseded novelty ablations."""
import hashlib
import json
from pathlib import Path
from report import render

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    path = ROOT / relative
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in rows:
        row["source_file"] = relative
    return rows


def validate(rows, policies, seeds):
    assert set(r["policy"] for r in rows) == set(policies)
    assert len(rows) == len(policies)*len(seeds)*25
    keys = [(r["policy"], r["seed"], r["game_id"]) for r in rows]
    assert len(keys) == len(set(keys)), "duplicate experiment rows"
    games = {r["game_id"] for r in rows}
    assert len(games) == 25
    for policy in policies:
        for seed in seeds:
            assert {r["game_id"] for r in rows if r["policy"] == policy and r["seed"] == seed} == games
    assert all(not r["exceptions"] for r in rows), "recorded execution failures"
    assert all(r["action_count"] <= 200 for r in rows)


def save(rows, stem):
    destination = ROOT / "reports" / (stem + ".jsonl")
    destination.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    destination.with_suffix(".md").write_text(render(rows), encoding="utf-8")
    print(f"{stem}: {len(rows)} validated rows")


if __name__ == "__main__":
    main = read("reports/public-ablation-v01.jsonl")
    corrected = read("reports/novelty-corrected-v01.jsonl")
    coverage = read("reports/coverage-v01.jsonl")
    confirmation = read("reports/confirmation-v01.jsonl")
    memory_confirmation = read("reports/memory-confirmation-v01.jsonl")
    # Keep original JSONL evidence untouched. Only consolidated reports exclude
    # the model-enabled policy that was initially mislabeled as novelty.
    training = [r for r in main if r["policy"] != "novelty"] + coverage
    training += [r for r in corrected if r["seed"] in (0, 1, 2)]
    confirm = [r for r in confirmation if r["policy"] in ("starter", "random")]
    confirm += memory_confirmation + [r for r in corrected if r["seed"] in (3, 4)]
    validate(training, ["starter", "random", "novelty", "memory", "planning", "persistent", "coverage"], [0, 1, 2])
    validate(confirm, ["starter", "random", "novelty", "memory"], [3, 4])
    save(training, "public-ablation")
    save(confirm, "confirmation")
    paths = sorted({r["source_file"] for r in training + confirm})
    manifest = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    (ROOT / "reports/evidence-sha256.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
