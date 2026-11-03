"""Reuse the strict original-account 27B launcher for its frozen capacity repair."""
from scripts import run_qwen27_baseline as runner

runner.PACKAGE=runner.ROOT/'notebooks/qwen27_fair_capacity'
runner.DIRECTORY=runner.ROOT/'reports/arc3/qwen27-fair-capacity'
runner.OUTPUT=runner.ROOT/'reports/kaggle/qwen27-fair-capacity-v1'
runner.KERNEL='kunalsinghh25/arc-hydra-qwen27-fair-capacity'
original_validate=runner.validate_package
runner.validate_package=lambda:original_validate(runner.PACKAGE)

if __name__=='__main__':runner.main()
