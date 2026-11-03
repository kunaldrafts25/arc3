"""Read bounded prefixes of our completed public traces; no compute launch."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path

import requests

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reports/research/arc3-training-selection-20261101/teacher-prefixes'
LIMIT=8*1024*1024
SOURCES={'general':'arc-hydra-general-learner','control':'arc-hydra-inspection-matched-control',
         'prediction':'arc-hydra-prediction-matched-candidate'}


def main():
    split=json.loads((ROOT/'reports/arc3/qwen27-training-pilot/split.json').read_text())['games']
    eligible={game+'_p0_requests.jsonl' for game,kind in split.items() if kind!='test'}
    token=ROOT/'.kaggle/access_token'
    os.environ['KAGGLE_API_TOKEN']=token.read_text(encoding='utf-8-sig').strip()
    os.environ['KAGGLE_CONFIG_DIR']=str(token.parent)
    from kaggle.api.kaggle_api_extended import KaggleApi
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest
    api=KaggleApi();api.authenticate()
    for label,slug in SOURCES.items():
        exact='kunalsinghh25/'+slug+'/1'
        if api.kernels_status(exact).status.name!='COMPLETE':raise RuntimeError('Teacher source not complete: '+exact)
        directory=BASE/label;directory.mkdir(parents=True,exist_ok=True)
        existing_path=directory/'manifest.json'
        existing=json.loads(existing_path.read_text()) if existing_path.exists() else dict(files={})
        items=[];page=None
        with api.build_kaggle_client() as client:
            while True:
                req=ApiListKernelSessionOutputRequest();req.user_name='kunalsinghh25';req.kernel_slug=slug
                req.version_label=api._kernel_version_label('1');req.page_size=100
                if page:req.page_token=page
                response=client.kernels.kernels_api_client.list_kernel_session_output(req)
                items.extend((item.file_name,item.url) for item in response.files or [] if item.file_name in eligible)
                page=response.next_page_token
                if not page:break
        def fetch(item):
            name,url=item;path=directory/name;old=existing.get('files',{}).get(name)
            if old and path.is_file() and sha256(path.read_bytes()).hexdigest()==old['sha256']:return name,old
            try:
                with requests.get(url,headers={'Range':f'bytes=0-{LIMIT-1}'},stream=True,timeout=(15,60)) as response:
                    response.raise_for_status();chunks=[];size=0
                    for chunk in response.iter_content(1024*1024):
                        take=chunk[:LIMIT-size];chunks.append(take);size+=len(take)
                        if size>=LIMIT:break
                    payload=b''.join(chunks)
                    # A bounded partial record is excluded, never parsed as complete.
                    end=payload.rfind(b'\n')
                    if end<0:raise ValueError('No complete log records in bounded prefix')
                    payload=payload[:end+1]
                    for line in payload.splitlines():json.loads(line)
                    path.write_bytes(payload)
                    return name,dict(sha256=sha256(payload).hexdigest(),bytes=len(payload),
                        complete_lines=len(payload.splitlines()),prefix_limit_bytes=LIMIT,
                        entire_remote_file_captured=size<LIMIT,range_supported=response.status_code==206)
            except Exception as exc:
                # Signed URLs must never enter user output or retained diagnostics.
                return name,dict(error_type=type(exc).__name__)
        with ThreadPoolExecutor(max_workers=4) as pool:results=dict(pool.map(fetch,items))
        manifest=dict(source_kernel=exact,files=results,split_sha256=sha256((ROOT/'reports/arc3/qwen27-training-pilot/split.json').read_bytes()).hexdigest(),
            boundary='Original contiguous complete JSONL prefix only, at most eight MiB per file. Test-game files excluded. Incomplete final line dropped. No remote mutation or GPU use. Prefix hash is not a whole-file hash.')
        existing_path.write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(dict(source=label,files=len(results),bytes=sum(x.get('bytes',0) for x in results.values()),
            errors={n:x for n,x in results.items() if 'error_type' in x}),indent=2),flush=True)


if __name__=='__main__':main()
