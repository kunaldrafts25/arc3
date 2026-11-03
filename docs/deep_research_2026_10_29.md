# Research for the next ARC-AGI-3 capability experiment

Reviewed 29 October 2026. This combines primary-source research with our own
failure evidence and a new executable CPU diagnostic. External results below
are author-reported. No new competition score, GPU comparison or notebook
integration is established by this review.

## Decision

Develop a small optional mechanism for competing predictions and observed
counterexamples. Add short experiment lookahead when useful actions require
setup. Keep the flexible action path, exact observation tools and original
model/runtime as the control. The goal is better action decisions, not a higher
simulator replay score, a longer prompt or more stored beliefs.

The substantial missing work is still candidate generation and perceptual
grounding: the model must propose useful alternatives from pixels and history.
The prototype below receives its candidate forecasts and measured features.
It does not solve that problem and must not be represented as a new general
game-playing agent.

## Primary research and what transfers

| Source | Demonstrated contribution / relevant assumption | Engineering implication for us |
| --- | --- | --- |
| [EMPA: theory-based modeling, exploration and planning](https://arxiv.org/html/2107.12544) | Evaluates a program-based causal learner on 90 VGDL-style games. The learner assumes avatar identity/type and wall identity/type; its termination language is restricted to counts of object classes reaching zero. | Learn object interactions, conditional rules and goal alternatives together. Do not import its success claim as proof of black-box ARC capability: our agent must discover the assumed roles and support broader goals. |
| [WorldCoder](https://arxiv.org/html/2402.12275) | Synthesizes executable transition/reward programs and uses optimism to explore. Assumes symbolic discrete states, deterministic dynamics and an externally supplied natural-language goal. | Use checked code proposals and preserve failed examples. Its known-goal setting leaves a major ARC problem unsolved; optimistic imagined reward must not become a fabricated win condition. |
| [Executable World Models for ARC-AGI-3](https://arxiv.org/html/2605.05138) | Reports 58.12 mean public RHAE with a frontier coding agent, executable verification and refactoring. The authors did not test the private validation set. | Test compact reusable rule programs and measured counterexamples. Do not promise a gain from reproducing an entire model for every action or substitute public results for an official score. |
| [Tycho](https://arxiv.org/html/2607.28287) | In a matched public-set policy comparison, actor-requested model building scores 88.49; automatic repair scores 83.07 despite better transition match. Uses frontier hosted models. Partial predictions can abstain on uncertain regions. | Build or repair a model when it can change the decision. Retain model bypass and explicit coverage; a matching simulator is not a certified objective or a good next action. Offline model substitution needs a new experiment. |
| [Counterexample-guided synthesis](https://people.csail.mit.edu/asolar/SynthesisCourse2020/Lecture10.htm) | Candidate programs are refined using counterexamples from a checker. Formal guarantees depend on the specification and checker. | Store frozen predictions before acting and preserve actual disagreements for the next proposal. Our environment is a costly source of examples, not an exhaustive formal verification oracle. |
| [Bayes-adaptive POMDPs](https://www.cs.cmu.edu/afs/cs/Web/People/sross1/publications/jpineau-isaim08.pdf) | Jointly reasons about uncertainty in state and dynamics and the exploration/exploitation tradeoff; exact belief tracking is costly. | Maintain a bounded set of plausible states/rules, including hidden mode and history. Do not label arbitrary language-model confidence scores a calibrated posterior. |
| [POMCP](https://papers.nips.cc/paper_files/paper/2010/file/edfbe1afcf9246bb0d40eb4d8027d90f-Paper.pdf) | Combines particle beliefs and Monte Carlo planning using a supplied generative simulator. | Search becomes useful after we have plausible transition hypotheses. Adding MCTS alone cannot discover missing mechanics, goals or an adequate representation. Start with short bounded questions, not a huge tree. |
| [DreamCoder](https://arxiv.org/abs/2006.08381) | Learns reusable program abstractions and a neural search policy through wake/sleep cycles over supplied domains and tasks. | Reuse measured operations and learned solver fragments with preconditions. Full library/neural training is a larger project; copying an action sequence without its conditions is weak transfer. |
| [Options framework](https://www.sciencedirect.com/science/article/pii/S0004370299000521) | Formalizes temporally extended, closed-loop action policies in an MDP/semi-MDP framework. | A reusable skill needs an initiation condition, a policy and termination/interrupt conditions. Prefer a guarded skill over an unverified fixed macro when later levels vary. |
| [Metareasoning for Planning Under Uncertainty](https://ijcai.org/proceedings/2015/229) | Studies the value and cost of additional computation; exact general metareasoning is itself impractical, motivating approximations. | Decide whether the next model call, model repair or search expansion is likely to change the action. We need measured learning progress and bounded repair budgets, not another generic notice after N moves. |
| [DreamerV3](https://www.nature.com/articles/s41586-025-08744-2) | A trained latent world model supports imagined rollouts across many control tasks. This is a training-based system with its own interaction requirements, not instantaneous unknown-game induction. | A valuable longer-term direction, but a replacement Dreamer training project is poorly matched to the current deadline, sparse feedback and available compute. |
| [DAgger](https://proceedings.mlr.press/v15/ross11a.html) | Addresses the distribution shift of sequential imitation by collecting supervision on states induced by the learner. | If we distill a smaller policy, include its actual failure/recovery states, not only clean expert wins. An appropriate expert and valid labels are additional requirements. |
| [STaR](https://proceedings.neurips.cc/paper_files/paper/2022/file/639a9a172c044fbb64175b5fad42e9a5-Paper-Conference.pdf) | Bootstraps rationale training using answer correctness and rationalization. | Filter synthetic interactive trajectories by actual outcomes and prediction checks. A successful final answer alone cannot certify the intervening reasoning or establish ARC transfer. |

These are selected methods, not an exhaustive review of all relevant research.
We independently implemented the prototype; no source repository was copied
into the agent as part of this experiment.

## What the agent should learn to distinguish

An inert action is compatible with several explanations: the clicked object is
not a control, the control mode is wrong, the path is blocked, an enabling
condition is missing, or the effect is delayed. A single best-guess story loses
those alternatives. The next useful question is which affordable interaction
would make their observable predictions differ.

However, maximizing immediate disagreement is also insufficient. Selecting a
control or obtaining a key can have no immediate diagnostic value while making
the next experiment informative. Include short prerequisite sequences and
goal-directed actions. If all models agree on a useful plan, the agent should
act efficiently instead of seeking more novelty. If all models fail, request
a new state/rule proposal instead of choosing the least-wrong survivor.

Keep uncertainty about object extraction, mechanics and goals separate. A
prediction mismatch might reflect a bad actor identity or missing hidden mode;
it does not always mean the movement law is wrong. Successful predicted motion
without completion raises a different question about the goal or prerequisites.
Observed steps support scoped claims, not universal causal correctness.

A useful state abstraction preserves distinctions that change future actions,
outcomes or cost. Ignore neither all border pixels nor all counters: these may
be controls or resources. Instead, make explicit partial predictions about the
measured features needed for the current question, retain the original frame,
and refine the abstraction when histories with the same encoding diverge.

## New implementation and diagnostic

`hydra/prediction_ledger.py` is a standalone prototype with:

- Frozen pre-action forecasts, consumed once, for named hypothesis versions.
- Exact comparisons on measured JSON features, with partial-observation and
  unknown-prediction outcomes distinct from successful checks.
- Permanent counterexamples per contradicted candidate, retained even after
  the bounded general evidence log evicts old records.
- Explicit level scope, step ordering and boundary handling. Transferred rules
  require a fresh ledger and new checks.
- Coverage-weighted predicted-outcome disagreement per declared action cost.
  This is a local finite-ensemble heuristic, not calibrated posterior confidence,
  formal expected task value or Bayes-optimal experiment design.
- No forced winner when all supplied hypotheses are contradicted. No action
  execution or changes to ordinary environment action batching.

It assumes deterministic measured effects. Noisy sensors, stochastic dynamics
and uncertain feature extraction need a richer likelihood/representation;
one exact mismatch must not become a general-purpose stochastic inference rule.
The module is not yet connected to the actual sandbox, persistent host state,
model-generated proposals or notebook. Current submitted versions are unchanged.

`scripts/benchmark_prediction_ledger.py` ran 768 episodes across three policies
and two deliberately small identification families, 128 matched seeds per cell.
Actions and signal colors are randomized, with an irrelevant changing counter.
The prerequisite family needs an enabling action before an informative probe.
Lookahead executes the enabling action first, observes it and replans; it does
not blindly execute a two-action batch.

| Diagnostic | Random probing | Greedy immediate disagreement | Supplied two-action lookahead |
| --- | ---: | ---: | ---: |
| Direct identification | 128/128; 6.96 mean actions | 128/128; 3 actions | 128/128; 3 actions |
| Identification requiring setup | 128/128; 11.89 mean actions | 0/128; stops without a diagnostic action | 128/128; 4 actions |

Crucial limitation: all eight candidate programs are supplied, the true one is
included, features are measured exactly, and the setup operation is represented
in the candidate class. This is not a mechanics-family holdout, general game
solving, LLM induction, goal discovery or ARC scoring. The negative greedy result
diagnoses a design pitfall; a production controller must fall back to useful
exploration rather than stopping. Cases with the correct hypothesis absent,
abstention, missing features and scope changes are covered by semantic tests.

Ten new ledger tests and the existing planner/memory tests passed together:
33 checks. This proves those local contracts, not competitive gameplay. The
diagnostic and hashes are in `reports/research/active-identification/diagnostic.json`.

## A practical experiment sequence

1. Couple exact observation inspection with a bounded proposal interface:
   ask for two or three decision-relevant alternatives and forecasts only at
   consequential uncertainties. Keep the existing agent as the fallback.
2. Run a CPU host integration gate that checks actual before/after timing,
   authoritative observation ownership, persistence through tool resets,
   no unexpected environment actions and no cross-game/level evidence reuse.
3. Evaluate whether the unchanged local model generates useful alternatives
   and adopts the interface. Supplied-model synthetic success does not answer
   this. Measure checked-feature coverage, counterexample use and whether the
   selected question changes the next action.
4. Compare real gameplay under a matched model/runtime and compute budget.
   Primary measures are level/game completion, action efficiency, inference cost
   and time. Auxiliary model accuracy is diagnostic only. Existing public games
   are development data, not an unseen evaluation set.
5. Submit only a concrete validated candidate when allowance permits. Keep
   submission 57751759 and the best completed official 28.45 result intact.

Separately, test guarded within-game skill transfer when an early level is
solved: parameterize a route/search procedure by new observations and recheck
its initiation conditions. This may reduce later-level rediscovery, but should
not be bundled into the first prediction-interface comparison. Cross-game
libraries require stronger scope and evaluation controls.

Training is a conditional branch. If the interface works but the local model
fails to propose correct state/rule alternatives, generate verifiable synthetic
discovery and recovery trajectories, hold out mechanics families, and evaluate
an adapter or small specialist. Do not train on unverified reasoning, assume
ARC-2 gains transfer, or launch full RL/pretraining without a resource estimate.
Current resources make a focused hypothesis-generation or perception specialist
more plausible to investigate than a new foundation model.

The original account's remaining development quota is too small for the planned
full-model comparison before the 31 October refresh. Research and CPU gates
can proceed now. No paid compute, additional-account quota bypass, GPU launch
or new competition submission occurred during this experiment. The objective
still requires a completed official result of 100 or above the latest verified
competing leader; this prototype does not establish either outcome.
