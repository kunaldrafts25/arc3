import os
import time
import torch
import numpy as np


def is_on_kaggle_commit() -> bool:
    return os.getenv("KAGGLE_KERNEL_RUN_TYPE") == "Batch" and not bool(
        os.getenv("KAGGLE_IS_COMPETITION_RERUN")
    )


def is_on_kaggle_interactive() -> bool:
    return os.getenv("KAGGLE_KERNEL_RUN_TYPE") == "Interactive" and not bool(
        os.getenv("KAGGLE_IS_COMPETITION_RERUN")
    )


start_time = time.time()
final_cutoff_time = start_time + (4 * 60 + 45) * 60  # 4.75 hours from start time
cutoff_times = [
    int(x) for x in np.linspace(final_cutoff_time, start_time + 12 * 60, 50 + 1)
]  # 5 minutes loading time at the start
cutoff_times.pop()

os.makedirs("solutions", exist_ok=True)

assert torch.cuda.is_available()
assert torch.cuda.device_count() == 1