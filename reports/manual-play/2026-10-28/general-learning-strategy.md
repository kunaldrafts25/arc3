# Learning an unfamiliar game from interaction

The user's requirement is a transferable learning procedure. A game ID, starting
board, color convention or memorized solution must not determine the strategy.
The agent must infer controls, entities, dynamics and goals from observations,
then update those beliefs as the game changes. No claim of understanding every
possible game follows from public-game performance.

## Evidence collected directly

I ran the public games through Arcade's observation/action API, without reading
their implementation or accessing hidden environments. All 25 public games were
reset/observed and received at least two chosen gameplay actions. There were
**99 gameplay actions**, including deeper conditional-rule tests. Two levels of
one game were completed; no whole game was won in this session. This is an
initial intervention sweep, not 25 completed playthroughs or an official score.
The action rationales, observations, deltas and images are preserved locally;
`session-summary.json` gives counts and the raw observation-file hash.

Observed lessons:

- Visual prominence did not reliably identify the controlled object. In several
  scenes, the initially suspected actor stayed fixed while another object moved.
- Some valid actions changed only a corner/edge counter. Other clicks produced
  no change at all. Valid input does not establish that the intended object was
  manipulated, or that no internal mode changed.
- Clicking a visible slot could be inert while clicking a separate arrow/button
  changed the scene substantially. Ground controls separately from game objects.
- A learned mirrored movement relation supported a 16-action route and actual
  first-level completion. On the next level, RIGHT moved the reflection axis
  while the source object stayed fixed. SPACE changed marker pixels; subsequent
  RIGHT moved the source object with the axis fixed. A control-mode variable
  explained the apparent contradiction. A mode-conditioned reflection model
  then supported another route and actual second-level completion.
- A separate binary-cell puzzle supported repeatable toggle behavior. Two
  proposed transformations did not advance its level. This does not independently
  refute those transformations: goal interpretation or completion triggering
  could also be wrong. Mechanics evidence and goal evidence must remain separate.

These are diagnostic examples, not game-specific rules for deployment. In
particular, colors and action semantics observed in one game are not transferred
as facts to another game.

## The general learning loop

1. **Ground the interface.** Enumerate legal actions; determine coordinates,
   selection/drag/confirm semantics, time behavior, counters and reset effects.
   Begin with small interventions, choosing real occupied pixels or visible
   controls when possible. Keep several explanations for an inert action.
2. **Build a revisable state representation.** Track candidate objects and
   relations, controllability, camera/viewport changes, selected object/mode,
   inventory, motion phase and remaining resources. Use segmentation as evidence,
   not an assertion that each color component is one semantic object. Add state
   variables when otherwise identical situations produce different responses.
3. **Separate mechanics and goals.** Maintain a few competing causal rules and
   candidate completion conditions. Record their scope, assumptions, supporting
   transitions, counterexamples and untested cases. A reliable movement model
   does not establish what the player should achieve.
4. **Choose a discriminating experiment.** Predict what each leading hypothesis
   would produce. Prefer an action whose outcomes distinguish them, with useful
   progress, low resource cost and recoverability. Opposite actions, repeated
   clicks, selection changes and isolated interactions are experiments when
   their expected outcomes have been stated first.
5. **Compare predictions with actual observations.** Distinguish actor changes,
   camera motion, control markers, animation and resource consumption. Preserve
   raw observations when abstractions hide a contradiction. Count a mismatch as
   evidence about a particular claim, rather than discarding the whole model.
6. **Diagnose the failure at the right level.** Incorrect movement can mean bad
   dynamics, wrong actor, unobserved mode, collision or timing. Correct mechanics
   without progress can mean an incorrect goal or missing prerequisite. An
   apparent no-op can mean an invalid hit location or a selection interaction.
7. **Plan at the supported scope.** Use short direct actions or search when the
   relevant mechanics/goal are sufficiently supported. Optional executable
   models help where they simplify planning; constructing a complete simulator
   is not a prerequisite to playing. Check new outcomes and shorten plans when
   evidence is weak or consequences are hard to reverse.
8. **Transfer hypotheses across levels and test them again.** Retain useful
   rules, but re-check active mode, new objects, goals and constraints. New-level
   initialization can change control state while preserving the same physics.
9. **Manage computation as well as moves.** Track action cost, remaining time,
   inference tokens and learning progress. Switch from repeated unsuccessful
   simulator repair to another experiment or representation when it is more
   informative. Our separate strict-planner benchmark regressed from 45.02 to
   33.18; verified execution alone is not sufficient for effective learning.

## Memory the agent needs

Use a compact, persistent evidence ledger rather than a long unstructured story:

| Field | Meaning |
| --- | --- |
| Observation IDs | Actual before/action/after evidence |
| Claim type | Control, representation, mechanics, goal, resource or timing |
| Claim and scope | Conditional prediction; game/level/mode assumptions |
| Status | Untested, supported, contradicted or unresolved |
| Supporting/contradicting IDs | Evidence behind the current status |
| Missing variable | Possible selection, camera, phase or inventory aliasing |
| Next experiment | Competing predictions, expected information and cost |
| Current plan | Preconditions, predicted effects and stopping conditions |

The host should preserve evidence and compact notes through context drains. The
model should not mark a belief true merely by repeating it. Likewise, a counter
change should remain a resource observation instead of being mistaken for goal
progress. Confidence values require calibration; unsupported numeric certainty
is less useful than explicit evidence and unresolved alternatives.

This ledger/instruction change is a proposed next intervention, not yet installed
in the running candidate. Existing frame diffs, segmentation, history, retained
functions and optional checked planning should be reused. Add only missing
capabilities and measure their cost. The current candidate's model weights remain
frozen; direct researcher play is not model-weight training.

## How to evaluate transfer

Continue deeper play of all 25 games to expose mistakes in this procedure. Public
games already inspected cannot become a clean unseen holdout. Evaluate the
learning process on newly generated mechanics families with different layouts,
colors, control mappings, modes and goals; separate families before producing
any training data. Inspect first-contact learning, action efficiency, recovery
from wrong goals and rule changes, not final replay of a memorized solution.

After integration checks, compare the complete agent on equal model/runtime/time
budgets and inspect per-game failures. Use official submissions, within the daily
allowance, to establish hidden performance. The target remains official 100 or
strictly above the latest competing leader; this manual session does not prove it.
