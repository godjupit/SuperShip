"""Reproduce official benchmark and separate diagnostic runs; no competition submission."""
import datetime,hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];EXP=Path(__file__).resolve().parent;OUT=ROOT/'output'/EXP.name;PY='/home/ubuntu/.cache/supership-venv/bin/python';NSYS='/home/ubuntu/.local/opt/nsight-systems-2024.2.3/bin/nsys'
os.chdir(ROOT);cfg=json.loads((EXP/'config.json').read_text());env=os.environ|cfg
# Explicitly remove unrelated inherited configuration; all runtime overrides are versioned.
for key in list(env):
    if key.startswith(('KERNEL_','FEATURE_CAT')) and key not in cfg:env.pop(key)
commands=[]
def run(cmd,label,timeout=600):
    if (OUT/(label+'.log')).exists():raise FileExistsError('Refusing to overwrite existing log: '+label)
    commands.append(dict(label=label,argv=cmd,cwd=str(ROOT)));(EXP/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    print('START',label,flush=True)
    with (OUT/(label+'.log')).open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    if r.returncode:raise RuntimeError(f'{label}: exit {r.returncode}; see log')
    print('DONE',label,flush=True);return (OUT/(label+'.log')).read_text()
def score(pred,split,label):
    gt=f'data/SuperShip/{split}/annotations/instances_{split}.json'
    text=run([PY,'supership/score_submission.py','--gt',gt,'--submission',str(pred)],label)
    return float(re.search(r'AP@0.50\s+([0-9.]+)',text).group(1))
def validate(pred,split):
    sys.path.insert(0,str(ROOT));from supership.submission import validate_output
    meta='data/SuperShip/reference/reference_images_meta.json' if split=='reference' else 'data/SuperShip/val/annotations/instances_val.json'
    return validate_output(str(pred),meta)
if (EXP/'metrics.json').exists():raise FileExistsError('Experiment already has metrics; choose a new experiment directory')
metrics=dict(status='running',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),started=datetime.datetime.now().isoformat(),hidden_ap50=None,competition_submitted=False,config=cfg)
try:
    text=run([PY,'supership/benchmark_submission.py','--image-dir','data/SuperShip/reference/images','--meta-file','data/SuperShip/reference/reference_images_meta.json','--output-file',str(OUT/'reference.json'),'--runs','3','--','env','PYTHON_BIN='+PY,'bash','run.sh','--worker'],'reference-benchmark')
    metrics.update(json.loads(next(l for l in reversed(text.splitlines()) if l.startswith('{"runs_seconds"'))))
    metrics['reference_ap50']=[score(OUT/f'reference.run{i}.json','reference',f'reference-score{i}') for i in range(1,4)]
    metrics['reference_output_checks']=[validate(OUT/f'reference.run{i}.json','reference') for i in range(1,4)]
    run([PY,'supership/benchmark_submission.py','--image-dir','data/SuperShip/val/images','--meta-file','data/SuperShip/val/annotations/instances_val.json','--output-file',str(OUT/'validation.json'),'--runs','1','--','env','PYTHON_BIN='+PY,'bash','run.sh','--worker'],'validation-benchmark')
    metrics['validation_ap50']=score(OUT/'validation.json','val','validation-score');metrics['validation_output_check']=validate(OUT/'validation.json','val')
    run([NSYS,'profile','--trace=cuda,nvtx,osrt','--sample=none','--cpuctxsw=none','--cuda-graph-trace=node','--capture-range=cudaProfilerApi','--capture-range-end=stop','-o',str(OUT/'inference'),PY,'tools/reference/profile_fastest_range.py','--config',str(EXP/'config.json'),'--output',str(OUT/'nsys-predictions.json')],'nsys-profile')
    run([NSYS,'export','--type','sqlite','--output',str(OUT/'inference.sqlite'),str(OUT/'inference.nsys-rep')],'nsys-export')
    run([PY,'tools/reference/summarize_nsys.py',str(OUT/'inference.sqlite'),str(EXP/'nsys-summary.json')],'nsys-summary')
    metrics['nsys_ap50']=score(OUT/'nsys-predictions.json','reference','nsys-score');metrics['nsys_output_check']=validate(OUT/'nsys-predictions.json','reference')
    for i in range(1,4):
        run([PY,str(EXP/'stages.py'),'--config',str(EXP/'config.json'),'--output',str(OUT/f'stages{i}-predictions.json'),'--stats',str(EXP/f'stages{i}.json')],f'stages{i}')
        metrics[f'stages{i}_ap50']=score(OUT/f'stages{i}-predictions.json','reference',f'stages{i}-score');metrics[f'stages{i}_output_check']=validate(OUT/f'stages{i}-predictions.json','reference')
    metrics['status']='completed'
except Exception as e:
    metrics.update(status='failed',error=str(e));raise
finally:
    metrics['finished']=datetime.datetime.now().isoformat()
    metrics['sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'weights/baseline.pth',ROOT/'supership/benchmark_submission.py',ROOT/'supership/submission.py',ROOT/'data/SuperShip/reference/reference_images_meta.json',ROOT/'data/SuperShip/val/annotations/instances_val.json']}
    metrics['artifacts_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file()}
    (EXP/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
