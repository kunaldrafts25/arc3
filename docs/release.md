> GitHub publication note: this expanded snapshot retains archived public logs up to 11 MB; use `--max-file-mib 25` for the release audit. GitHub's normal file limit is larger. Model weights and credentials remain excluded.

# GitHub release and reproduction notes

## What is preserved

The cleanup retains source, tests, frozen notebook packages, provenance,
compact evaluation evidence, and research conclusions. The historical README
is preserved as [starter_guide.md](starter_guide.md). Existing ARC2 work and
its jobs are separate and were not reset, reformatted, or removed.

Large/private artifacts remain on disk under ignored paths: credentials,
adapters/checkpoints, raw teacher requests and training rows, downloaded wheels,
tokenizers, copied dependency sources, raw model transcripts, and host logs.
Ignoring them does not delete them. Five previously tracked preflight transcripts
were removed from the Git index with `git rm --cached`; all five remain on disk.
Those five removals, `.gitattributes`, and ARC3 artifact byte-preservation updates
are staged, with other source/documentation changes left for review. The artifact
updates change Git newline handling, not their local evaluated content. This cleanup
does not release a trained model.

## Verify before committing

From the repository root, using Python 3.12:

```powershell
.venv/Scripts/python.exe -m scripts.audit_release --max-file-mib 25
.venv/Scripts/python.exe -m pytest --ignore-glob="tests/test_arc2*.py"
git diff --check
git status --short
```

The audit considers both tracked and nonignored files. It blocks known model
weight formats, credential files, recognizable tokens/private keys/signed URLs,
the current local Kaggle credential, and files above 10 MiB. It prints only
paths and finding types. It does not audit dependency security or grant licenses.
Use the accompanying tests to verify detection without real credentials.

To make a source-only ZIP without changing the shared branch or index:

```powershell
.venv/Scripts/python.exe -m scripts.export_release
```

The exporter audits first, preserves actual file bytes, excludes ignored local
artifacts and `.git`, and refuses to overwrite an existing export. It includes
the current ARC2 source in the shared repository; review that track separately
before publishing a combined project. `dist/` itself is ignored.

The complete local ARC3 test suite passed **219 tests**, including four release-audit
tests. Integration tests use the local ignored framework checkouts
and completed CPU gate records; CI deliberately runs the self-contained subset.
The **55-test CI subset** and the frozen memory/prediction composition checks
also passed in an isolated source-only snapshot without private artifacts or
the ignored vendor checkout. All **867 reachable Git blobs** were scanned for
the configured credential patterns and the current local token; no matches
were found. This is a scoped check, not a guarantee against every secret type.

## Reproduction boundaries

The original starter setup pins `ARC-AGI-3-Agents` to
`4743e7d0aaae0ded0d98a89a7e282e63564cd58b`. Duck extension integration additionally
requires the read-only source from
`da-fr/arc-agi-3-solution@10882e332d883af3e61616df8c8a17d03a328a75`, with its
`ARC3-Inference` directory under `vendor/duck-m2/` as used by the research tests.
See the builders and source manifests for exact installed-file hashes.

Frozen notebook JSON is kept byte-for-byte. Reformatting it would invalidate
the provenance checks. `.gitattributes` disables Git newline conversion for
ARC3 notebook/evidence paths, because recorded Windows CRLF hashes otherwise
change on a Linux checkout. Existing artifacts may therefore appear changed
relative to their previously normalized Git blobs; their local evaluated bytes
have not been rewritten. ARC2 paths retain their previous newline behavior.
ARC3 Python source uses LF consistently for the same reason. The cleanup has staged the attributes and refreshed the previously normalized
ARC3 artifact index entries; review them with `git diff --cached --ignore-space-at-eol`.
ARC2 entries were excluded. A fresh repository created from the source export
already records the correct bytes under these attributes.
Notebook metadata references external public models and
runtime inputs that must be attached on Kaggle; those large inputs are not
bundled in Git. Some training experiments also require private trace bundles.
Their source and outcome records are provided, but the private bundles and
trained weights are not part of this release. Cached research downloads can be
retrieved from the pinned URLs and commits in their `sources.json` files.

Historical launchers are operational tools, not a recommended way to spend
remaining quota after the deadline. Do not run them simply to verify an import.
`audit_release` and CI make no network calls, GPU launches, or submissions.

## GitHub destination

At cleanup, `origin` points to the official ARC Prize starter repository.
The shared branch and remote configuration are unchanged. Choose your own
GitHub repository when publishing; do not push these changes to the upstream
starter by accident. No commit, force-push, or public upload is part of the
cleanup. Review ARC2 changes separately before staging a combined release.
