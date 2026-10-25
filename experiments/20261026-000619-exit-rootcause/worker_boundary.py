"""Diagnostic worker identical core runtime, with timestamp immediately before exit."""
import json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from supership.fast_worker import Runtime
from supership.generate_submission import read_worker_request
runtime=Runtime()
import torch
mode=os.environ.get('EXIT_PROBE_MODE','boundary')
print(json.dumps(dict(diagnostic='ready-memory',allocated=torch.cuda.memory_allocated(),reserved=torch.cuda.memory_reserved(),host_maps=len(Path('/proc/self/maps').read_text().splitlines()))),file=sys.stderr,flush=True)
if mode=='empty-cache':
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    print(json.dumps(dict(diagnostic='trimmed-memory',allocated=torch.cuda.memory_allocated(),reserved=torch.cuda.memory_reserved())),file=sys.stderr,flush=True)
if os.environ.get('EXIT_KERNEL_TRACE')=='1':
    marker=Path(os.environ['EXIT_SAMPLE_MARKER']);marker.with_suffix('.ready').touch()
    deadline=time.monotonic()+15
    while not marker.with_suffix('.armed').exists():
        if time.monotonic()>deadline:raise RuntimeError('kernel trace helper failed to arm')
        time.sleep(.005)
print('THU_RS_READY',flush=True)
request=read_worker_request();received=time.monotonic_ns()
detections,images=runtime.run(request);finished=time.monotonic_ns()
print(f'processed {images} images; wrote {detections} detections',file=sys.stderr,flush=True)
print(json.dumps(dict(diagnostic='worker-boundary',request_received_ns=received,run_finished_ns=finished,runtime_seconds=(finished-received)/1e9,before_exit_ns=time.monotonic_ns())),file=sys.stderr,flush=True)
sys.stdout.flush();sys.stderr.flush()
marker=os.environ.get('EXIT_SAMPLE_MARKER')
if marker:Path(marker).write_text(json.dumps({'pid':os.getpid(),'ns':time.monotonic_ns()}))
if mode=='device-reset':
    import ctypes
    started=time.monotonic_ns()
    cudart=ctypes.CDLL(str(Path(torch.__file__).resolve().parent.parent/'nvidia/cuda_runtime/lib/libcudart.so.12'))
    cudart.cudaDeviceReset.restype=ctypes.c_int
    code=cudart.cudaDeviceReset()
    print(json.dumps(dict(diagnostic='device-reset',code=code,duration_ns=time.monotonic_ns()-started)),file=sys.stderr,flush=True)
os._exit(0)
