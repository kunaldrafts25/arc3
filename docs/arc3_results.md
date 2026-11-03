# ARC3 results at competition close

Verified 3 November 2026, 09:25 UTC through the authenticated Kaggle API.
The final submission deadline was 2 November 2026, 23:59 UTC.

The best completed on-time official score is **28.45**, submission **57726784**.
The user associated it with `arc-hydra-general-learner/1`; the API verified the
score but did not independently expose that notebook-version linkage.
Submission **57751759** completed at **25.96**. It is not pending.
The latest competing leader at this check was Yi-Chia Chen @ Fields Model,
**75.56**. The target of 100, or a score above the competing leader, was not met.

## Final screen and submission decision

The exact final package, `arc-hydra-deadline-candidate/1`, completed substantive
model gameplay on all 25 public games within its hard two-hour notebook cap.
It scored **36.6019**, completing 84 levels and four games. Actual gameplay
lasted 4,935.117 seconds after setup and before saving.

At that same gameplay duration, the historical memory run scored **38.5342**
with 87 levels, and the prediction run scored **36.4446** with 86 levels.
The candidate recorded memory changes in 22 games. This was one stochastic
draw with different scheduling horizons; it establishes neither a causal
memory benefit nor unseen-game performance.

The predeclared promotion gate rejected the final screen. The watcher therefore
made **no new on-time official submission**. Evidence:

- [Equal-time comparison](../reports/arc3/deadline-candidate/comparison.json).
- [Completed watcher decision](../reports/arc3/deadline-candidate/watcher-state.json).
- [Frozen package manifest](../notebooks/arc3_deadline_candidate/manifest.json).

On 3 November, the user explicitly requested uploading the last notebook if
possible. Kaggle reported a post-deadline allowance and accepted exact version 1
as **57942215** at 09:27 UTC. Its initial status was **PENDING**. This is a late
evaluation, not an on-time competition entry. The read-only monitor writes the
current status to `reports/arc3/late-submission/state.json`; its result must be
reported separately from the competition-close result.

## Training outcome

The actual 27B LoRA pilot completed 40 optimizer updates on 158 examples.
Sampled validation loss fell from 0.766336 to 0.723652, with independently
verified adapter reload and serving effects. This was actual weight training.

In paired gameplay on five whole-game gradient holdouts, the base scored
**15.7143** with 12 levels; the adapter scored **5.3301** with seven levels.
Every adapted game score regressed. The adapter was rejected. The recorded
observer JSON race was reconciled against all ten actual transcripts, without
a GPU rerun. The original corrupt artifact and executed package were preserved.

See [reconciliation](../reports/arc3/qwen27-lora-gameplay/completed-reconciliation.json)
and [training selection](arc3_training_selection_2026_11_01.md).

Lower loss, more tools, simulator replay parity, and longer reasoning were not
accepted as substitutes for real gameplay or official scores. The remaining
learning and generalization gap is unresolved.
