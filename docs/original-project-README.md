# ARC-Hydra: ARC-AGI-3 research agent

An offline game-playing agent and experiment archive for
[Kaggle ARC Prize 2026, ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3).
The strongest verified stack uses Intel AutoRound Qwen3.8-Flash-Next,
Albucino speculative decoding, and the Pennyroyal SGLang runtime on one
competition-provided RTX PRO 6000.

## Results and status

The competition deadline was **2 November 2026, 23:59 UTC**. The best completed
on-time official submission is **57726784, score 28.45**. The last verified
competing leader scored **75.56**. The project did not reach its competition target.

| Experiment | Evaluation | Result |
| --- | --- | --- |
| General learner with bounded memory | All 25 public development games, about 8h22 gameplay | 62.09; 147 levels; 11 wins |
| Flexible optional-planning agent | Official submission 57751759 | 25.96 |
| Final memory/inspection/prediction composition | Two-hour total development cap | 36.60; 84 levels; 4 wins |
| Final composition versus retained memory agent | Same 4,935 seconds of gameplay | 36.60 versus 38.53; promotion gate rejected it |
| Trained 27B adapter versus its base | Same five held-out public games | 5.33 versus 15.71; all five game scores regressed |

Public development scores use different environments from official scoring.
These experiments do not isolate every component's effect. A smaller training
loss did not produce better gameplay. No winning performance is claimed.

At the user's request, the exact final notebook was accepted **after the deadline**
as submission **57942215** on 3 November. It is a late evaluation, not an on-time
competition entry. Its live status is kept locally under
`reports/arc3/late-submission/`; the initial checked state was PENDING.
See [the experiment results](docs/arc3_results.md) for evidence and limitations.

## Repository map

- `hydra/`: perception, memory, optional planning, measured predictions, and training helpers.
- `agent/`: the original local agent integration.
- `scripts/`: notebook builders, data preparation, gameplay audits, and guarded Kaggle workflows.
- `notebooks/general_learner/`: frozen strongest long-run public agent.
- `notebooks/arc3_deadline_candidate/`: exact last uploaded candidate; retain its recorded hashes.
- `tests/`: unit, packaging, resource-guard, and integration checks.
- `docs/`: research, reproduction notes, provenance, and historical handoffs.
- `reports/`: selected metrics and provenance. Large raw artifacts stay local.
- `arc2/`: a separately maintained ARC-AGI-2 track; see [its notes](docs/arc2_baseline.md).

## Local setup and verification

Use Python 3.12. The [archived starter guide](docs/starter_guide.md) contains
the original setup and notebook workflow. On Windows:

```powershell
./scripts/setup_windows.ps1
.venv/Scripts/python.exe -m pytest --ignore-glob="tests/test_arc2*.py"
.venv/Scripts/python.exe -m scripts.audit_release
```

The full integration suite also needs the ignored Duck source checkout and
recorded CPU-gate artifacts described in [reproduction notes](docs/release.md).
CI runs a smaller set that needs no Kaggle credentials, GPU, or private traces.
Do not interpret passing tests as evidence of game-solving improvement.

Kaggle credentials belong in the ignored `.kaggle/access_token`. No source import starts a GPU job. Launch/submission scripts
require explicit execution; historical deadline guards may intentionally refuse
new runs. Read their scope before executing them.

## Release boundaries

This is a **code and selected-results release**. Model weights, adapters, raw
teacher examples, full transcripts, downloaded dependencies and credentials are
excluded from Git and preserved locally. Frozen notebooks are not reformatted:
their source hashes identify the actual evaluated packages. Some training
notebooks reference private input bundles; those bundles are not included or
claimed to be reproducible from the public checkout alone.

Run the release audit before committing. See [the release checklist](docs/release.md)
and [third-party notices](THIRD_PARTY_NOTICES.md). The configured `origin` may
still point to ARC Prize's starter repository; use your own GitHub destination.

Project additions and Duck-derived work are provided under [Apache-2.0](LICENSE),
subject to the original components' notices. ARC Prize starter/framework code
retains its [MIT license](docs/licenses/ARC-Prize-MIT.txt). Models and runtimes
have separate licenses. This repository is not affiliated with ARC Prize,
Qwen, Intel, or Tufa Labs.
