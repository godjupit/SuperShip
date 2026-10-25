"""Diagnostic CPU profile after unchanged synthetic initialization; not official timing."""
import argparse,cProfile,json,os,pstats,sys,time,threading
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
profile=cProfile.Profile();start=time.perf_counter();profile.enable()
with torch.inference_mode():detections,images=runtime.run(request)
profile.disable();elapsed=time.perf_counter()-start
s=pstats.Stats(profile)
rows=[dict(file=k[0],line=k[1],function=k[2],primitive_calls=v[0],calls=v[1],self_seconds=v[2],cumulative_seconds=v[3]) for k,v in s.stats.items()]
rows.sort(key=lambda x:x['cumulative_seconds'],reverse=True)
Path(a.stats).write_text(json.dumps(dict(scope='Instrumented diagnostic; main-thread cumulative times nest; load durations overlap',runtime_seconds=elapsed,images=images,detections=detections,load_tasks=len(loads),load_sum_seconds=sum(b-a for a,b in loads),load_wall_span_seconds=max(b for a,b in loads)-min(a for a,b in loads),functions=rows),indent=2)+'\n')
print(json.dumps(dict(images=images,detections=detections,runtime_seconds=elapsed)))
