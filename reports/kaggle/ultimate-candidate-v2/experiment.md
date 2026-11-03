# Optional planning after the strict-planner regression

Exact job: `kunalsinghh25/arc-hydra-ultimate-candidate/2`. All 25 public games,
one pass, 7200 seconds after readiness, 12000-second notebook timeout. Original
Intel target/draft, v2.5.3 runtime and scheduler. Full public diagnostics and
mechanical helper events. No official submission or weight training.

Ordinary action batches/repeated calls delegate to the original host and retain
its guards/results. Prediction/encoding callbacks still cannot spend actions.
Optional execute_plan replays evidence and checks each action. Ordinary actions
use original benchmark accounting; helper events cover checked-plan adoption.
Guidance describes the contract, valid step limits and function dependencies.

Rationale: completed baseline/3 scored 45.0150 with 103 levels; strict planner/2
scored 33.1771 with 75 levels. Fifteen games regressed versus four improvements.
This does not isolate causes; keep the original as the validated baseline.

CPU probe/5 COMPLETE: eight sandbox cases, 16 rendered prompt combinations.
Local suite 93 passed before the path fix; three input-layout checks then passed.
Version 1 was ERROR before model loading: its hard-coded dataset path was absent.
Version 2 resolves exact input names in both known layouts before copying/loading.
Logs confirm short source/runtime dataset mounts and canonical model mounts;
the harness patch applied successfully.

Later authoritative status: **ERROR**, before model loading. The competition
wheel directory was also mounted under its short path, which the first fix did
not cover. Version 3 resolves that wheel path before installation and uses the
same resolved parent for public environment files. No score or gameplay result
was produced by versions 1 or 2. Neither job was restarted while live.

Compare final scores, levels, wins, completion curves, tokens, errors and helper
use with baseline/3. The baseline is a prior stochastic run, not paired seeds.
Require substantive gameplay across all games. Upload, CPU checks, startup and
public scores do not establish a hidden-score gain.
