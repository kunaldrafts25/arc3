resp: ChatCompletion = client.chat.completions.create(
    model="vllm-model",  # use your served name; if not set, the model path/name vLLM shows in logs
    messages=[
        {"role": "system", "content": "Reply your answer in \\boxed{}"},
        {"role": "user", "content": "How many r are there in strawberry?"},
    ],
    max_tokens=1024,
    temperature=1.0,
    extra_body=dict(min_p=0.02, stop_token_ids=stop_token_ids, chat_template_kwargs=dict(enable_thinking=True)),
)

print(resp.choices[0].message.reasoning_content)
print(resp.choices[0].message.content)