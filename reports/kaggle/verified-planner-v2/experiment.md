# Full public comparison after functional/adoption pilot

Control: `kunalsinghh25/arc-hydra-duck-m2-baseline/3`.
Candidate: `kunalsinghh25/arc-hydra-verified-planner/2`.

Both arms: all 25 public games, one pass, the original Intel AutoRound target
and draft, original v2.5.3 serving stack, original scheduler, and 7,200 seconds
after confirmed model readiness. Both use full public diagnostics; the candidate
also retains its lightweight lifecycle/mechanical event evidence. Notebook
timeouts are 12,000 seconds. No official submission and no weight training.

Control source is byte-identical to the completed baseline/2 upload. Candidate
helper/installer hashes are unchanged from the completed five-game GPU pilot
and passed CPU gate. It changes action enforcement, system guidance and lifecycle
instrumentation, so this compares complete agent configurations rather than
isolating one mechanism. Sampling is stochastic and seeds are not paired.

Collect final analysis, per-game scores/levels, completion curves, model tokens,
mechanical helper adoption, replay failures and prospective mismatches. Confirm
all games have substantive model gameplay. The older five-game pilot control's
timer included startup and cannot establish a quality gain for this candidate.

Promotion requires the complete evidence, not early snapshots or a successful
upload. A single public comparison does not prove hidden score improvement or
completion of the official >71.48 objective.

After both exact jobs finish, download their `benchmark.json` and model summaries
into their versioned report directories. Run the substantive-gameplay analyzer
on each, then compare the raw histories:

```powershell
.venv/Scripts/python.exe scripts/compare_duck_runs.py reports/kaggle/duck-m2-benchmark-v3 reports/kaggle/verified-planner-v2 --output reports/kaggle/verified-planner-v2/comparison.json
.venv/Scripts/python.exe scripts/analyze_verified_events.py reports/kaggle/verified-planner-v2
```

The comparison requires 25 unique matching games, single-pass finished outputs,
substantive model gameplay, consistent action accounting, matching level counts
and game weights, and elapsed durations within 120 seconds. It reconstructs
tokens including terminal no-action generation, hashes both raw inputs and emits
per-game deltas. Startup/readiness alignment still requires separate source/log
inspection; elapsed-time matching alone cannot prove it. No automatic promotion
or statistical confidence claim is made from one stochastic pair.
