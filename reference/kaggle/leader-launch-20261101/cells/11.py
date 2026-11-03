from openai import OpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

# Point the client to your local vLLM server
os.environ["OPENAI_API_BASE"] = "http://127.0.0.1:8000/v1"
os.environ["OPENAI_API_KEY"] = "sk-local"  # any non-empty string

client: OpenAI = OpenAI(
    base_url=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
)

# https://github.com/vllm-project/vllm/issues/27243
# Unexpected token 2000?? while expecting start token 200006
stop_token_ids: list[int] = [
    token_id
    for token_id in range(200_000, 201_088)
    if token_id not in [200005, 200006, 200007, 200008]
]