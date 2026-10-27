"""Diagnostic worker, invoked by benchmark_submission.py from the project root.

Load configs/presets/thread100-light.json into the environment before launch.
PROBE_TRACE=1 additionally exports a CPU/CUDA Chrome trace beside the prediction.
Uses the original READY/request/output protocol and preserves prediction bytes.
Instrumentation and trace export affect timing: never use this worker for scores.
Requires an allocated GPU compute node, including for CPU-only stage analysis.
"""
import ast, inspect, textwrap, time, resource, json, sys, os, collections, contextlib
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import torch, cv2
from supership import fast_worker as fw
PROF=os.environ.get('PROBE_TRACE','0')=='1'
SAMPLES=collections.defaultdict(list)
@contextlib.contextmanager
def span(name):
    record=torch.profiler.record_function(name) if PROF else contextlib.nullcontext()
    with record:
        t=time.perf_counter_ns(); c=time.thread_time_ns()
        try: yield
        finally: SAMPLES[name].append(((time.perf_counter_ns()-t)/1e6,(time.thread_time_ns()-c)/1e6))

def instrument(fn,name):
    def wrapped(*a,**kw):
        with span(name): return fn(*a,**kw)
    return wrapped
for name in ['imread','resize','cvtColor']:
    setattr(cv2,name,instrument(getattr(cv2,name),'cv2_'+name))
fw.serialized_batch=instrument(fw.serialized_batch,'json_encode_worker')
fw.Runtime.load_image=instrument(fw.Runtime.load_image,'loader_total')
def load_after_copy(self,event,item,image_dir,destination):
    with span('loader_input_reuse_wait'): event.synchronize()
    return self.load_image(item,image_dir,destination)
fw.Runtime.load_after_copy=load_after_copy
os.fsync=instrument(os.fsync,'output_fsync')
source=textwrap.dedent(inspect.getsource(fw.Runtime.run))
tree=ast.parse(source)
class Stages(ast.NodeTransformer):
    def visit(self,node):
        if isinstance(node,ast.stmt) and not isinstance(node,(ast.FunctionDef,ast.ClassDef)):
            code=ast.unparse(node)
            label=None
            if isinstance(node,ast.Assign):
                if code.startswith('loaded = '): label='main_input_future_wait'
                elif code.startswith('chunks = '): label='main_json_future_wait'
                elif code.startswith('payload = '): label='main_payload_assemble'
            elif isinstance(node,ast.Expr):
                if code.startswith('event.synchronize('): label='main_output_event_wait'
                elif code.startswith('self.images.copy_('): label='main_h2d_submit'
                elif code.startswith('self.sizes[:n].copy_('): label='main_sizes_prepare'
                elif code.startswith('self.graph.replay('): label='main_graph_submit'
                elif code.startswith('collect('): label='main_collect_submit'
                elif code.startswith('self.pool.shutdown('): label='main_loader_join'
                elif code.startswith('torch.cuda.synchronize('): label='main_device_sync'
            elif isinstance(node,ast.With) and 'path.open' in ast.unparse(node.items[0].context_expr):
                label='main_output_write_close'
            if label:
                node=self.generic_visit(node)
                return ast.copy_location(ast.With(items=[ast.withitem(context_expr=ast.Call(func=ast.Name(id='span',ctx=ast.Load()),args=[ast.Constant(label)],keywords=[]))],body=[node]),node)
        return super().visit(node)
tree=Stages().visit(tree); ast.fix_missing_locations(tree)
namespace=dict(fw.__dict__,span=span)
exec(compile(tree,'<diagnostic_runtime_run>','exec'),namespace)
original_run=namespace['run']
original_init=fw.Runtime.__init__
def init(self,*a,**kw):
    original_init(self,*a,**kw)
    smaps=Path('/proc/self/smaps_rollup').read_text()
    print('PROBE_INIT '+json.dumps({line.split(':')[0]:line.split(':',1)[1].strip() for line in smaps.splitlines() if line.startswith(('Rss:','AnonHugePages:','Anonymous:'))}),file=sys.stderr,flush=True)
fw.Runtime.__init__=init

def run(self,request):
    mode='trace' if PROF else 'light'
    trace=None
    if PROF:
        trace=torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA], record_shapes=False, with_stack=False, profile_memory=False)
    before=resource.getrusage(resource.RUSAGE_SELF)
    io0=Path('/proc/self/io').read_text()
    started=time.perf_counter()
    with trace if trace else contextlib.nullcontext():
        result=original_run(self,request)
    core=time.perf_counter()-started
    after=resource.getrusage(resource.RUSAGE_SELF)
    summary={name:dict(calls=len(samples),wall_ms=sum(x[0] for x in samples),thread_cpu_ms=sum(x[1] for x in samples),max_wall_ms=max(x[0] for x in samples)) for name,samples in SAMPLES.items()}
    metrics=dict(mode=mode,core_ms=core*1000,user_ms=(after.ru_utime-before.ru_utime)*1000,system_ms=(after.ru_stime-before.ru_stime)*1000,max_rss_kb=after.ru_maxrss,voluntary_switches=after.ru_nvcsw-before.ru_nvcsw,involuntary_switches=after.ru_nivcsw-before.ru_nivcsw,stages=summary,io_before=io0,io_after=Path('/proc/self/io').read_text())
    print('PROBE_RESULT '+json.dumps(metrics),file=sys.stderr,flush=True)
    if trace:
        trace.export_chrome_trace(str(Path(request['output_file']).with_suffix('.trace.json')))
        print(trace.key_averages().table(sort_by='self_cuda_time_total',row_limit=20),file=sys.stderr,flush=True)
    return result
fw.Runtime.run=run
fw.main()
