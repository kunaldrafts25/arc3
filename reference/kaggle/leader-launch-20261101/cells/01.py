import subprocess

uninstall_proc = subprocess.Popen(
    ["pip", "uninstall", "--yes", "tensorflow", "keras", "scikit-learn"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)