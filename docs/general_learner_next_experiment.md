# Next experiment after official 28.45

The next isolated GPU experiment should test exact coordinate inspection on
the preserved flexible agent. The original recovery advisory is held back:
the 29 October replay audit below found that most of its prompts lack evidence
of repeated visible transitions. Recovery remains a hypothesis requiring a
more selective trigger and measured gameplay benefit. No GPU job is launched
by this document.

## What the completed run establishes

Development score 62.09, 147 levels, 11 full wins. Official submission 57726784
scores 28.45, a 3.58-point improvement over the previous official best. Official
game diagnostics are unavailable, so public failure classes are candidate
interventions rather than explanations of the official score.

At two hours the new run scored 42.99 versus the previous candidate's 48.29.
At six hours it had 61.06; the final two-plus hours added 1.03 points. Both
agent protocol and budget changed. A memory or strategy improvement is not
isolated. Persistent notes were actually used in all 25 games, with 244 updates.

## Candidate intervention

1. Add a compact progress monitor to the existing observation/tool pathway.
   Track actions and inference cost since level completion, repeated public
   observation/action transitions, and explicit model-recorded failed tests.
   A stationary screen alone must not trigger rejection: timing, deliberate
   waiting and hidden-state effects can be legitimate. Do not block legal
   actions or impose a universal action threshold.
2. On sustained stagnation, ask for one concrete representation or hypothesis
   revision and a discriminating probe. Consult existing memory before retrying
   a failed experiment. Require a changed condition to justify a repeat.
   Keep supported mechanics separate from uncertain goals and control modes.
   A context refresh should carry concise counterexamples and a next test,
   rather than simply repeat the same summary and route.
3. For supported dynamics, encourage shortest-path/permutation/constraint
   planning in Python before spending more environment actions. Existing
   optional simulator checks remain optional. Plans must use visible
   observations and actual boundary feedback. Do not equate fewer Python calls
   with fewer environment actions.
4. Evaluate a scheduling change separately. Prefer inference allocations that
   still produce progress or resolve uncertainty, with a minimum exploration
   allocation for difficult games. Do not use public game IDs, human baseline
   access or hidden-score feedback as the scheduler's decision rule.

The completed levels' ideal-efficiency development ceiling is 73.44 versus
62.09 observed; missing later levels account for the remaining 26.56 points.
Improving only action efficiency cannot reach 100 on this run's completion set.

## Evaluation that answers the question

- Preserve and rerun the original flexible candidate at a matched two-hour
  gameplay budget, then compare the recovery intervention with identical model,
  runtime, concurrency and readiness policy. Use multiple seeds when possible.
  Compare completions, action efficiency, stalled-level actions, tokens and
  time to completion, not only a single final score.
- For CPU functional checks, generate simple puzzle families with varied
  controls, goals, modes and delayed effects. Split by mechanics families,
  not by starting board. Test that the monitor does not suppress a legitimate
  waiting strategy and that changing a prerequisite permits a repeated probe.
  Functional tests cannot establish that a language model solves these games.
- Use official evaluation only after a candidate is concrete and verified.
  The inspected development games are not an unseen generalization holdout.
- Preserve an ablation of the added guidance/memory. Its use is observed but
  its causal benefit is not; simplify it if matched runs show a consistent cost.

## Compute

Fresh quota check found 1,192.259 unreserved free GPU seconds (about 19m52s),
paid scaling disabled. Reset is 31 October 2026, 05:30 IST. The remaining quota
is too small for the planned matched gameplay runs with the current startup
cost. Continue artifact analysis and CPU validation first. Do not launch a
multi-hour job against the remaining quota or use other accounts to bypass it.

No model-weight training has occurred. Training a policy or teacher-distilled
model would require family-separated data, adequate compute and a new held-out
evaluation. It is a separate experiment, not a guaranteed next-score increase.

## Replay audit and revised decision, 29 October 2026

`scripts/audit_recovery_replay.py` replayed the frozen 15,476 public actions
through the offline observation/action API. All 25 games reproduced their
recorded completed-level counts and per-level action counts. This is aggregate
parity, not proof that every pixel matched the original run: original frame
hashes are unavailable. Decision boundaries are approximated by positive
generation-token charges; no-action decisions are absent from the recording.

The existing recovery monitor would emit 257 notices (128,046 characters).
252 notices have no repeated visible transition in their evidence window.
123 precede later success on that same level, including 38 within 32 actions
of completion. These are retrospective observations, not a counterfactual:
a notice might help or hurt, and a long successful level can still waste actions.
Only five notices include a repeated visible transition; full-frame changes
such as counters may conceal repetition. The broad trigger should therefore
not be promoted simply because the CPU integration passed. Retain the frozen
candidate for provenance and test a selective trigger separately if justified.

Exact inspection has a concrete motivating trace defect (incorrect run-length
endpoints) and a completed CPU gate, but still lacks GPU gameplay evidence.
Its next test must use the original account with the competition attachment,
preserve the same model/runtime and compare completions and action efficiency.
The official comparison of the preserved flexible agent is already accepted
as submission 57751759 and was still PENDING at 06:29 UTC on 29 October.

The authenticated official leaderboard at that check was led by Yi-Chia Chen
@ Fields Model at 75.56. Our best completed official result remains 28.45.
Deadline remains 2 November 23:59 UTC (3 November 05:29 IST); CPU/GPU runs must
finish within nine hours with internet disabled. These are separate from the
original account's development quota: 1,192.259 free RTX seconds remain until
31 October 00:00 UTC, and paid scaling is disabled.

The official [accelerator guidance](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview)
explicitly limits RTX to notebooks attached to ARC-AGI-3. This is consistent
with the two unattached development jobs receiving no GPU driver; it does not
prove the backend's exact failure mechanism. The historical public-input
builder now refuses that configuration. Do not use additional accounts to
bypass quota. No additional GPU job or duplicate submission was launched.
