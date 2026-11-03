# ARC3 prospective-evidence experiment, 29 October 2026

Update 1 November 07:36 UTC: exact control/1 is COMPLETE at public 31.5812675,
81 levels/four wins, with all 25 model-gameplay lifecycles verified. Gameplay
lasted 4,819.35 seconds within the total two-hour cap. The original local observer
exited; its stale state was preserved and the completed control reconciled without
relaunch. Recovery observer child PID 11468 accepted prediction candidate/1 at
07:31:56 UTC, independently confirmed QUEUED. Fresh resources before that launch:
101,311.34 free seconds, no reservations or active shared GPU notebooks, paid
scaling disabled. The candidate retains the hard 7,200-second timeout. Original
frozen packages/plan remain intact; the explicit recovery launch window is now
1 November 18:00 UTC. Consult live runner-state and exact launch journals, never
restart from the old observer record. Fourteen recovery/resource checks passed.
No official submission or candidate improvement has been established. New public
source research and control diagnostics are described in
`docs/arc3_research_update_2026_11_01.md`.

Update, 1 November IST: user explicitly resumed the work and requested a hard
two-hour development cap. Both matched notebooks now use 7,200 seconds total,
including startup and the 600-second finalization reserve. The external Kaggle
timeout is also 7,200 seconds, and longer development launch requests are rejected.
Two sequential runs use at most four hours total. Twelve focused cap/resource
checks passed. Fresh quota is 30 free hours with zero used/reserved; paid scaling
is disabled. The resumed runner checks shared jobs before each launch and retains
the ARC2 quota floor. Older paused and 12,000-second development descriptions are
historical; inspect live state and exact launch journals for current progress.

Control-state update: the goal service returned `paused` during the final check.
The confirmed idle V2 background waiter was stopped before any GPU launch.
Live runner state is `goal_paused`; older rearmed/ARMED descriptions below are
historical. The objective remains unmet and no new official submission was made.

## Latest state: host V2

The latest official verification, 12:04 UTC / 17:34 IST, still gives leader 75.56,
best completed official 28.45 and submission 57751759 COMPLETE at 25.96. The full
objective remains active and unmet. No new official submission or GPU job occurred.

A targeted regression reproduced a V1 defect: an evidence write failure after
an executed action raised instead of returning the action result. The idle V1
resource waiter was stopped before any launch. V2 now preserves the original
handler's result or error exactly once, reports prediction evidence unchecked
when bookkeeping fails, and keeps ordinary tools working with a corrupt optional
store. A level change without a completion flag is excluded without disabling
tools. V2 also logs full forecasts before dispatch and measured outcomes afterward.

Final Linux CPU gate `kunalsinghh25/arc-hydra-prediction-cpu-probe/3` is COMPLETE:
12 prediction cases, eight base cases and 16 prompt combinations. The final local
suite passed 84 tests. Gate versions 1 and 2 remain separate preserved artifacts.

V2's complete real-observation replay reproduced all 15,476 frozen actions and
25 game-level/action-count totals. All 25 observation digests match the V1 CPU
replay, not necessarily the unavailable original GPU-frame hashes. The independent
event audit found zero inconsistencies: 1,593 frozen forecasts and dispatches,
1,545 checked resolutions, 48 exclusions, no pending tickets. Of those forecasts,
1,009 predicted some disagreement; these are naive programmatic proposals, not
model adoption or useful decision-making. See `reports/research/prediction-real-replay-v2/`.
An earlier Windows replay interrupted by denied atomic replacement during live
sidecar inspection is preserved separately and is not counted as complete.

The frozen V2 comparison is in `notebooks/arc3_prediction_ablation_v2/`; its guarded
background waiter is rearmed for the October 31 refresh. Inspect live process and
state files before any action. The original V1 packages and plan are preserved.
The full-budget V2 final candidate is `notebooks/prediction_candidate_v2/`, with
32,400 seconds and no development gameplay cap. No automatic promotion/submission
is armed. The runner collects model-origin adoption and serving audits after real
gameplay; neither tool availability nor passing forecast checks is a promotion rule.

The new fixed-trajectory allocation oracle scores 53.2257 with perfect future
information at the observed two-hour charge of 4,211,289 tokens, versus 42.9868
observed. Conservative and optimistic 500-token rounding bounds coincide there.
All observed final completions lie within prefixes costing 10,020,517 tokens,
versus 15,203,434 total charges. No allocation of these existing prefixes exceeds
62.0947. Free interruption and future completion knowledge make this an offline
opportunity bound, not a deployable scheduler, achievable policy score or hidden
estimate. It motivates practical allocation research while retaining the need for
new successful trajectories. See `reports/research/arc3-allocation-bound/`.

The older details below describe the initial V1 experiment where named. V2
supersedes it for future gameplay, and model adoption/score benefit remain unproven.

Official verification at 10:21 UTC / 15:51 IST: leader Yi-Chia Chen @ Fields
Model remains 75.56; our best completed submission remains 57726784 at 28.45.
Submission 57751759 is COMPLETE at 25.96. No duplicate submission is authorized
by this experiment. Deadline remains 2 November 23:59 UTC / 3 November 05:29 IST.
The full goal remains active and unmet.

## Implemented and measured

`hydra/prediction_host.py` owns forecasts and measured outcomes outside the
model's Python process. It measures fixed cells, color counts and color bounding
boxes from supplied public frames. It freezes forecasts before ordinary actions,
checks only a matching next single action, preserves counterexamples, and exposes
durable feedback through RPC and the next user prompt. No user-supplied outcome
or executable measurement callback is accepted. These measurements do not establish
object identity, a Markov state, a mechanics rule or a goal.

Ordinary batches retain their original behavior. A different action/batch, stale
observation, refusal, reset, skipped step or terminal boundary cannot certify a
forecast. Reset invalidates even same-level claims. A new game uses a separate
store. An in-flight interrupted action is explicitly uncertified; a completed
action's evidence is saved before the sandbox can time out.

Private offline CPU notebook `kunalsinghh25/arc-hydra-prediction-cpu-probe/1`
is independently confirmed COMPLETE. Nine actual Linux sandbox/ToolAgent cases
passed, together with eight original flexible-agent mechanical cases and 16
rendered prompt combinations. The final focused local suite passed 74 checks,
including executed development-versus-official budget logic and resource guards.
No ARC3 weights changed.

`scripts/audit_prediction_replay.py` replayed all 15,476 frozen public actions.
All 25 games matched the recorded completed-level counts and per-level action
counts. It froze 1,593 forecasts during the first 64 recorded actions per game:
1,545 were checked and 48 excluded at boundaries. These are actual ARC public
observations, but the actions were fixed, not chosen by a new policy. Original
frame hashes are unavailable, so aggregate parity does not prove original pixel
equality.

The diagnostic generated two deliberately naive proposals from past observations:
unchanged selected color features, or repeating the last observed same-action
feature difference. Neither is supplied the real mechanics. Both were refuted
in 743 checks. The repeat-effect proposal matched selected features in 238 checks,
was refuted in 785 and abstained in 522. There were 1,443 transitions with changing
selected features; even those features can include counters or unrelated objects.
This establishes the need to handle an absent correct candidate. It establishes
neither useful hypothesis generation by our model nor gameplay improvement.

Evidence and fingerprints are in `reports/kaggle/prediction-cpu-probe-v1/`,
`reports/research/prediction-real-replay/diagnostic.json`, and the source manifests
inside the separately staged notebook packages.

## Research judgment

The host mechanism is a contained experiment, not a commitment to a large simulator
architecture. The strongest alternative to investigate alongside it is preserving
useful interaction history and improving effective inference throughput, rather
than adding instructions. An independently published competitor research note
reports substantial stochastic variation, little benefit from prompt additions,
benefit from retained history, and serving-queue problems. Scores/configurations
are withheld, so this is a hypothesis source, not a reproduced ablation:
https://makaroff.ai/ (inspected 29 October).

The newly downloaded public `serve.log` is 11,030,664 bytes. Its SHA-256 is
`77c05b31552cf43d43bee2cb4bc0952183ad3cb910c95ab08eec11dbaf8cac84`.
`scripts/audit_arc3_serving.py` parsed all 7,964 timing lines without failure;
7,961 requests entered during gameplay. Weighted prompt-prefix reuse is 93.748%.
Server queue delay is p50 1.51 ms, p90 2.8 ms, p99 4.761 seconds and maximum
14.966 seconds. Of 6,317 prompts longer than 62,000 tokens, 33 reused fewer than
10,000 cached tokens. Completed server responses account for 15,245,063 tokens,
about 506.30 tokens/second over the 30,110.76-second gameplay window. Benchmark
charges account for 15,203,434; the 41,629-token difference is not assigned a cause.

This weakens the hypothesis of a broadly broken prefix cache or persistent
server-queue bottleneck in this public run. Server timing excludes harness
admission waiting. Decode event samples have median seven running requests and
90th percentile ten, but event weighting is not wall-time weighting or GPU
utilization. Logged initial-prefill interval union covers about 4,204 seconds;
this is not exact device busy time. All benchmark uncached-input counters were
zero despite real prefill work, demonstrating why those counters alone are
uninformative. Full audit: `reports/research/arc3-serving-audit/general-learner-v1.json`.

Franzen's original primary write-up reports 27.89 official for the source stack
and already combines larger context, retained reasoning/functions, animation,
undo, prefix caching and adaptive admission. It reports no clear benefit from
several more prescriptive verification/memory variants. The existing stack already
contains those core changes. Recommending them again is not a new intervention:
https://github.com/da-fr/arc-agi-3-solution/blob/main/WRITEUP.md.

The reviewed primary work remains relevant with its restrictions: Tycho separates
transition fit from useful action choice; WorldCoder assumes a supplied goal and
symbolic state; EMPA supplies some object roles and a restricted termination
language. Their reported results do not validate our offline model's proposals.

Sources:

- https://arxiv.org/html/2607.28287
- https://arxiv.org/html/2605.05138
- https://arxiv.org/html/2402.12275
- https://arxiv.org/html/2107.12544

## Shared compute and concrete next evaluation

Fresh original-account quota remains 402.27 unreserved GPU seconds, paid scaling
disabled. No ARC3 submission allowance remains today. Quota refresh is 31 October
00:00 UTC / 05:30 IST. The shared ARC2 development notebook was COMPLETE at the CPU
gate launch. Its official job and observer are preserved.

The frozen plan `reports/arc3/prediction-ablation/plan.json` defines a development
comparison of exact inspection versus exact inspection plus predictions, all 25
public games, identical original model/draft/runtime/scheduler, and 7,200 seconds
after readiness. A 12,000-second whole-notebook safety limit includes startup and
finalization and is also sent as the external Kaggle session timeout. Notebook
titles are checked against their requested slugs and the original RTX shape is
explicitly pinned. Sampling is stochastic; one pair cannot establish a small causal gain.
The separate final-agent package retains 32,400 seconds, including startup and
600 seconds for finalization; development packages must not be submitted.

`scripts/run_prediction_ablation.py --run` waits until the quota refresh. Before
each launch it checks original-account free quota, reservations and recent active
GPU notebooks, and retains at least 10,800 free seconds for shared ARC2 work. It
requires enough quota for both remaining experiments at their full safety budgets.
It waits when another GPU development job is active. No quota is reserved now.
The ARC2 floor is a courtesy guard, not exclusive allocation or a guarantee about
the other chat's future needs. A `cancel.requested` file in the plan directory
stops future activity; it does not cancel another job.

Each launch has an exclusive intent journal before mutation. Uncertain outcomes
stop for reconciliation; no launch is retried blindly. The runner observes exact
versions, downloads diagnostics and analyzes actual gameplay after completion.
It performs no official submission, no automatic promotion, no paid scaling and
no other-account work. It must stop launches by 1 November 06:00 UTC. A local
background runner requires this computer to remain available.

After the comparison, inspect model-authored alternatives, actual adoption,
counterexample-driven revisions, per-game completions/action efficiency and
inference/time cost. A tool that is unused or mostly checks irrelevant features
does not justify promotion. Then evaluate the strongest concrete candidate at the
full budget and use the authorized official allowance when appropriate. Completion
still requires an official result of 100 or strictly above a freshly verified leader.
