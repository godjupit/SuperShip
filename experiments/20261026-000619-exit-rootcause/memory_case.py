"""Run the complete validation worker inside a preconfigured 32GiB cgroup."""
import json,os,subprocess,sys,threading,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent
label=sys.argv[1];out=root/'output'/exp.name/('memory32-'+(sys.argv[2] if len(sys.argv)>2 else label));out.mkdir(parents=True,exist_ok=False)
env=os.environ.copy();env.update(json.loads((exp/'config.json').read_text()));env['HOST_THP']='1' if label=='candidate' else '0';env.pop('GLIBC_TUNABLES',None)
cgroup=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
limit=(cgroup/'memory.max').read_text().strip();assert limit==str(32*1024**3),limit
python=env['PYTHON_BIN'];meta='data/SuperShip/val/annotations/instances_val.json'
cmd=[python,'supership/benchmark_submission.py','--image-dir','data/SuperShip/val/images','--meta-file',meta,'--output-file',str(out/'predictions.json'),'--runs','1','--','/usr/bin/time','-v','-o',str(out/'time.txt'),'bash','run.sh','--worker']
(out/'command.json').write_text(json.dumps(dict(command=cmd,env_overrides={**json.loads((exp/'config.json').read_text()),'HOST_THP':env['HOST_THP']},source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()),indent=2)+'\n')
sampled_peak=[0];stop=threading.Event()
def sample():
    while not stop.is_set():
        sampled_peak[0]=max(sampled_peak[0],int((cgroup/'memory.current').read_text()))
        stop.wait(.01)
thread=threading.Thread(target=sample,daemon=True);thread.start()
r=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True);(out/'stdout.log').write_text(r.stdout);(out/'stderr.log').write_text(r.stderr)
if r.returncode:raise RuntimeError(r.stderr)
score=[python,'supership/score_submission.py','--gt',meta,'--submission',str(out/'predictions.json')]
s=subprocess.run(score,cwd=root,env=env,capture_output=True,text=True);(out/'score.log').write_text(s.stdout+s.stderr)
if s.returncode:raise RuntimeError(s.stderr)
stop.set();thread.join()
record=dict(label=label,cgroup=str(cgroup),memory_max_bytes=int(limit),sampled_cgroup_peak_bytes=sampled_peak[0],memory_events=(cgroup/'memory.events').read_text(),time_report=(out/'time.txt').read_text(),scope='cgroup contains timer, complete worker including init, descendants and scoring; full validation1030 images')
(out/'memory.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
