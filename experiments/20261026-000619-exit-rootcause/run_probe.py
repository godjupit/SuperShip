"""Run a uniquely named, recorded exit diagnostic under the unchanged timer."""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--trace',action='store_true');p.add_argument('--runs',type=int,default=3);p.add_argument('--mode',default='boundary');p.add_argument('--sample',action='store_true');a=p.parse_args()
out=root/'output'/exp.name/a.name;out.mkdir(parents=True,exist_ok=False)
env=os.environ.copy();env.update(json.loads((exp/'config.json').read_text()));env['EXIT_PROBE_MODE']=a.mode
if a.sample:env['EXIT_SAMPLE_MARKER']=str(out/'exit-marker.json')
python=env['PYTHON_BIN'];worker=[python,str(exp/'worker_boundary.py')]
if a.trace:worker=['strace','-f','-ttt','-T','-e','trace=exit_group,munmap,close,ioctl','-o',str(out/'strace.log'),*worker]
cmd=[python,str(exp/'observe_exit.py'),'--image-dir','data/SuperShip/reference/images','--meta-file','data/SuperShip/reference/reference_images_meta.json','--output-file',str(out/'predictions.json'),'--runs',str(a.runs),'--',*worker]
record=dict(command=cmd,env_overrides={**json.loads((exp/'config.json').read_text()),'EXIT_PROBE_MODE':a.mode},source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip())
(out/'command.json').write_text(json.dumps(record,indent=2)+'\n')
with (out/'stdout.log').open('w') as stdout,(out/'stderr.log').open('w') as stderr:r=subprocess.run(cmd,cwd=root,env=env,stdout=stdout,stderr=stderr)
print(out,r.returncode);print((out/'stdout.log').read_text());print((out/'stderr.log').read_text()[-4000:]);sys.exit(r.returncode)
