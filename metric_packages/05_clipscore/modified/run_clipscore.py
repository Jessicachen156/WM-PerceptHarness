"""Prompt-window input adapter; all CLIP scoring stays in pinned VBench code."""
import argparse, csv, hashlib, importlib.metadata, json, os, shutil, subprocess, sys, time
from official_runtime import load_clip_functions, verify_official, read_manifest, exact_prompt, verify_checkpoint, require_persistent_remote_session
from pathlib import Path

OUT = None

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    tmp.replace(path)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''): h.update(b)
    return h.hexdigest()

def publish(rows):
    records=[]
    for row in rows:
        p=OUT/'results'/row['model']/(row['sample_id']+'.json')
        if p.exists(): records.append(json.loads(p.read_text(encoding='utf-8')))
    data={'updated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'expected_videos':len(rows),'reported_videos':len(records),'models':{}}
    for model in ['wan','lingbot-dense']:
        complete=[x for x in records if x['model']==model and x['status']=='complete']
        scores=[x['score'] for x in complete]
        windows=[w for x in complete for w in x['windows']]
        data['models'][model]={'complete':len(complete),'failed':sum(x['model']==model and x['status']=='failed' for x in records),'mean':sum(scores)/len(scores) if scores else None,'window_count':len(windows),'truncated_prompts':sum(w['token_count_with_special_tokens']>77 for w in windows)}
    save(OUT/'progress.json',data)
    with (OUT/'scores.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['model','sample_id','status','score','window_count','truncated_prompt_count'])
        w.writeheader()
        for r in records:
            w.writerow({**{k:r.get(k) for k in ['model','sample_id','status','score']},'window_count':len(r.get('windows',[])),'truncated_prompt_count':sum(x['token_count_with_special_tokens']>77 for x in r.get('windows',[]))})
    return data

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True, help='Pre-provisioned OpenAI CLIP ViT-B/32 .pt; never downloaded')
    parser.add_argument('--gpu', help='Optional CUDA_VISIBLE_DEVICES selection')
    parser.add_argument('--limit', type=int)
    args=parser.parse_args()
    if args.limit is not None and args.limit<1: parser.error('--limit must be positive')
    require_persistent_remote_session()
    global OUT
    OUT=args.output_dir.resolve()
    if args.gpu is not None: os.environ['CUDA_VISIBLE_DEVICES']=args.gpu
    import clip, torch, numpy as np, decord
    from clip.clip import _tokenizer
    from decord import VideoReader,cpu
    source=verify_official()
    functions=load_clip_functions()
    clip_alignment=functions['clip_alignment']
    get_frame_indices=functions['get_frame_indices']
    model_path,model_hash=verify_checkpoint(args.checkpoint)
    manifest=args.manifest.resolve(strict=True)
    rows=read_manifest(manifest, 'clip')
    protocol={'metric':'CLIPScore','source':source,'checkpoint_sha256':model_hash,'manifest_sha256':sha(manifest),'adapter_sha256':sha(Path(__file__)),'official_scoring_function':'competitions.clip_score.clip_alignment','sampling':'Unchanged official 8 middle-sampled frames per supplied video/window. Official CLIP ViT-B/32 tokenize(truncate=True), 77-token context.','text_mapping':'Exact saved Wan prompt; LingBot compact JSON serialization of structured_caption.caption, ensure_ascii=False, separators=(comma,colon), matching official caption_from_sample.','temporal_mapping':'Actual inclusive final frame range; adjacent generated windows share one conditioning boundary frame. Full generation prompts use full final video.','aggregation':'Official mean of the segment/window scores for each sample, then equal mean over complete samples. Different prompt structures across models limit direct CLIP comparison.','runtime':{n:importlib.metadata.version(n) for n in ['torch','torchvision','openai-clip','decord','numpy']},'prompt_adaptation_status':'Custom-dataset prompt-window evaluation, not the original VBench benchmark suite.'}
    protocol['device']='cuda'
    protocol['adapter_helper_sha256']=sha(Path(__file__).with_name('official_runtime.py'))
    prior=OUT/'protocol.json'
    if prior.exists() and json.loads(prior.read_text(encoding='utf-8'))!=protocol:
        successes=[p for p in (OUT/'results').glob('*/*.json') if json.loads(p.read_text(encoding='utf-8')).get('status')=='complete']
        if successes: raise RuntimeError('CLIP run identity changed; use a separate output folder')
        shutil.copyfile(prior,OUT/('failed_pilot_protocol_'+sha(prior)[:12]+'.json'))
    save(prior,protocol)
    device=torch.device('cuda')
    clip_model,preprocess=clip.load(str(model_path),device=device)
    selected=rows[:args.limit] if args.limit else rows
    publish(rows)
    for row in selected:
        model,sid=row['model'],row['sample_id']
        result_path=OUT/'results'/model/(sid+'.json')
        if result_path.exists():
            previous=json.loads(result_path.read_text(encoding='utf-8'))
            if previous.get('status')=='complete':
                if previous.get('source_video_sha256')!=row['recorded_final_sha256'] or sha(Path(row['video_path']))!=row['recorded_final_sha256']: raise ValueError('Resume source identity mismatch')
                continue
        started=time.time()
        work=OUT/'work'/model/sid
        work.mkdir(parents=True,exist_ok=True)
        try:
            source_video=Path(row['video_path'])
            video=source_video
            input_hash=sha(video)
            if row.get('recorded_final_sha256') and input_hash!=row['recorded_final_sha256']:
                raise ValueError('Source video differs from frozen complete.json hash')
            segments=row.get('actual_segment_prompts') or [{'prompt':row['prompt'],'prompt_source':row.get('prompt_source'),'final_frame_range_inclusive':None}]
            windows=[]
            info=[]
            decord.bridge.set_bridge('native')
            original=VideoReader(str(video),ctx=cpu(0),num_threads=2)
            actual_frames=len(original)
            if row.get('recorded_evaluation_frames') and actual_frames!=row['recorded_evaluation_frames']:
                raise ValueError('Decoded frame count differs from manifest')
            for i,segment in enumerate(segments):
                prompt=exact_prompt(segment,model)
                if not prompt: raise ValueError('Missing actual prompt text')
                frame_range=segment.get('final_frame_range_inclusive')
                command=None
                scored_video=video
                if frame_range and frame_range!=[0,actual_frames-1]:
                    start,end=frame_range
                    if not (0<=start<=end<actual_frames): raise ValueError('Invalid window range')
                    scored_video=work/f'window_{i:03d}.mp4'
                    command=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-threads','2','-i',str(video),'-map','0:v:0','-vf',f'trim=start_frame={start}:end_frame={end+1},setpts=PTS-STARTPTS','-an','-vsync','0','-c:v','libx264','-preset','ultrafast','-crf','0','-threads','2',str(scored_video)]
                    p=subprocess.run(command,capture_output=True,text=True)
                    if p.returncode: raise RuntimeError(p.stderr[-3000:])
                    cut=VideoReader(str(scored_video),ctx=cpu(0),num_threads=2)
                    if len(cut)!=end-start+1: raise ValueError('Wrong cut frame count')
                    checks=get_frame_indices(8,len(cut),sample='middle',input_fps=cut.get_avg_fps())
                    if not np.array_equal(cut.get_batch(checks).asnumpy(),original.get_batch([start+j for j in checks]).asnumpy()):
                        raise ValueError('Lossless window extraction RGB pixel verification failed')
                    del cut
                tokens=_tokenizer.encode(prompt)
                selected_range=frame_range or [0,actual_frames-1]
                sample_indices=[int(j) for j in get_frame_indices(8,selected_range[1]-selected_range[0]+1,sample='middle')]
                windows.append({'index':i,'prompt':prompt,'prompt_source':segment.get('prompt_source'),'prompt_text_scope':'exact_runtime_text','frame_range_inclusive':selected_range,'official_sample_indices':sample_indices,'source_sample_indices':[selected_range[0]+j for j in sample_indices],'sampled_rgb_identity_verified':True,'token_count_with_special_tokens':len(tokens)+2,'clip_visible_text':_tokenizer.decode(tokens[:75]),'clip_token_ids':clip.tokenize([prompt],truncate=True)[0].tolist(),'video_path':str(scored_video),'video_sha256':sha(scored_video),'extraction_command':command})
                info.append({'prompt':prompt,'video_list':[str(scored_video)]})
            del original
            raw_mean,raw_rows=clip_alignment(clip_model,info,preprocess,device)
            if len(raw_rows)!=len(windows): raise ValueError('Missing official window score')
            for window,scored in zip(windows,raw_rows):
                if window['video_path']!=scored['video_path']: raise ValueError('Official result path mismatch')
                window['score']=float(scored['video_results'])
            result={'model':model,'sample_id':sid,'status':'complete','score':float(raw_mean),'windows':windows,'official_result':[float(raw_mean),raw_rows],'source_video_path':str(source_video),'source_video_sha256':input_hash,'elapsed_s':time.time()-started}
            save(result_path,result)
            # Only remove our verified reproducible scratch windows; source videos remain intact.
            for window in windows:
                path=Path(window['video_path'])
                if path.parent==work and window['extraction_command'] is not None: path.unlink()
            print(model,sid,'complete',len(windows),float(raw_mean),round(time.time()-started,2),flush=True)
        except Exception as error:
            save(result_path,{'model':model,'sample_id':sid,'status':'failed','error':repr(error),'windows':[],'elapsed_s':time.time()-started})
            print(model,sid,'FAILED',repr(error),flush=True)
        publish(rows)
    save(OUT/'batch_finished.json',publish(rows))

if __name__=='__main__': main()
