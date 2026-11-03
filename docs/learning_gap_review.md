# Capability gap review, 29 October 2026

The main research hypothesis is that the agent needs better correction of its
own state, mechanics and goal assumptions. Giving the existing reasoning loop
more advice or time has not established that capability. This review derives
from our implementation and recorded gameplay; it makes no new score claim.

## Evidence and its limits

The best completed official result is 28.45. Submission 57751759, the preserved
flexible candidate, is still pending at this review. The last authenticated
leaderboard check was 75.56. Public practice scores and official scores use
different environments and cannot be subtracted to diagnose a hidden failure.

The general learner completed 147 levels and 11 games, scoring 62.09 on the
25 public development games. Its completed-level ceiling under perfect action
efficiency is 73.44. Recovering the 11.35-point public efficiency deficit alone
cannot solve its missing later levels, and says nothing quantitative about the
separate official leaderboard gap. Both completion and efficiency need work.

`scripts/analyze_learning_gaps.py` measures 5,182,917 of 15,203,434 generated
tokens (34.09%) after the last completion on games that remained unfinished.
That is unsuccessful tail expenditure, not a proof that every token was wasted.
The same audit finds 298 changed note versions marked supported, 119 marked
hypothesis, and zero marked contradicted. There are implicit rewrites and three
supported-to-hypothesis changes; no explicit contradiction does not mean no
correction occurred. The mechanism currently checks that evidence step IDs
exist, while the model chooses what those observations mean and whether a rule
is supported. Persistent prose is therefore weaker than a checked causal model.

Exact-inspection work addresses an observed arithmetic defect in a generated
geometry helper. Broad recovery work has weaker support: 252 of 257 replayed
notices lacked repeated visible-transition evidence. Neither CPU integration
success nor actual memory use proves better gameplay. A previous strict planner
scored 33.18 versus 45.02 for its flexible control in one stochastic comparison;
mandatory full simulation is not justified by our evidence.

## What a stronger learning loop needs

1. **Measured state.** Separate raw pixels from proposed objects, roles, control
   mode and resource indicators. Use exact geometry helpers and actual motion
   to test identity. A component is an observation, not automatically the actor
   or goal. Keep alternatives when two interpretations fit the same picture.
2. **Executable, scoped predictions.** For an important uncertain action,
   record what each candidate explanation predicts about a small observable
   feature, then compare with the returned observation automatically. Partial
   predictions are useful; a complete simulator is optional. A passed check
   supports that prediction in that context, not an entire universal rule.
3. **Separate goals from dynamics.** When motion predictions succeed but no
   level completes, consider a mistaken goal, incomplete dependency or missing
   trigger. Repeatedly changing the movement model cannot resolve every failure.
   Keep small goal alternatives and test preconditions when recoverable.
4. **Directed experiments.** Choose an action on which the leading explanations
   disagree, with low action cost and useful progress if possible. Avoid probing
   irrelevant uncertainty. Deterministic local search chooses probes only when
   predictions are available; otherwise the reasoning model proposes them.
5. **Compile supported structure.** Instantiate navigation, permutation, toggle,
   geometry or constraint solvers only after their assumptions fit observations.
   Let code do arithmetic and combinatorial search; let the model propose the
   representation and revise it. Check short execution prefixes and actual
   boundaries without removing efficient ordinary action batches.
6. **Repair the failing layer.** A geometry disagreement calls for measurement;
   a failed prediction calls for missing state or rule revision; predicted
   effects without completion call for goal revision. A generic reminder at
   every long level does not identify which problem to fix. Preserve observed
   counterexamples through context trimming, alongside successful mechanics.

This is adaptive control and experimental reasoning in mostly single-agent
partially observed puzzles. Minimax or opponent game theory applies only when
the environment provides an actual strategic opponent or justified adversarial
model. Search and mathematics operate on an inferred model; they cannot certify
that its state or goal assumptions match the environment.

## Priorities and experiments

Keep the pending official comparison unchanged. Exact-coordinate inspection is
the next contained GPU ablation. The larger capability experiment should add
an optional prediction ledger and automatic outcome feedback, starting with
small features and explicit counterexamples. Avoid another long universal
prompt or forcing every action through a full simulator. Baseline ordinary
action batching remains available while the model is uncertain.

Evaluate the new loop first on procedurally varied mechanics: random action
labels, object colors, layout, control modes, delayed effects, prerequisites and
goals. Include visually identical states with different histories and deliberately
incorrect hypotheses. Split evaluation by mechanics families, keeping some
families outside development. Measure next-effect prediction accuracy,
correction after contradictions, cost to identify a control/goal, completion,
environment actions, inference tokens and wall time. A solver-specific unit
test suite or familiar public set cannot establish unfamiliar-game learning.

Then compare matched-budget real gameplay with the same model, serving stack
and scheduler, and officially evaluate the strongest validated candidate.
Report actual gains rather than rewarding memory updates, tool availability,
long reasoning or confident rule descriptions. Existing public games are
development evidence; synthetic family holdouts are a diagnostic, not the
official hidden benchmark.

Model capability remains a plausible limitation. Our current stack already
uses a substantial quantized model, a draft model and optimized serving. A
different or larger model needs a representative matched test and a hardware
fit, not a reputation-based switch. A second critic sharing the same wrong
state interpretation can amplify the error; use targeted independent proposals
with explicit counterexamples only as an ablation. Full pretraining is outside
the current time/resources. Teacher-distilled small-model or adapter training
could target rule discovery, correction and tool use on randomized families,
but needs compliant teacher/data access, family-separated evaluation and measured
transfer. ARC-2 grid LoRA results do not establish ARC-3 game-playing gains.

Resource allocation should respond to measured learning progress as well as
level completions: predictive contradictions resolved, a control grounded or
a necessary prerequisite discovered. Those intermediate signals must be checked
against later success; otherwise novelty rewards counters or attractive but
irrelevant discoveries. Keep an exploration allocation for hard games and
budget a fresh representation attempt when a long trajectory stops learning.
This is a separate ablation, not a guaranteed saving of the observed tail tokens.

The original account has about 20 minutes of free RTX development time left
until 31 October 00:00 UTC. Preserve it until a short run answers a concrete
question. Do not bypass quota with additional accounts or enable paid scaling.
The final submission deadline is 2 November 23:59 UTC. A large new architecture
has material schedule risk; prioritize the smallest change that tests the
missing capability, then expand only if the measured benefit supports it.
