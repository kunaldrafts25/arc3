# Published research artifacts

The [artifact release](https://github.com/kunaldrafts25/arc3/releases/tag/untagged-3f7374879df81a5dcba5) contains **319 original files** (3,003,424,404 bytes) as two individual adapters and one lossless raw-data archive. All payloads have server-verified SHA-256 hashes. Every restored file was independently verified in both repository layouts.

```bash
python scripts/restore_artifacts.py
python scripts/restore_artifacts.py --verify-only
```

Use `--kind adapters` or `--kind raw` for a subset. Existing matching files are reused; conflicting files require `--overwrite`. Payloads are cached in ignored `.artifact-cache/`. Original file paths and hashes are recorded in `ARTIFACTS.json`. Restored large data remain excluded from regular Git.

The adapters are research negative results: gameplay regressed. See [MODEL_CARD.md](MODEL_CARD.md). Model and dependency licenses remain attached to their original components.
