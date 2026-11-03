"""Single-example native multimodal collation with exact assistant-only loss."""
import base64
from hashlib import sha256
from io import BytesIO

from PIL import Image


def collate_example(record,processor,max_tokens=32768):
    """Requires the actual target processor. No teacher code is executed."""
    messages=record['messages']
    if messages[-1]['role']!='assistant':raise ValueError('Final supervised assistant reply required')
    kwargs=record['template_kwargs']
    render=processor.tokenizer.apply_chat_template
    prefix=render(messages[:-1],tools=record['tools'],tokenize=False,add_generation_prompt=True,**kwargs)
    text=render(messages,tools=record['tools'],tokenize=False,add_generation_prompt=False,**kwargs)
    if (not text.startswith(prefix) or len(prefix)!=record['assistant_start_char']
            or sha256(text.encode()).hexdigest()!=record['rendered_text_sha256']):
        raise ValueError('Native target rendering differs from the frozen data audit')
    images=[]
    for message in messages[:-1]:
        content=message.get('content')
        if not isinstance(content,list):continue
        for part in content:
            if part.get('type')!='image_url':continue
            url=part['image_url']['url']
            if not url.startswith('data:image/png;base64,'):raise ValueError('Only embedded PNG observations allowed')
            image=Image.open(BytesIO(base64.b64decode(url.split(',',1)[1],validate=True))).convert('RGB')
            images.append(image)
    batch=processor(text=[text],images=images or None,return_tensors='pt',padding=False,add_special_tokens=False)
    prompt=processor(text=[prefix],images=images or None,return_tensors='pt',padding=False,add_special_tokens=False)
    ids=batch['input_ids'];prompt_ids=prompt['input_ids'];length=prompt_ids.shape[-1]
    if ids.shape[0]!=1 or ids.shape[-1]>max_tokens:raise ValueError('Training context limit exceeded')
    if not ids[:,:length].equal(prompt_ids):raise ValueError('Actual image-expanded token prefix differs')
    labels=ids.clone();labels[:,:length]=-100
    if int((labels!=-100).sum())<16:raise ValueError('No substantial supervised reply')
    batch['labels']=labels
    return batch,dict(actual_input_tokens=ids.shape[-1],masked_prompt_tokens=length,
        supervised_tokens=int((labels!=-100).sum()),images=len(images),
        boundary='Actual processor tensor/loss-mask checks only; not a backward pass or model-quality result.')
