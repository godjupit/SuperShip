"""Diagnostic worker identical core runtime, with timestamp immediately before exit."""
import json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from supership.fast_worker import Runtime
from supership.generate_submission import read_worker_request
runtime=Runtime()
print('THU_RS_READY',flush=True)
request=read_worker_request();received=time.monotonic_ns()
detections,images=runtime.run(request);finished=time.monotonic_ns()
print(f'processed {images} images; wrote {detections} detections',file=sys.stderr,flush=True)
print(json.dumps(dict(diagnostic='worker-boundary',request_received_ns=received,run_finished_ns=finished,runtime_seconds=(finished-received)/1e9,before_exit_ns=time.monotonic_ns())),file=sys.stderr,flush=True)
sys.stdout.flush();sys.stderr.flush()
os._exit(0)
