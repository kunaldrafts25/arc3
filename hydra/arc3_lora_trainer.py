"""Bounded actual-checkpoint ARC3 teacher adaptation. Imported only in training jobs."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import random
import time

SUPPORTED_PROJECTIONS = frozenset(['q_proj','k_proj','v_proj','o_proj',
    'in_proj_qkv','in_proj_z','out_proj','gate_proj','up_proj','down_proj'])


def select_lora_targets(linear_names):
    """Native language projections supported by the pinned serving runtime.

    Exclude vision, output embeddings and GDN beta/decay projections. The latter
    are not in the deployed runtime's supported packed adapter families.
    """
    return sorted(name for name in linear_names if 'language_model.layers.' in name
        and name.rsplit('.',1)[-1] in SUPPORTED_PROJECTIONS)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--processor',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--deadline',type=float,required=True,help='Absolute epoch time, before the notebook finalization reserve')
    args=parser.parse_args()
    import torch
    import torch.nn.functional as functional
    from peft import LoraConfig,get_peft_model
    from transformers import AutoModelForImageTextToText,AutoProcessor
    from transformers.models.qwen3_5.modeling_qwen3_5 import chunk_gated_delta_rule
    if not torch.cuda.is_available():raise RuntimeError('Actual CUDA device required')
    if not callable(chunk_gated_delta_rule):raise RuntimeError('Fast differentiable GDN kernels are unavailable')
    torch.set_num_threads(8);torch.manual_seed(20261101);random.seed(20261101)
    output=args.output;output.mkdir(parents=True,exist_ok=True)
    report_path=output/'training-report.json'
    if (output/'adapter').exists():raise RuntimeError('Refusing to overwrite an existing adapter')
    started=time.time()
    report=dict(phase='loading',started_at_epoch=started,deadline=args.deadline,
        trainable_scope='Rank16, alpha32,400 supported language attention/recurrent/feed-forward projections; frozen base and vision. GDN beta/decay and embeddings excluded.',
        seed=20261101,learning_rate=1e-5,gradient_accumulation=4,max_epochs=1,
        device=torch.cuda.get_device_name(0),gpu_total_bytes=torch.cuda.get_device_properties(0).total_memory,
        optimizer_steps=0,training_examples=0,training_input_tokens=0,supervised_tokens=0,
        examples=[],validation=[],boundary='Actual teacher-imitation training, not a gameplay or official score. Validation loss and serialization checks do not establish unfamiliar-game improvement.')
    def save():
        report['updated_at_epoch']=time.time()
        tmp=report_path.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2)+'\n');tmp.replace(report_path)
    save()
    try:
        from arc3_lora_export import preflight_export
        report['export_preflight']=preflight_export(output/'export-preflight',Path(__file__).with_name('sglang_gdn_normalizer.py').read_text())
        save()
        manifest=json.loads((args.assets/'manifest.json').read_text())
        for name,record in manifest['files'].items():
            if sha256((args.assets/name).read_bytes()).hexdigest()!=record['sha256']:
                raise ValueError('Training asset changed: '+name)
        report['dataset_sha256']={s:manifest['files']['16k/'+s+'.jsonl']['sha256'] for s in ['train','validation']}
        train=[json.loads(line) for line in (args.assets/'16k/train.jsonl').read_text().splitlines()]
        validation=[json.loads(line) for line in (args.assets/'16k/validation.jsonl').read_text().splitlines()]
        split=json.loads((args.assets/'split.json').read_text())['games']
        if any(split[r['metadata']['game_id']]!='train' for r in train):raise ValueError('Training game split violation')
        if any(split[r['metadata']['game_id']]!='validation' for r in validation):raise ValueError('Validation game split violation')
        # A fixed two-example sample per validation game, selected without student losses.
        grouped=defaultdict(list)
        for row in validation:grouped[row['metadata']['game_id']].append(row)
        validation_sample=[]
        for game,rows in sorted(grouped.items()):
            validation_sample.extend(sorted(rows,key=lambda r:sha256(('arc3-fixed-val-v1/'+r['example_id']).encode()).hexdigest())[:2])
        report['validation_sample_ids']=[r['example_id'] for r in validation_sample]
        namespace={};exec((args.assets/'arc3_training_collator.py').read_text(),namespace)
        collate=namespace['collate_example']
        processor=AutoProcessor.from_pretrained(args.processor,local_files_only=True,trust_remote_code=False)
        native=AutoModelForImageTextToText.from_pretrained(args.model,torch_dtype=torch.bfloat16,
            device_map={'':'cuda:0'},attn_implementation='sdpa',local_files_only=True,trust_remote_code=False)
        native.config.use_cache=False
        targets=select_lora_targets(name for name,module in native.named_modules() if isinstance(module,torch.nn.Linear))
        if len(targets)!=400:raise ValueError('Unexpected supported language adapter placement')
        model=get_peft_model(native,LoraConfig(r=16,lora_alpha=32,target_modules=targets,lora_dropout=0.0,
            bias='none',task_type='CAUSAL_LM'))
        parameters=[p for p in model.parameters() if p.requires_grad]
        trainable=[name for name,p in model.named_parameters() if p.requires_grad]
        if not parameters or any('lora_' not in name for name in trainable):raise ValueError('Frozen-base invariant violated')
        if sum(p.numel() for p in parameters)!=108789760:raise ValueError('Native adapter shapes differ from the executed CPU module inventory')
        report.update(phase='baseline_validation',trainable_parameters=sum(p.numel() for p in parameters),lora_targets=targets,
            model_loaded_at_epoch=time.time(),training_examples_available=len(train))
        save()
        # Verify selected-position CE against the model's built-in shifted loss
        # on a short actual-checkpoint forward before spending time on training.
        model.eval()
        calibration=processor.tokenizer('Observe the grid, test a hypothesis, compare the outcome and revise the model.',return_tensors='pt',add_special_tokens=False)
        calibration={key:value.to('cuda:0') for key,value in calibration.items()}
        calibration_labels=calibration['input_ids'].clone();calibration_labels[:,:-6]=-100
        calibration_positions=torch.nonzero(calibration_labels[0]!=-100,as_tuple=False).flatten()
        with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16):
            builtin=model(**calibration,labels=calibration_labels,use_cache=False).loss
            chosen=model(**calibration,use_cache=False,logits_to_keep=calibration_positions-1).logits[0]
            selected=functional.cross_entropy(chosen.float(),calibration_labels[0,calibration_positions])
        alignment_error=abs(float(builtin)-float(selected))
        if not math.isfinite(alignment_error) or alignment_error>1e-3:raise ValueError('Selected next-token loss differs from native shifted loss')
        report['native_loss_alignment']=dict(native_loss=float(builtin),selected_loss=float(selected),absolute_error=alignment_error,
            boundary='Short actual-checkpoint mathematical loss alignment check, not an ARC3 capability evaluation.')
        del calibration,calibration_labels,calibration_positions,builtin,chosen,selected
        save()
        def loss_for(row):
            batch,info=collate(row,processor,max_tokens=16384)
            batch={key:value.to('cuda:0') for key,value in batch.items()}
            labels=batch.pop('labels')
            positions=torch.nonzero(labels[0]!=-100,as_tuple=False).flatten()
            if positions.numel()<16 or int(positions.min())<1:raise ValueError('Invalid next-token supervision positions')
            # Compute vocabulary logits only at supervised positions. This is
            # exactly masked next-token CE, avoiding a16K *248K full logits tensor.
            with torch.autocast('cuda',dtype=torch.bfloat16):
                result=model(**batch,use_cache=False,logits_to_keep=positions-1)
                logits=result.logits[0]
            expected=labels[0,positions]
            if logits.shape[0]!=expected.numel():raise ValueError('Selected logits/labels mismatch')
            loss=functional.cross_entropy(logits.float(),expected,reduction='mean')
            return loss,info
        def validate(tag):
            model.eval();weighted=tokens=0;values=[]
            with torch.no_grad():
                for row in validation_sample:
                    loss,info=loss_for(row)
                    if not torch.isfinite(loss):raise FloatingPointError('Non-finite validation loss')
                    n=info['supervised_tokens'];weighted+=float(loss)*n;tokens+=n
                    values.append(dict(example=row['example_id'],loss=float(loss),supervised_tokens=n))
            value=dict(tag=tag,mean_token_loss=weighted/tokens,supervised_tokens=tokens,examples=values)
            report['validation'].append(value);save();return value
        before=validate('before_training')
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        model.enable_input_require_grads()
        optimizer=torch.optim.AdamW(parameters,lr=1e-5,betas=(0.9,0.999),weight_decay=0.0)
        order=list(range(len(train)));random.Random(20261101).shuffle(order)
        report.update(phase='training',training_started_at_epoch=time.time());save()
        durations=[]
        for group_start in range(0,len(order),4):
            # Reserve for at least one more observed-duration group; external
            # notebook timeout still independently bounds a stalled CUDA call.
            estimate=max(durations[-4:],default=60.0)
            if time.time()+estimate*min(4,len(order)-group_start)+30>=args.deadline:break
            model.train();native.model.visual.eval()
            optimizer.zero_grad(set_to_none=True)
            indices=order[group_start:group_start+4];processed=0
            for index in indices:
                if processed and time.time()+max(durations[-4:],default=60.0)+15>=args.deadline:break
                tick=time.time();loss,info=loss_for(train[index])
                if not torch.isfinite(loss):raise FloatingPointError('Non-finite real-checkpoint training loss')
                (loss/len(indices)).backward();torch.cuda.synchronize()
                duration=time.time()-tick;durations.append(duration);processed+=1
                report['training_examples']+=1;report['training_input_tokens']+=info['actual_input_tokens']
                report['supervised_tokens']+=info['supervised_tokens']
                report['examples'].append(dict(example=train[index]['example_id'],loss=float(loss.detach()),wall_seconds=duration,**info))
                save()
            if not processed:break
            if processed<len(indices):
                for parameter in parameters:
                    if parameter.grad is not None:parameter.grad.mul_(len(indices)/processed)
            gradients=[p.grad for p in parameters if p.grad is not None]
            if not gradients or not all(bool(torch.isfinite(g).all()) for g in gradients):raise FloatingPointError('Missing/non-finite actual gradients')
            norm=torch.nn.utils.clip_grad_norm_(parameters,1.0)
            if not torch.isfinite(norm) or float(norm)<=0:raise FloatingPointError('No finite nonzero adapter update')
            optimizer.step();report['optimizer_steps']+=1
            if report['optimizer_steps']==1 or report['optimizer_steps']%8==0:
                model.save_pretrained(output/'checkpoints'/('step-'+str(report['optimizer_steps'])),safe_serialization=True)
            report['last_gradient_norm']=float(norm)
            report['max_gpu_allocated_bytes']=torch.cuda.max_memory_allocated()
            report['max_gpu_reserved_bytes']=torch.cuda.max_memory_reserved()
            print(json.dumps(dict(optimizer_step=report['optimizer_steps'],examples=report['training_examples'],
                last_loss=report['examples'][-1]['loss'],gradient_norm=float(norm))),flush=True)
            save()
        if report['optimizer_steps']<1:raise RuntimeError('No actual optimizer update completed within the training budget')
        optimizer.zero_grad(set_to_none=True)
        report.update(phase='checkpoint_validation',training_finished_at_epoch=time.time());save()
        after=validate('after_training')
        adapter=output/'adapter';model.save_pretrained(adapter,safe_serialization=True)
        nonzero=sum(float(parameter.detach().float().square().sum()) for name,parameter in model.named_parameters() if 'lora_B' in name)
        if not math.isfinite(nonzero) or nonzero<=0:raise ValueError('Saved adapter has no nonzero output update')
        report['adapter_output_squared_norm']=nonzero
        from arc3_lora_export import export_serving_adapter
        report['serving_export']=export_serving_adapter(adapter,output/'serving-adapter',native.config.text_config.to_dict())
        save()
        # Prove the saved adapter loads into a separate adapter slot and is used;
        # zero the original slot after loading so it cannot mask a broken reload.
        model.load_adapter(adapter,adapter_name='reloaded',is_trainable=False)
        model.set_adapter('reloaded')
        with torch.no_grad():
            for name,parameter in model.named_parameters():
                if 'lora_' in name and '.default.' in name:parameter.zero_()
        reloaded=validate('saved_adapter_reloaded')
        error=abs(reloaded['mean_token_loss']-after['mean_token_loss'])
        if error>1e-3:raise ValueError('Saved-adapter reload does not reproduce loss: '+str(error))
        report.update(phase='complete',adapter_files={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p.read_bytes()).hexdigest()) for p in adapter.iterdir() if p.is_file()},
            reloaded_adapter_active=str(model.active_adapter),reload_loss_absolute_error=error,
            validation_loss_delta=after['mean_token_loss']-before['mean_token_loss'],
            training_epoch_fraction=report['training_examples']/len(train),
            finished_at_epoch=time.time(),serving_verified=False,gameplay_improvement_verified=False,official_submission_eligible=False)
        save()
    except BaseException as exc:
        report.update(phase='failed',error_type=type(exc).__name__,error=str(exc)[:800]);save();raise


if __name__=='__main__':main()
