"""Package tracked source, evidence and generated notebook; exclude local state."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
paths = sorted(set(p for p in paths if p) | {"notebooks/submission.ipynb"})
for relative in paths:
    if relative.startswith((".kaggle/", ".venv/", "vendor/", "environment_files/", "recordings/", ".git/")):
        raise ValueError(f"Local-only path unexpectedly tracked: {relative}")
    if not (ROOT / relative).is_file():
        raise FileNotFoundError(relative)
manifest = {
    "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "sha256": {p: sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
    "validation_boundary": "Local public gameplay and Kaggle v3 offline public smoke verified; v0.2 hidden score pending",
    "competition_submission": "57630597",
}
destination = ROOT.parent / "arc-hydra-v0.2.zip"
with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
    for relative in paths:
        archive.write(ROOT/relative, "arc-hydra-v0.2/"+relative)
    archive.writestr("arc-hydra-v0.2/RELEASE_MANIFEST.json", json.dumps(manifest, indent=2)+"\n")
with ZipFile(destination) as archive:
    assert archive.testzip() is None
print(f"Created {destination} ({destination.stat().st_size:,} bytes); ZIP integrity verified")
