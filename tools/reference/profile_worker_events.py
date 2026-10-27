"""Diagnostic worker measuring graph/copy envelopes with CUDA Events.

Invoke through benchmark_submission.py from the project root, using the exact
selected preset. Requires an allocated GPU compute node. Event instrumentation
affects timing; graph envelopes include small internal gaps and are not exact
kernel activity. Preserve the normal worker for formal end-to-end comparisons.
"""
import sys, time, resource, json, os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import torch
from supership import fast_worker as fw
EVENTS=[]; TARGETS={}; ARMED=False

def mark(name,fn,*a,**kw):
    start=torch.cuda.Event(enable_timing=True); end=torch.cuda.Event(enable_timing=True)
    start.record(); result=fn(*a,**kw); end.record()
    EVENTS.append((name,start,end))
    return result
class Graph:
    def __init__(self,wrapped): self.wrapped=wrapped
    def replay(self): return mark('graph',self.wrapped.replay)
init0=fw.Runtime.__init__
def init(self,*a,**kw):
    init0(self,*a,**kw)
    TARGETS[id(self.images)]='image_h2d'
    for host in self.host_outputs: TARGETS[id(host)]='output_d2h'
    self.graph=Graph(self.graph)
fw.Runtime.__init__=init
copy0=torch.Tensor.copy_
def copy(tensor,*a,**kw):
    name=TARGETS.get(id(tensor)) if ARMED else None
    if name: return mark(name,copy0,tensor,*a,**kw)
    return copy0(tensor,*a,**kw)
torch.Tensor.copy_=copy
run0=fw.Runtime.run
def run(self,request):
    global ARMED
    origin=torch.cuda.Event(enable_timing=True); origin.record()
    before=resource.getrusage(resource.RUSAGE_SELF); t=time.perf_counter(); ARMED=True
    result=run0(self,request)
    core=(time.perf_counter()-t)*1000; ARMED=False
    after=resource.getrusage(resource.RUSAGE_SELF)
    spans=[dict(name=name,start_ms=origin.elapsed_time(start),end_ms=origin.elapsed_time(end)) for name,start,end in EVENTS]
    merged=[]
    for span in sorted(spans,key=lambda r:r['start_ms']):
        a,b=span['start_ms'],span['end_ms']
        if not merged or a>merged[-1][1]: merged.append([a,b])
        else: merged[-1][1]=max(merged[-1][1],b)
    union=sum(b-a for a,b in merged)
    width=merged[-1][1]-merged[0][0]
    metrics=dict(core_ms=core,user_ms=(after.ru_utime-before.ru_utime)*1000,system_ms=(after.ru_stime-before.ru_stime)*1000,gpu_envelope_union_ms=union,gpu_span_ms=width,between_envelopes_gap_ms=width-union,spans=spans)
    print('EVENT_PROBE '+json.dumps(metrics),file=sys.stderr,flush=True)
    return result
fw.Runtime.run=run
fw.main()
