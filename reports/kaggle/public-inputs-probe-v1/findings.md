# Public-only development inputs

Exact CPU version `kunalsinghh03/arc-hydra-public-inputs-probe/1` completed.
All 25 public practice environments (183 levels) loaded offline with
arc-agi 0.9.8 and arcengine 0.9.3. Each seeded RESET observation exactly matched
the SHA-256 of the observation recorded during earlier direct public play.
This is input equivalence, not model gameplay or a score improvement.

The private dataset `kunalsinghh03/arc3-public-development-inputs` contains only
those public practice versions, their metadata, and 31 pinned wheels fetched
from official PyPI releases. Every wheel digest was checked against PyPI.
Total wheel size is 43,744,928 bytes. Embedded upstream wheel licenses remain
intact. No credentials, model weights, evaluation-game files, solutions or
agent recordings were uploaded. Game implementation files were copied as
runtime assets, not read by the reasoning agent.

The first control push, which still attached the competition datasource, was
rejected before creating a runnable version because the compute account had
not accepted its rules. No account enrollment or rule acceptance was performed.
The public-only dataset removes that datasource dependency. Input-access
validation does not independently certify compliance with account rules.

The dataset upload CLI initially failed saving relative-path upload state on
Windows after staging archives. A native absolute Windows path succeeded;
the dataset then reported ready. CPU execution verified its unpacked layout
and full asset hashes before the GPU jobs were launched.

`scripts/kaggle_local.py --token-file access_token2 ...` and the equivalent
watcher option select the supplied compute token without replacing the default
`access_token`. The original official submission waiter still uses its original
credential and stops if that credential changes. Only filenames, never token
values, appear in provenance.
