# Research review — 2026-10-24

All results below are author-reported, not independently reproduced in this project. Public-set results do not establish hidden-set performance.

| Method | Evidence and reproducibility | Compute / Kaggle fit | Solo implementation and weaknesses |
|---|---|---|---|
| NVIDIA AVO | NVIDIA reports 100 RHAE, 183 levels across 25 public games, 6,624 actions; full agent backend not reproduced | Report uses frontier Claude Opus 5; hosted dependency conflicts with offline objective | Reuse persistent memory and stagnation detection; reproducing full system is not a short project |
| VISTA | Paper reports 100 RHAE on 25 public games with Claude Opus 5; visual memory and retrieval harness | Frontier model dependency; offline substitution needs experiments | Lossless observations are useful immediately; score transfer to a small local model is unknown |
| Programmatic world models / active abstraction | Tycho reports 88.49 RHAE with actor-requested model building on Opus 4.8; selected policy reports 100 with Opus 5 and GPT-5.6 Sol. Public source is available; not reproduced here | Frontier-model transports and container execution do not directly fit offline Kaggle; CPU search itself is cheap | Days to weeks; accurate observed transitions alone do not identify goals or guarantee better actions |
| Empirical transition graph + bounded BFS/MPC | Standard executable graph search; no ARC score claimed | CPU-only, no weights | Hours to days; cannot extrapolate unobserved transitions, must revalidate predictions |
| Object-centric perception | Connected components and temporal differences; no ARC score claimed | NumPy / CPU | Hours to days; sprites, backgrounds and animation create ambiguous objects |
| Information-seeking exploration | Visit counts and uncertain action-outcomes approximate information gain; not Bayesian optimality | Cheap and offline | Hours; visual novelty can reward timers and cosmetic changes |
| Hierarchical options | Replay independently validated subplans; no reproduced ARC result | Cheap once mechanics learned | Days; transfer across levels is unsafe without checking preconditions |
| ReAct-style control | Alternating reasoning, action and evidence is a control pattern, not a validated policy here | Hosted implementations unsuitable; symbolic loop is offline | Hours for controller, substantial work for useful reasoning |
| Partial-observability belief models | Maintain conflicting outcomes and refuse deterministic planning on contradictions | Lightweight empirical distributions first | Days; image hashes are observations, not guaranteed Markov states |
| Local VLM / neural world model | No selected model or measured gain | VRAM, licensing, packaged weights and runtime unverified | Defer until baseline and rules verified; training is not justified yet |

Ranked implementation shortlist:

1. Advertised-action validation, deterministic seeds, exact lifecycle handling and measurement.
2. State/action counts, transition uncertainty, repeated-state avoidance and bounded recovery.
3. Observation differences and component-based click candidates, with raw-frame fallback.
4. Bounded BFS over repeatedly confirmed empirical edges; execute one step and revalidate.
5. Goal hypotheses grounded in observed completions; defer ungrounded goal heuristics.
6. Only then consider learned abstractions, reusable options and a local model.

Expected implementation times above are engineering estimates, not measured results. No external method has been reproduced by this repository. Sources inspected:

- https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/
- https://arxiv.org/abs/2610.02200
- https://arxiv.org/abs/2603.24517 (AVO kernel-search paper; distinguish it from the ARC-specific report)
- https://docs.arcprize.org/methodology
- https://arxiv.org/abs/2607.28287
- https://github.com/NIMI-research/Tycho (README and reported results inspected; implementation not independently reproduced)
- https://vista-research.github.io/ (public code link and observation design)

The NVIDIA post explicitly describes its comparison with VISTA as uncontrolled and its results as public-set only. We do not interpret it as proof that one memory mechanism causes the reported improvement.

Tycho's paper reports that automatic repair improves transition reproduction yet scores below actor-controlled delegation (83.07 versus 88.49 in its matched Opus 4.8 comparison). This supports testing whether a model improves action selection, beyond testing transition accuracy. VISTA's project page and later paper differ in their action-reduction percentages (56.0 versus 57.4); we retain only the common public-completion claim here and do not treat those percentages as a controlled comparison.
