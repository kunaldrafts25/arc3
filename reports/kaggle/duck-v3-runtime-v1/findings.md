# Runtime preflight failure

Exact notebook `kunalsinghh25/arc-hydra-duck-v3-runtime/1`: ERROR.
No GPU gameplay or throughput improvement was established.

The final server log reports:

```
/usr/include/python3.12/pyconfig.h:3:12: fatal error:
x86_64-linux-gnu/python3.12/pyconfig.h: No such file or directory
```

Triton invoked Conda GCC to compile its host-C `cuda_utils.c` extension. That
compiler's sysroot does not provide the system Python multiarch header search
path. A child failed and SGLang killed its process tree; the notebook observed
exit -9 before readiness. Exit -9 alone does not establish memory exhaustion.

The independent CPU input probe completed and checked all 36 files and the
exact manifest at the supported notebook-input mount. No input corruption or
mount-path repair is warranted by this evidence.

Repair v2 uses system GCC for host-C/Python extensions while retaining GCC15
C++/CUDA-host compilation. It runs Triton's real driver-helper compilation
before checkpoint loading. The bundle manifest, model and agent settings remain
unchanged. GPU success is still unverified until the new probe and gameplay pass.
