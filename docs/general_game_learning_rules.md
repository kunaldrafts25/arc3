# Draft rules for learning unfamiliar interactive games

Status: research-backed draft with direct public-game experiments. This is a
general learning procedure, not a guarantee of solving almost all games, and is
not yet installed in the running Kaggle candidate. Select methods from observed
structure; never dispatch on game ID, a memorized board or fixed color meanings.

## 1. Establish the interface and separate uncertainties

Track five separate questions: what is controlled, what state matters, what each
action does, what completes the level, and what resources actions consume.
Legal-action availability answers none of the other questions by itself.

Start from observations and small interventions. Use actual occupied pixels or
visible controls for clicks, but distinguish a control from the object it affects.
Selection, click-to-place, dragging, confirmation and reset are hypotheses until
tested. An inert input can mean a missed hit, collision, wrong mode, missing
prerequisite, delayed effect or genuine no-op.

## 2. Build the smallest state that predicts the relevant effects

Use objects, slots, relations, orientation, active selection/mode, inventory,
camera, time/animation phase and resources as needed. Color components provide
measurements; they do not define semantic objects or stable identities. Group
parts that move together, and keep identically colored objects distinct when
their roles differ. Preserve raw observations for diagnosing abstraction errors.

Identify counters from their behavior. Keep resource changes separate from
gameplay changes. Do not discard border pixels globally: goals and controls can
also be on an edge.

## 3. Maintain competing, conditional explanations

Record a few useful alternatives for mechanics and goals. Each claim needs its
scope, preconditions, supporting transition IDs, contradictory transition IDs
and unresolved cases. Distinguish untested, supported and contradicted claims.
Do not invent precise confidence numbers without calibration.

When an old prediction fails, first check active mode, selected object, timing,
camera, boundaries, collision and prerequisites. Add a missing state variable
when it explains the contradiction; do not immediately abandon every old rule.
Correct dynamics without completion can mean a wrong goal or missing trigger.

## 4. Choose experiments that change the next decision

Before a probe, state which hypotheses predict different observable outcomes.
Prefer useful progress, informative differences, small action/time cost and
recoverability. Information for an irrelevant detail is less valuable than
testing a dependency that blocks a promising route.

Useful experiments include opposite actions, repeated actions, selection/mode
changes, the same action in another context, and changing one input at a time.
Compare the predicted relevant effect with the actual effect. Avoid repeating
the same failed experiment unless conditions changed or repetition itself tests
a temporal/stochastic hypothesis. Ordinary actions remain available while a
complete simulator is unknown.

## 5. Select mathematics after testing its assumptions

| Observed structure | Candidate method | Required checks |
| --- | --- | --- |
| Traversal through obstacles | BFS, Dijkstra or A* in configuration space | Actor footprint, stride, intermediate collision, doors and modes |
| Rigid shapes/contact targets | Discrete rotations/reflections, geometry, affine constraints | Group connected parts; measure rotation anchoring and contact/collision |
| Tokens moving through fixed slots | Permutation/cycle algebra and abstract search | Conservation, inverse actions, composition and overlapping controls |
| Binary switches | Linear algebra over GF(2) | Repeat twice restores state, effects are context-independent, tested actions commute |
| Symbolic prerequisites and ordering | Constraint propagation, SAT/SMT or bounded planning | Correct variables, transition clauses and independently supported goal |
| Hidden mode or time-dependent effect | Belief-state/finite-state/hybrid model | Same visible pose under different histories; distinguish delay from randomness |
| Large branching with a usable model | Beam search or MCTS | Model validity, useful evaluation/rollouts and bounded compute |
| Actual strategic opponent | Appropriate minimax/game-theoretic reasoning | Identify players, information, chance and objectives; do not invent an opponent |

Methods can combine. A navigation plan may depend on an unknown switch, and a
permutation puzzle can have several overlapping cycles. Independent-looking
controls may not commute. A solver finds a solution to its supplied model; it
does not establish that the supplied model or goal is correct.

## 6. Reduce search while preserving what matters

Track only goal-relevant token positions or relations when other details do not
affect transitions or completion. Keep omitted information available for checking
the abstraction. If different outcomes share one encoded state, refine it.

For GF(2), elimination gives a feasible solution when the validated model applies;
minimum-action selection can require additional null-space search. For A*,
shortest-path claims depend on the graph and heuristic. For a permutation model,
an abstract shortest plan is shortest within that model/action set, not proof
that every possible interaction was considered.

## 7. Execute at a supported horizon and learn from errors

Use short actions when consequences are uncertain; use longer efficient plans
when tested mechanics and goal assumptions support them. Optional executable
models can check replay and prospective outcomes. Complete simulation is not a
prerequisite to playing. Stop or replan on unexpected effects, invalidated
preconditions, unknown predictions or actual level/game boundaries.

Judge progress using actual completion feedback and resource consumption, not
just matching a chosen abstraction. A passing historical replay is consistency
with those observations, not proof of the goal or unobserved cases.

## 8. Preserve learning and control its cost

Keep a compact evidence ledger through context drains: current controls/mode,
supported mechanics, competing goals, unresolved dependency, next discriminating
test and guarded plan. Retain exact observations separately. Spend inference on
information that changes an action; avoid indefinite simulator repair or lengthy
descriptions of already understood scenes.

At a new level, transfer supported rules as hypotheses and check initialization,
new objects, active mode and goals. Evaluate transfer on fresh mechanics families;
already inspected public games are development evidence. No local solver,
successful replay or public win establishes the official competition target.
