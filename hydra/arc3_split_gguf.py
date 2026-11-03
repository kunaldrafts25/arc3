"""Checked split-file reader integration for the pinned experimental HF fork.

The quantizer sees a combined tensor inventory; every lazy tensor retains its
own file reader and offset. No large checkpoint is copied or concatenated.
"""
from math import prod
from pathlib import Path


def read_split_headers(paths):
    from transformers.integrations.gguf import reader
    paths=[Path(path).resolve() for path in paths]
    if len(paths)<2 or len(set(paths))!=len(paths):raise ValueError('Distinct split files required')
    headers=[];seen=set();architecture=None
    for path in paths:
        blob=reader._mapped(str(path))
        metadata,count,position=reader._read_metadata(blob,str(path))
        current=metadata.get('general.architecture',architecture)
        if not current or (architecture is not None and current!=architecture):
            raise ValueError('Split GGUF architecture mismatch or missing primary metadata')
        architecture=current
        entries,position=reader._read_tensor_table(blob,count,position)
        alignment=int(metadata.get('general.alignment',32))
        if alignment<=0 or alignment>2**20 or alignment&(alignment-1):raise ValueError('Invalid GGUF alignment')
        data_start=(position+alignment-1)//alignment*alignment
        tensors=[]
        for name,shape,kind,offset in entries:
            size=reader._byte_count(kind,prod(shape),str(path))
            if name in seen or offset<0 or data_start+offset+size>path.stat().st_size:
                raise ValueError('Duplicate or out-of-bounds split tensor: '+name)
            seen.add(name);tensors.append(reader.TensorInfo(name,shape,kind,offset,size))
        headers.append(reader.GgufHeader(str(path),architecture,tuple(tensors),data_start))
        del blob
    return headers


def install_split_loader(paths):
    from transformers.integrations.gguf.reader import load_gguf_state_dict
    from transformers.quantizers.quantizer_gguf import GgufHfQuantizer
    paths=[Path(path).resolve() for path in paths]
    headers=read_split_headers(paths);primary=paths[0]
    original_header=GgufHfQuantizer.read_header;original_state=GgufHfQuantizer.get_state_dict
    if getattr(original_header,'_arc3_split_loader',False):raise RuntimeError('Split loader already installed')
    def read_header(self,checkpoint):
        result=original_header(self,checkpoint)
        if Path(checkpoint).resolve()==primary:
            if not self.supported:raise ValueError('Pinned quantizer does not support this architecture')
            self.header=headers[0]._replace(tensors=tuple(t for h in headers for t in h.tensors))
            self._arc3_split_headers=headers
        return result
    def get_state_dict(self,checkpoint,model):
        if not hasattr(self,'_arc3_split_headers'):return original_state(self,checkpoint,model)
        if Path(checkpoint).resolve()!=primary:raise ValueError('Unexpected split-loader checkpoint')
        merged={}
        for header in self._arc3_split_headers:
            current=load_gguf_state_dict(header,mmap_policy=self.quantization_config.mmap_policy)
            if merged.keys()&current.keys():raise ValueError('Repeated split state dictionary key')
            merged.update(current)
        return merged
    read_header._arc3_split_loader=True
    GgufHfQuantizer.read_header=read_header;GgufHfQuantizer.get_state_dict=get_state_dict
    return dict(primary=str(primary),files=[str(path) for path in paths],tensors=sum(len(h.tensors) for h in headers),
        boundary='Metadata and lazy source-reader integration only. Full-model CUDA loading/training still required.')
