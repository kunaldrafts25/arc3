# First scored competition result

Submission 57601062, notebook version 2, completed with public score **0.01**. The official status API returned no evaluation error and no private score. This is the actual Kaggle score, not an estimate or a transformed local score.

The official submission-download endpoint returned HTTP 403. We did not attempt another route to the denied artifact. Hidden per-game action counts, completion counts, handled agent exceptions and timing diagnostics are unavailable. COMPLETE does not prove every game agent ran without an internally handled failure, and a rounded aggregate score cannot identify which levels were completed.

The architecture and public measurements establish a major limitation: the selected policy explores state/action pairs, without an implemented game-objective recognizer. It has no demonstrated useful gameplay planning. The scored result confirms the deployment pipeline works; it does not establish competitive performance.

## Next experiment: more actions

Compared the same novelty policy on cd82, ls20, r11l and vc33, policy seeds 0/1/2 and environment seed 0. The 200-action baseline comes from the existing validated public ablation; the 1,000-action candidate ran through the same official loop.

| Per-game command cap | Runs | Total commands | Level completions | Full wins | Mean official local score |
|---|---:|---:|---:|---:|---:|
| 200 | 12 | 2,400 | 4 | 0 | 0.9357866260 |
| 1,000 | 12 | 12,000 | 6 | 0 | 0.9359760621 |

All runs recorded zero exceptions. The additional completions were inefficient first-level vc33 completions in seeds 1 and 2. cd82 and ls20 stayed unsolved, and r11l did not progress beyond its first level. Scores here are means over this four-game subset on the local 0–100 scale; they must not be compared directly with the 25-game aggregate or hidden Kaggle score.

Decision: do not globally promote a fivefold action cap based on this narrow, low-gain trial. More actions alone do not solve the observed generalization problem. Prioritize inferred controllable objects, action effects, and testable goal hypotheses. Preserve raw observations and validate proposed mechanics before planning through them.

## Guard correctness fix

Source inspection found the per-game timer started in the constructor, while Swarm constructs all game agents before launching threads. Thus setup waits could consume play time. The local candidate now starts that timer at main-loop entry. A test simulates an expired construction-time timer and verifies the game still receives its actual play budget. All 22 local tests pass.

This fix is not proven to explain any part of the 0.01 score. It was not part of submitted version 2 and has not been evaluated on Kaggle. The one daily submission has already been used; the deployed notebook is unchanged.

Evidence: submission-status.json, submission-status-history.jsonl, ../budget-comparison.json, ../budget-1000-v01.jsonl and ../logs/budget-1000-v01.txt.
