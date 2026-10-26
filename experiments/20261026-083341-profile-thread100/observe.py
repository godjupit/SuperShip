"""Observe unchanged timer functions for diagnostic request/exit boundaries."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from supership import benchmark_submission as official
exits=[];requests=[];wait=official.record_exit;send=official.send_request
def record_exit(process,completed,result):
    wait(process,completed,result);exits.append(dict(pid=process.pid,**result))
def send_request(stream,request,deadline):
    start=time.monotonic_ns();send(stream,request,deadline);requests.append(dict(start_ns=start,end_ns=time.monotonic_ns()))
official.record_exit=record_exit;official.send_request=send_request;official.main()
print(json.dumps(dict(diagnostic='parent',exits=exits,requests=requests)))
