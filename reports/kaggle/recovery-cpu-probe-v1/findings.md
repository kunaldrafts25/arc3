# Recovery advisory CPU integration gate

Exact cloud version `kunalsinghh25/arc-hydra-recovery-cpu-probe/1` is COMPLETE.
Downloaded `recovery-probe.json` reports four actual-host cases passed:
cross-decision recovery rendering/event recording, same-step cooldown,
level-boundary clearing and per-game isolation in a shared directory.

The same installed bundle also passed the eight original mechanical cases,
16 rendered prompt combinations and nine study-memory/host cases. The recorded
installed source hashes are in the three extension reports. Upload hashes were
recorded before cloud completion, and packaging checks the current source and
CPU package against them before embedding the installer.

115 local tests passed, including six new cases for delayed effects with
unchanged pixels, changed prerequisites, boundaries, stale/truncated histories
and notice cooldown. This is synthetic functional/integration validation, not
language-model gameplay evidence. No GPU quota was consumed by this gate.

The advisory observes a bounded suffix of public observation history. It emits
after at least 64 recorded current-level transitions, at most once per 32 new
environment steps. Exact full visible-grid hashes identify repeated visible
transitions; they cannot distinguish hidden state and may miss loops where a
HUD counter changes. These limitations are explicit in the notice. No actions
are refused, no automatic resets occur, and the model still chooses its tests.
The monitor is scoped per game and cleared for a new level; its checkpoint is
in host memory, not certified causal knowledge.

The 64/32 thresholds are experimental engineering choices, not tuned or proven
optimal. Telemetry will measure notice frequency and downstream decisions.
Effect on score, useful waiting and reasoning efficiency requires gameplay.

Packaged but NOT launched:

- `notebooks/recovery_candidate`: general learner plus this advisory.
- `notebooks/flexible_extended_control`: preserved flexible optional-planning
  agent with the longer wall budget, without study/recovery additions.

Both default to 32,400 seconds including startup and a 600-second finalization
reserve, all 25 public games. This also tests whether the earlier 48.29 flexible
agent improves simply with more compute. The previous 62.09 study run provides
another descriptive comparison, subject to startup/runtime and stochastic
differences. Model checkpoints and serving stack remain fixed.

Current free quota cannot support either full job. Recheck quota and status
before launch after the 31 October 05:30 IST reset. Do not start both by assuming
quota refreshed, change accounts, or enable paid scaling. Preserve official
submission 57726784 at 28.45 until a better completed official result exists.
