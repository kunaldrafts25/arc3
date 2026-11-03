# Mathematical strategy for unfamiliar interactive games

## Conclusion and evidence boundary

Use a model-selection and experiment-selection process over several mathematical
tools. Game theory contributes when strategic players or an explicitly justified
robust-control formulation are present. For a single-agent unfamiliar puzzle,
the immediate bottleneck is discovering controls, state variables, transitions
and the completion condition. A sophisticated solver applied to the wrong model
can be consistently wrong.

The new operational draft is `docs/general_game_learning_rules.md`. It is not
installed in the running candidate. The earlier ARC-specific paper/model review
is `reports/research/2026-10-27/strategy.md`; this follow-up adds foundations and
new direct experiments. It does not reproduce the reviewed algorithms in full
or establish an official score improvement.

## What the research supports

| Primary source | Useful principle | Scope and application here |
| --- | --- | --- |
| [OpenSpiel minimax implementation](https://raw.githubusercontent.com/google-deepmind/open_spiel/master/open_spiel/python/algorithms/minimax.py) and [framework paper](https://arxiv.org/abs/1908.09453) | Choose the algorithm from the game structure. The alpha-beta implementation explicitly requires two players, deterministic sequential play, perfect information and zero-sum utility. | Do not treat an unknown puzzle as if an adversary were choosing every outcome. Chance, hidden information and learning mechanics require different representations. ARC practice uses observations/actions; do not use an engine clone as an oracle. |
| [Guez, Silver and Dayan, 2013](https://www.gatsby.ucl.ac.uk/~dayan/papers/guez_jair2013.pdf) | Bayes-adaptive planning represents uncertainty over dynamics and balances exploration with exploitation; BAMCP samples models for tree search. | Use competing models to identify useful experiments. The paper focuses on fully observable MDP dynamics, not discovering pixel semantics and unknown goals from nothing. Exact Bayes-optimal planning is expensive; finite hypotheses or sampled models are approximations. It does not establish ARC performance. |
| [He and Geng, 2008](https://jmlr.org/papers/volume9/he08a/he08a.pdf) | Interventions can distinguish causal structures that passive observations cannot; experiment design can reduce ambiguity. | Choose actions with different predicted consequences, then compare. Their causal-network assumptions and intervention access are not automatically available in pixel games; this is a design principle, not a direct reproduction. |
| [La et al., dual control](https://epubs.siam.org/doi/10.1137/16M1069936) | Control and parameter estimation interact; gathering information can improve subsequent decisions, but its extra cost matters. | Test the uncertain mechanic that blocks a promising plan. Do not maximize information about irrelevant details while losing the action/time budget. Only the accessible abstract was reviewed here. |
| [Li, Walsh and Littman, 2006](https://thomasjwalsh.net/pub/aima06Towards.pdf) | State abstraction can make planning practical, but different abstractions preserve different properties and can lose essential information. | Remove irrelevant token details when transitions and goals permit it. Preserve raw observations and test predictions outside the reduced state. A varying abstraction alone does not prove it is sufficient. |
| [Kocsis and Szepesvari, 2006](https://aima.cs.berkeley.edu/~russell/classes/cs294/s11/readings/Kocsis%2BSzepesvari:2006.pdf) | UCT directs Monte Carlo planning toward promising decisions under a generative model. | Use it after a usable model and evaluation exist. Searching a hallucinated simulator more deeply does not make it true. |
| [Kautz, 2006](https://aiweb.cs.washington.edu/ai/planning/papers/AAAI0609KautzA.pdf) | Planning can be encoded as satisfiability; encodings, solver behavior and problem structure determine practical value. | SAT/SMT are candidates for ordering, resources and logical prerequisites once semantics are identified. An incorrectly specified goal remains incorrect when its constraints are satisfied. The 1992 PDF's text extraction was unreadable, so substantive discussion relies on this readable primary account. |
| [Rigter et al., 2021](https://proceedings.neurips.cc/paper_files/paper/2021/file/08f90c1a417155361a5c4b8d297e0d78-Paper.pdf) | Risk-averse Bayes-adaptive control distinguishes model uncertainty from inherent randomness and can be expressed using a stochastic game. | Consider downside risk and reversibility when probes can lose a run. This does not imply blanket pessimism or prove that conservative play maximizes the competition score. |
| [Huang et al., 2026](https://arxiv.org/html/2610.21108v2) | Conservative versus aggressive plan commitment trades failed attempts against interaction/model-call cost. The study covers two partially observable domains. | Adapt the plan horizon to evidence. It is supporting research, not a demonstration on our ARC setup. Our strict-planner regression is separate direct evidence that compulsory checking can be costly. |
| [Juba, 2016](https://jmlr.org/papers/v17/13-584.html) | Regularities in traces can support planning under partial observability when suitable dynamics/policy assumptions hold; obtaining informative traces remains important. | Retain evidence-backed conditional rules and collect missing examples. The theorem's conditions are stronger than merely having a few screenshots. |

These sources motivate a combined architecture. None proves a universal procedure
for discovering arbitrary game rules or achieving the latest leaderboard score.

## A practical mathematical formulation

Let an episode history contain actual observations and actions. Keep uncertainty
over dynamics **M**, goal **G**, latent control mode **Z** and relevant state **S**.
The decision state is a belief over those quantities, rather than one confident
verbal story. A contradiction can change the inferred mode or representation
without invalidating every previously observed physical relation.

For a candidate action, compare predicted outcomes under competing explanations.
A practical priority heuristic can combine expected goal progress, disagreement
reduction, action/time cost and the downside of an irreversible error. This is
our proposed approximation, not an implementation of the exact Bayes-adaptive
Bellman equation. Adding an information bonus to an approximate planner does not
make it Bayes-optimal. When probabilities are uncalibrated, an explicit version
space and observed support are preferable to invented confidence percentages.

An experiment is valuable when its result changes the next decision. For example,
if every candidate route crosses one uncertain surface, testing that surface is
more useful than measuring another already understood movement direction. Keep
the completion hypothesis independent from the transition model: predicting a
scene correctly does not show that the desired scene is the winning scene.

## Direct experiments and mathematical deductions

All experiments use public observations/actions, not game implementation access.
The earlier sweep made 99 actions across all 25 games and completed two AR25
levels. This follow-up studies more mechanics and records additional results.
Raw observations, action rationales and images remain in the local reference
cache; compact experiment records are under `reports/manual-play/2026-10-28/`.

### Permutations, inverse operations and useful abstraction

In LP85, clicking one visible arrow shifted a 20-slot color sequence by one;
the opposite arrow restored the sequence. Bringing the goal-colored token to
the marked slot completed the first level automatically. No extra confirmation
click was necessary, correcting one earlier affordance hypothesis.

The next level exposed three controls affecting overlapping slots. From observed
transitions and inverse checks, I fitted proposed cycles of lengths 26, 10 and
10 over 42 mutable slots. This fit is within a proposed geometric grammar, not
proof of a unique underlying mechanism. The controls were therefore treated as
composable generators, with overlapping state retained rather than assuming
independent puzzles.

A breadth-first search over the complete color vector reached its approximately
100,000-state cap without finding a plan. Under the fitted color-independent
permutation model, the proposed goal depended only on the positions of two
indistinguishable blue tokens. This yields at most 42 choose 2 = 861 abstract
states. The reduced search discovered 335 states before finding an eight-action
plan. The reduction is a hypothesis about relevance, not permission to ignore
all other observations.

I executed that plan one real action at a time. All 42 tile colors were compared
with the full-vector prediction after each of the first seven steps; all matched.
The eighth action produced actual second-level completion. The shortened search
therefore led to a verified gameplay result. It is not proof of full-grid
correctness, optimality over every possible input, or transfer to unseen games.
The record is `permutation-experiment.json`.

General rule: fit reversible generators from interventions, verify composition,
and search a goal-relevant quotient representation while checking omitted detail.
This is algebra and abstraction selected from evidence, not an ID-based solution.

### Rigid transforms and contact constraints

In CN04, an alternate keyboard input changed a multicolor tool. A naive crop by
color included a disconnected interface pixel and failed to match a rigid
transform. Grouping the connected white body and attached orange tips removed
that contaminant. The observed 18-by-15 region then matched a quarter-turn into
a 15-by-18 region, preserving the colors exactly.

Further quarter-turn probes put the tips on the side facing two visible orange
ports. I inferred a goal hypothesis of aligning both tips with those ports while
keeping the white body outside the purple structure. The observed translation
stride was three pixels. The proposed route required four RIGHT and seven DOWN
inputs. I checked the body bounding-box prediction after each input: the first
ten matched, and the eleventh produced actual level completion.

This supports pose/contact modeling for that level. It also demonstrates why
perception and state identification precede solving geometric equations. The
same-color interface pixel would have corrupted an otherwise useful rotation
model. Records: `rotation-experiment.json` and `contact-plan-experiment.json`.

General rule: identify causally coherent parts, fit transform anchoring from
observations, solve relational constraints and check intermediate collision and
pose predictions. Do not transfer a specific color role to another game.

### A route planner correctly identifies its missing mechanic

In G50T, probes established a six-pixel stride for a five-by-five visible actor.
I built a configuration-space graph from observed floor and wall pixels,
checking the whole footprint and intermediate positions along each step. The
graph had no route to the proposed destination when orange pixels were treated
as obstacles; permitting them produced a route through an orange mechanism.

I moved only through the observed free portion. An attempted crossing then
produced no scene change. The alternate action restored the actor to its earlier
position and changed an indicator; repeating it there was inert. The mechanics
of the orange mechanism remain unresolved. No maze completion is claimed.

General rule: expose which assumption makes a plan possible, test it, and revise
the model when it fails. A shortest-path algorithm cannot discover a missing
interaction merely by searching the same blocked graph more deeply.

### Timing, selection and role uncertainty remain open

WA30 directional observations did not support one symmetric constant stride.
A small yellow/black object blocked motion; an interaction changed the visible
purple regions, and the following direction changed their configuration again.
A static single-object model is currently insufficient. Selection, animation,
transient effects and active-object identity are still competing explanations;
none is promoted as a confirmed rule.

Further probes covered ten additional games/control contexts, including geometry,
selection, alternate interactions and topology. Several affected only a counter
or nothing visible. Those are recorded as unresolved affordance/mode questions,
not discoveries of a game-specific solver. `broader-mechanics-probes.json`
contains the chosen interventions and responses.

## How the toolbox should be selected

The proposed model tests have concrete mathematical forms:

- **Permutation:** `x_next = P(mode, action) x`, with a bijection over the
  relevant slots. Check conservation and inverse/composition predictions.
- **Binary toggles:** `A u = goal XOR current (mod 2)`, only when each action
  has a tested state-independent XOR effect. Commuting twice-reversible actions
  are useful evidence, but do not by themselves prove this representation.
- **Rigid geometry:** `p_next = R p + translation`, with rotation anchoring,
  contacts and collision constraints measured from observations rather than
  assumed from a bounding-box center.
- **Navigation:** a configuration `q` is traversable only if the relevant body
  footprint at `q` fits the current free space. Check intermediate movement
  when the learned collision model requires it; doors and moving mechanisms
  make free space depend on state.

These are candidate representations, not laws to force onto every scene. The
state-abstraction conditions in the literature require preserving appropriate
reward/transition or value information; agreement on our few observations does
not establish those conditions over all future states.

1. Start with causal grounding: controls, state variables, resources and candidate
   goals. Do not select a solver from a game's name or first-frame resemblance.
2. Look for invariants and candidate operator structure. Stable slot counts and
   reversible rearrangements suggest permutations. Context-independent,
   commuting binary involutions suggest GF(2). Rigid multicolor motion suggests
   geometric pose. Traversal suggests configuration-space search. Ordering and
   resource constraints suggest logical planning.
3. Verify the assumptions with interventions and predictions at more than one
   state. A single successful action does not establish global linearity,
   commutativity, a collision model, or a winning condition.
4. Use the smallest sufficient representation and a bounded appropriate solver.
   Preserve fuller evidence for checking. If no abstraction predicts the data,
   add a latent variable or revisit segmentation before deepening search.
5. Execute with a horizon justified by the observations. Stop on model mismatch,
   mode changes, unknown outcomes or actual level/game boundaries. Ordinary
   exploration remains available; complete executable simulation is optional.
6. Preserve the resulting conditional knowledge through context drains and
   re-check initialization when a level changes. Optimize useful learning and
   actions per time/token budget, not the volume of reasoning.

The GF(2) case deserves a qualification: Gaussian elimination gives a feasible
binary solution when the model applies. Minimizing actions may require searching
its null space. Likewise, A* depends on a correct state graph and heuristic, and
MCTS depends on a useful model and evaluation. Mathematics reduces a correctly
identified problem; it does not certify an identification made from pixels.

## What to implement and how to test it

The next proposed intervention is a compact evidence ledger plus this conditional
solver-selection procedure, reusing existing frame diffs, segmentation, retained
functions and optional checked planning. Keep mechanics and goal hypotheses
separate, record specific counterexamples and state which experiment would
resolve the next decision. Avoid adding a large duplicated perception framework.

Do not inject these public starting positions, colors, coordinates or solution
sequences into a deployed dispatch table. The experiment records explain the
research; the operational draft contains no game-specific entries. Model-weight
training has not occurred. Current live Kaggle code remains unchanged.

Evaluate on deeper public play and newly generated mechanics families with
different control mappings, modes and goals. Split families before any data
generation/training. The public set is already inspected and cannot be called
an unseen holdout. Measure first-contact learning, rule/goal correction,
action efficiency and inference cost. Test the complete agent under matched
budgets and require official scoring to establish the 100/latest-leader target.

These experiments now show successful conditional reflection, cyclic algebra,
overlapping-permutation planning and rigid-contact planning in several public
levels. They leave many mechanics unresolved and do not establish a near-universal
solver. The outcome to pursue is a better tested learning process, with an
official result as the final evidence.
