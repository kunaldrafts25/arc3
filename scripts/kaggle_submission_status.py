"""Read and record one submission status without revealing local credentials."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("submission_ref", type=int)
args = parser.parse_args()
os.environ["KAGGLE_API_TOKEN"] = (ROOT/".kaggle/access_token").read_text(encoding="utf-8-sig").strip()
os.environ["KAGGLE_CONFIG_DIR"] = str(ROOT/".kaggle")
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()
submission = api.get_submission(args.submission_ref)
record = dict(submission_ref=str(submission.ref),
              status=submission.status.name if submission.status else None,
              public_score=submission.public_score, private_score=submission.private_score,
              error=submission.error_description,
              checked_at=datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat())
destination = ROOT / "reports/kaggle"
destination.mkdir(parents=True, exist_ok=True)
(destination/"submission-status.json").write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
with (destination/"submission-status-history.jsonl").open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(record)+"\n")
print(json.dumps(record))
