# Rolling-summary result

Exact notebook: `kunalsinghh25/arc-hydra-duck-summary/1`, COMPLETE.
All 25 public games have verified model gameplay. This is a single public pass,
not an official competition score or a controlled estimate of hidden performance.

The public mean was **37.0547**, compared with original **43.7621**. Levels fell
from 102 to 89; full wins increased from five to six. Do not promote this variant.

The BP35 request trace contains five distinct retained summary replies, first
visible at action counters 12, 25, 73, 80 and 83. Their lengths are 5,134–9,889
characters and none contains the upstream incomplete-summary marker. The source
hash and individual summary hashes are in `bp35-summary-audit.json`. This verifies
execution and retention in that game; it does not establish coverage of all games
or preservation of every important fact.

BP35 completed two of nine levels, versus one in the original run; its public
score was 6.6667 versus 0.5830. The aggregate regression therefore cannot be
described as universal harm across every game. Single-pass variation and the
shared scheduler prevent causal attribution from this comparison alone.

Summary calls occur outside the gameplay turn loop's request logger. Their
request/reply messages appear in later gameplay histories, but their direct
usage is absent from those logged response records. The 230,037 completion
tokens across 76 logged gameplay responses cannot measure summary overhead.
Do not subtract it from other aggregate token counters to infer that overhead:
unfinished generation and differing accounting boundaries also contribute.

Next memory experiment, if warranted by further traces: first add separate
summary-attempt usage/timing telemetry, then test a change addressing an observed
failure. Repeating the same global configuration or increasing summary frequency
has no supporting evidence from this run. The original runtime/model/agent
remains the submitted candidate while the independent CPU runtime build runs.
