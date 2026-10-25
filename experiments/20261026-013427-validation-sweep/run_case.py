"""Run one registered hypothesis through the unchanged full worker protocol."""
import argparse,hashlib,json,os,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('variant');p.add_argument('--name');p.add_argument('--runs',type=int,default=3);p.add_argument('--split',choices=['validation'],default='validation');p.add_argument('--combined-log',action='store_true');p.add_argument('--clean-preset',action='store_true');p.add_argument('--boundary',action='store_true');a=p.parse_args()
case=root/'output'/exp.name/(a.name or a.variant);case.mkdir(parents=True,exist_ok=False)
config=json.loads((exp/'variants'/f'{a.variant}.json').read_text());env=os.environ.copy();removed=[]
if a.clean_preset:
 for k in json.loads((exp/'variants/control.json').read_text()):
  if k not in config:env.pop(k,None);removed.append(k)
env.update(config);python=config['PYTHON_BIN'];split='reference' if a.split=='reference' else 'val'
meta='data/SuperShip/reference/reference_images_meta.json' if split=='reference' else 'data/SuperShip/val/annotations/instances_val.json';gt='data/SuperShip/reference/annotations/instances_reference.json' if split=='reference' else meta
worker=['bash','run.sh','--worker'];timer='supership/benchmark_submission.py'
if a.boundary:
 worker=[python,'experiments/20261026-002932-profile-thp/worker.py'];timer='experiments/20261026-002932-profile-thp/observe.py';env['PROFILE_MODE']='io'
cmd=[python,timer,'--image-dir',f'data/SuperShip/{split}/images','--meta-file',meta,'--output-file',str(case/'predictions.json'),'--runs',str(a.runs),'--',*worker]
record=dict(variant=a.variant,name=case.name,split=a.split,command=cmd,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),config=config,diagnostic=a.boundary,removed_env=removed)
(case/'command.json').write_text(json.dumps(record,indent=2)+'\n')
stdout_name='supership.out' if a.combined_log else 'stdout.log'
with (case/stdout_name).open('x') as stdout:
 if a.combined_log:r=subprocess.run(cmd,cwd=root,env=env,stdout=stdout,stderr=subprocess.STDOUT)
 else:
  with (case/'stderr.log').open('x') as stderr:r=subprocess.run(cmd,cwd=root,env=env,stdout=stdout,stderr=stderr)
text=(case/stdout_name).read_text();err=text if a.combined_log else (case/'stderr.log').read_text()
record['return_code']=r.returncode
if r.returncode:
 record['status']='failed';(case/'metrics.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));sys.exit(1)
record.update(next(json.loads(l) for l in text.splitlines() if l.startswith('{') and 'runs_seconds' in l));scores=[]
assert len(re.findall('processed '+('200' if split=='reference' else '1030')+' images',err))==a.runs
for i in range(a.runs):
 pred=case/(f'predictions.run{i+1}.json' if a.runs>1 else 'predictions.json');scorecmd=[python,'supership/score_submission.py','--gt',gt,'--submission',str(pred)]
 scored=subprocess.run(scorecmd,cwd=root,env=env,capture_output=True,text=True);(case/f'score{i+1}.log').write_text(scored.stdout+scored.stderr)
 if scored.returncode:raise RuntimeError(scored.stderr)
 ap=float(re.search(r'AP@0\.50\s+([\d.]+)',scored.stdout).group(1));scores.append(dict(ap50=ap,sha256=hashlib.sha256(pred.read_bytes()).hexdigest(),score_command=scorecmd))
record['scores']=scores;record['precision_threshold']=(.7935 if split=='reference' else .9170)*.98;record['precision_pass']=all(s['ap50']>=record['precision_threshold'] for s in scores);record['status']='completed' if record['precision_pass'] else 'precision_failed';record['hidden_ap50']=None
if a.combined_log:record['log_sha256']=hashlib.sha256((case/'supership.out').read_bytes()).hexdigest()
(case/'metrics.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(case=case.name,status=record['status'],runs_seconds=record['runs_seconds'],median_seconds=record['median_seconds'],ap50=[s['ap50'] for s in scores])),flush=True)
