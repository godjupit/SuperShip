"""Diagnostic line timing after unchanged synthetic initialization; not official timing."""
import argparse,json,os,sys,time,threading,collections,linecache
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--stats',required=True);a=p.parse_args()
if Path(a.output).exists() or Path(a.stats).exists():p.error('Output exists; choose unique experiment paths')
os.environ.update(json.loads(Path(a.config).read_text()));sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import torch
from supership.fast_worker import Runtime
runtime=Runtime();torch.cuda.synchronize()
loads=[];original_load=runtime.load_image
lock=threading.Lock()
def load(*args,**kwargs):
    t=time.perf_counter()
    try:return original_load(*args,**kwargs)
    finally:
        with lock:loads.append((t,time.perf_counter()))
runtime.load_image=load
request=dict(image_dir='data/SuperShip/reference/images',meta_file='data/SuperShip/reference/reference_images_meta.json',output_file=a.output)
target=Runtime.run.__code__;line_seconds=collections.defaultdict(float);line_calls=collections.Counter();state=[None,None]
def trace(frame,event,arg):
    if frame.f_code is not target:return None
    if event in ('line','return'):
        now=time.perf_counter()
        if state[0] is not None:line_seconds[state[0]]+=now-state[1]
        state[:]=[frame.f_lineno,now]
        if event=='line':line_calls[frame.f_lineno]+=1
    return trace
start=time.perf_counter();sys.settrace(trace)
try:
    with torch.inference_mode():detections,images=runtime.run(request)
finally:sys.settrace(None)
elapsed=time.perf_counter()-start
rows=[dict(line=k,source=linecache.getline(target.co_filename,k).strip(),seconds=v,calls=line_calls[k]) for k,v in line_seconds.items()]
rows.sort(key=lambda x:x['seconds'],reverse=True)
Path(a.stats).write_text(json.dumps(dict(scope='Line-traced main Runtime.run; inclusive calls, mutually exclusive line intervals; background load durations overlap',runtime_seconds=elapsed,images=images,detections=detections,load_tasks=len(loads),load_sum_seconds=sum(b-a for a,b in loads),load_wall_span_seconds=max(b for a,b in loads)-min(a for a,b in loads),lines=rows),indent=2)+'\n')
print(json.dumps(dict(images=images,detections=detections,runtime_seconds=elapsed)))
