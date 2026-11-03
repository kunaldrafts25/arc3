# General learner CPU gate

Exact cloud version: `kunalsinghh25/arc-hydra-study-cpu-probe/2`, COMPLETE.

The composed offline agent passed eight original mechanical sandbox cases,
16 rendered prompt combinations and nine memory/host integration cases.
These include actual sandbox export/restore, rejection of unseen evidence
references, note-size bounds, prior-level rechecking, actual host sidecar
persistence, context restart/prompt rendering and game isolation when paths
share a directory. No model inference or ARC score is established by this gate.

Version 1 failed while constructing the synthetic local agent because the
probe had not set LOCAL_ANALYZER_MODEL_ID. Setting the synthetic model ID
allowed the real host checks to run in version 2. Neither CPU run used GPU quota.

The four downloaded JSON artifacts record the actual executed sources and
results. `upload.json` hashes the unchanged local version-2 package after gate
completion; its recording boundary is explicit. The GPU notebook checks both
installed extension reports against these completed CPU artifacts before use.
