# Completed five-game verified-planner pilot

Exact notebook `kunalsinghh25/arc-hydra-verified-planner/1`: COMPLETE.
All five games have verified model gameplay. Final public mean **15.9206**,
10 levels, zero full wins and 343,178 action-accounted generated tokens.
Lifecycle ended `run_finished`, with no error and five model-gameplay games.

The actual installed source hashes match the passed Linux CPU gate. Mechanical
events were persisted for all five games: 81 executed probes, 51 replay checks,
29 passing checks, 15 retrospective counterexamples, six replay errors, and
27 plan calls reporting 158 executed plan actions. Three plans stopped on a
prospective prediction mismatch. All 51 replay checks used **abstract-state**
encoders; none establishes full-grid model correctness. Counts cover completed
sandbox calls and are not interchangeable with scorer action counts.

The six replay errors include one uninformative abstraction, one model-written
type error, three diagnostic ValueErrors and an undefined `BTN3` variable in a
retained helper. These are evidence to inspect rather than reasons to silently
relax the checker. BP35 used probes without a completed plan event. Do not claim
uniform adoption of every helper across every game.

The historical five-game baseline scored 11.3976 with seven levels, but its run
began at 14:35:39 UTC and the model's readiness markers appear only around
14:44:07–14:44:23 UTC. Its 900-second timer therefore included substantial model
startup. Its 135,986 accounted tokens versus this pilot's 343,178 also make a
direct score-gain claim inappropriate. The pilot proves integration and actual
helper use, not a reliable improvement in gameplay quality.

A fresh full comparison is now launched: original baseline version 3 versus
verified planner version 2, all 25 public games, one pass and 7,200 seconds
after readiness per arm. Both use the original model/runtime and full public
diagnostics. The planner's helper and installer code are frozen from this pilot.
One stochastic run per arm cannot establish a precise causal effect or predict
official hidden scores. No official entry is made from the pilot.

## Later transcript audit: conflicting user guidance

The two inspected transcripts repeat incompatible user instructions on every
turn: BP35 has 34 such user prompts, VC33 has 37. They tell the model to prefer
unchecked batches and allow repeated action calls despite the system contract.
VC33's reasoning explicitly notes the conflict. This establishes a prompt defect,
not its quantitative score effect. See `prompt-audit.json` for hashes/counts.

The source installer now produces extension v2, rewriting both user and system
prompts. Local relevant checks: 27 passed. Exact offline CPU probe version 4 is
COMPLETE with seven mechanical checks and 16 rendered user-prompt combinations
passing. The mechanical checker and installed sandbox hashes are unchanged.
No new GPU candidate has been launched from this fix. Full comparison notebook
version 2 retains the earlier extension v1, preserving its uploaded configuration.

Other observed issues remain follow-up evidence: VC33 used an unsupported
`max_steps` value once and retained a predictor referencing an ordinary global
that was not retained. BP35 used exploratory actions without a completed plan,
including one second-probe refusal and an unrelated model-written dictionary-key
error. Do not attribute every error or zero to the prompt conflict.
