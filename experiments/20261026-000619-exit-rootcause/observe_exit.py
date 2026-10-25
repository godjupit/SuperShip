"""Observe timestamps around existing timer functions without changing their logic.
Diagnostic only: normal official benchmark scores are separately retained.
"""
import json,sys,time,os,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from supership import benchmark_submission as official
records=[];requests=[]
original_exit=official.record_exit;original_send=official.send_request

def record_exit(process,completed,result):
    sampler=None
    marker=os.environ.get('EXIT_SAMPLE_MARKER')
    if marker:
        sampler=subprocess.Popen(['sudo','-n','/usr/bin/python3',str(Path(__file__).with_name('sample_proc.py')),marker,str(process.pid),marker+'.stacks.json'])
    original_exit(process,completed,result)
    if sampler: sampler.wait(timeout=10)
    records.append(dict(pid=process.pid,**result))

def send_request(stream,request,deadline):
    started=time.monotonic_ns();original_send(stream,request,deadline)
    requests.append(dict(send_started_ns=started,send_finished_ns=time.monotonic_ns()))

official.record_exit=record_exit;official.send_request=send_request
official.main()
print(json.dumps(dict(diagnostic='parent-observation',requests=requests,exits=records)))
