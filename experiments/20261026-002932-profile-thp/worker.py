"""Diagnostic worker: preserve input/exit protocol; instrument only real run()."""
import collections,json,linecache,os,sys,threading,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import torch
from supership.fast_worker import Runtime
from supership.generate_submission import read_worker_request
runtime=Runtime();torch.cuda.synchronize()
mode=os.environ['PROFILE_MODE'];loads=[];cv_calls=[];lock=threading.Lock()
if mode=='line':
    original=runtime.load_image
    def load(*args,**kwargs):
        start=time.perf_counter_ns()
        try:return original(*args,**kwargs)
        finally:
            with lock:loads.append((start,time.perf_counter_ns(),args[0]['id']))
    runtime.load_image=load
    import cv2
    def wrap_cv(name):
        fn=getattr(cv2,name)
        def wrapped(*args,**kwargs):
            start=time.perf_counter_ns()
            try:return fn(*args,**kwargs)
            finally:
                with lock:cv_calls.append((name,start,time.perf_counter_ns()))
        return wrapped
    for name in ['imread','resize','cvtColor']:setattr(cv2,name,wrap_cv(name))
print('THU_RS_READY',flush=True)
request=read_worker_request();received=time.monotonic_ns()
line_ns=collections.Counter();calls=collections.Counter();intervals=[];state=[None,None];target=Runtime.run.__code__
def trace(frame,event,arg):
    if frame.f_code is not target:return None
    if event in ('line','return'):
        now=time.perf_counter_ns()
        if state[0] is not None:
            line_ns[state[0]]+=now-state[1];intervals.append((state[0],state[1],now))
        state[:]=frame.f_lineno,now
        if event=='line':calls[frame.f_lineno]+=1
    return trace
if mode=='nsys':torch.cuda.cudart().cudaProfilerStart()
if mode=='line':sys.settrace(trace)
start=time.monotonic_ns()
try:
    with torch.inference_mode():detections,images=runtime.run(request)
finally:
    if mode=='line':sys.settrace(None)
finished=time.monotonic_ns()
if mode=='nsys':torch.cuda.cudart().cudaProfilerStop()
rows=[dict(line=k,source=linecache.getline(target.co_filename,k).strip(),milliseconds=v/1e6,calls=calls[k]) for k,v in line_ns.items()]
record=dict(mode=mode,request_received_ns=received,run_started_ns=start,run_finished_ns=finished,runtime_ms=(finished-start)/1e6,images=images,detections=detections,lines=rows,intervals=intervals,loads=loads,cv_calls=cv_calls,scope='diagnostic; main-thread line intervals are exclusive; background load/GPU times overlap')
Path(request['output_file']).with_suffix('.stages.json').write_text(json.dumps(record,indent=2)+'\n')
print(f'processed {images} images; wrote {detections} detections',file=sys.stderr,flush=True)
print(json.dumps(dict(diagnostic='boundary',mode=mode,request_received_ns=received,run_started_ns=start,run_finished_ns=finished,before_exit_ns=time.monotonic_ns())),file=sys.stderr,flush=True)
os._exit(0)
