import subprocess

def start_vllm_server() -> subprocess.Popen[bytes]:
    """Start vLLM server in the background"""
    os.environ["TRANSFORMERS_NO_TF"] = "1"
    os.environ["TRANSFORMERS_NO_FLAX"] = "1"
    os.environ["VLLM_ATTENTION_BACKEND"] = "TRITON_ATTN"
    os.environ["TRITON_PTXAS_PATH"] = "/usr/local/cuda/bin/ptxas"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    # https://docs.vllm.ai/projects/recipes/en/latest/OpenAI/GPT-OSS.html#troubleshooting
    os.environ["TIKTOKEN_ENCODINGS_BASE"] = (
        "/kaggle/usr/lib/pip_install_aimo3_1/tiktoken_encodings"
    )

    sequence_length = 65_536

    command: list[str] = [
        "python",
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        "/kaggle/input/gpt-oss-120b/transformers/default/1",
        "--served-model-name",
        "vllm-model",
        "--tensor-parallel-size",
        "1",
        "--max-num-seqs",
        "4",
        "--gpu-memory-utilization",
        "0.96",  # any higher may not have enough for graph capture
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--dtype",
        "auto",
        "--max-model-len",
        f"{sequence_length}",
    ]

    # Start the process in the background
    with open("/kaggle/working/a-vllm.log", "w") as logfile:
        process: subprocess.Popen[bytes] = subprocess.Popen(
            command, stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True
        )

    print("Logs: /kaggle/working/a-vllm.log")
    return process

# Start the server
vllm_process: subprocess.Popen[bytes] = start_vllm_server()