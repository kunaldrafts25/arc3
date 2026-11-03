# Runtime version 2: terminal GPU failure

Exact notebook `kunalsinghh25/arc-hydra-duck-v3-runtime/2`: ERROR.
The real Triton host-extension probe passed on CUDA device 0, resolving v1's
Python multiarch-header failure for that path.

Later, FlashInfer's XQA attention JIT attempted to link with the Conda C++
toolchain and failed with `cannot find -lcuda`. SGLang subsequently exited
before readiness. No gameplay score or throughput gain was established.

This is a distinct failure after the earlier repair, not proof that the runtime
bundle is corrupt or the model exhausted memory. The completed CPU build and
the independent bundle checksum probe do not cover every GPU JIT path.

The next runtime repair would require a correct compile-time CUDA driver-library
search path and a representative GPU JIT/warmup check. No version 3 was launched:
the user requested deeper strategic research, now recorded in
`reports/research/2026-10-27/strategy.md`. The original runtime remains the control.
