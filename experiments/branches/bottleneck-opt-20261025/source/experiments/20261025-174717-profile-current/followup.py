"""Keep every repeat after slower E2E and low GPU coverage; no score submission."""
import datetime,hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];EXP=Path(__file__).resolve().parent;OUT=ROOT/'output'/EXP.name;PY='/home/ubuntu/.cache/supership-venv/bin/python';NSYS='/home/ubuntu/.local/opt/nsight-systems-2024.2.3/bin/nsys'
os.chdir(ROOT);env=os.environ|json.loads((EXP/'config.json').read_text());commands=[]
if (EXP/'followup-metrics.json').exists():raise FileExistsError('Followup already has metrics; choose a new experiment directory')
metric=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),started=datetime.datetime.now().isoformat(),reason='Initial E2E slower than history, GPU kernel sum stable but timeline coverage lower; original trials retained',hidden_ap50=None,competition_submitted=False)
def run(cmd,label):
 if (OUT/(label+'.log')).exists():raise FileExistsError('Refusing to overwrite existing log: '+label)
 commands.append(dict(argv=cmd,label=label));(EXP/'followup-commands.json').write_text(json.dumps(commands,indent=2)+'\n');print('START',label,flush=True)
 with (OUT/(label+'.log')).open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 if r.returncode:raise RuntimeError(label)
 print('DONE',label,flush=True);return (OUT/(label+'.log')).read_text()
def score(pred,label):
 text=run([PY,'supership/score_submission.py','--gt','data/SuperShip/reference/annotations/instances_reference.json','--submission',str(pred)],label)
 sys.path.insert(0,str(ROOT));from supership.submission import validate_output
 return dict(ap50=float(re.search(r'AP@0.50\s+([0-9.]+)',text).group(1)),detections=validate_output(str(pred),'data/SuperShip/reference/reference_images_meta.json'))
try:
 text=run([PY,'supership/benchmark_submission.py','--image-dir','data/SuperShip/reference/images','--meta-file','data/SuperShip/reference/reference_images_meta.json','--output-file',str(OUT/'repeat.json'),'--runs','3','--','env','PYTHON_BIN='+PY,'bash','run.sh','--worker'],'repeat-benchmark')
 metric.update(json.loads(next(l for l in reversed(text.splitlines()) if l.startswith('{"runs_seconds"'))))
 metric['reference_checks']=[score(OUT/f'repeat.run{i}.json',f'repeat-score{i}') for i in range(1,4)]
 for i in range(1,4):
  run([PY,str(EXP/'stages_line.py'),'--config',str(EXP/'config.json'),'--output',str(OUT/f'line{i}-predictions.json'),'--stats',str(EXP/f'line{i}.json')],f'line{i}')
  metric[f'line{i}']=score(OUT/f'line{i}-predictions.json',f'line{i}-score')
 run([NSYS,'profile','--trace=cuda,nvtx,osrt','--sample=none','--cpuctxsw=none','--cuda-graph-trace=node','--capture-range=cudaProfilerApi','--capture-range-end=stop','-o',str(OUT/'inference-repeat'),PY,'tools/reference/profile_fastest_range.py','--config',str(EXP/'config.json'),'--output',str(OUT/'nsys-repeat-predictions.json')],'nsys-repeat-profile')
 run([NSYS,'export','--type','sqlite','--output',str(OUT/'inference-repeat.sqlite'),str(OUT/'inference-repeat.nsys-rep')],'nsys-repeat-export')
 run([PY,'tools/reference/summarize_nsys.py',str(OUT/'inference-repeat.sqlite'),str(EXP/'nsys-repeat-summary.json')],'nsys-repeat-summary')
 metric['nsys_repeat']=score(OUT/'nsys-repeat-predictions.json','nsys-repeat-score');metric['status']='completed'
finally:
 metric['finished']=datetime.datetime.now().isoformat();(EXP/'followup-metrics.json').write_text(json.dumps(metric,indent=2)+'\n')
