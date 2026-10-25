"""Serialize fresh baseline, stage and Nsight runs; retain full commands and scores."""
import json,os,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent;out=root/'output'/exp.name;out.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.update(json.loads((exp/'config.json').read_text()));python=env['PYTHON_BIN'];source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();records=[]
for name,runs in [('io',3)]:
    case=out/name;case.mkdir();e=env.copy();mode='nsys' if name.startswith('nsys') else name;e['PROFILE_MODE']=mode
    worker=['bash','run.sh','--worker'] if name=='baseline' else [python,str(exp/'worker.py')]
    if mode=='nsys':worker=['/home/ubuntu/.local/opt/nsight-systems-2024.2.3/target-linux-x64/nsys','profile','--trace=cuda,nvtx,osrt','--sample=none','--cpuctxsw=none','--cuda-graph-trace=node','--capture-range=cudaProfilerApi','--capture-range-end=stop','-o',str(case/'inference'),*worker]
    timer='supership/benchmark_submission.py' if name=='baseline' else str(exp/'observe.py')
    cmd=[python,timer,'--image-dir','data/SuperShip/reference/images','--meta-file','data/SuperShip/reference/reference_images_meta.json','--output-file',str(case/'predictions.json'),'--runs',str(runs),'--',*worker]
    (case/'command.json').write_text(json.dumps(dict(source_commit=source,command=cmd,env_overrides={**json.loads((exp/'config.json').read_text()),'PROFILE_MODE':mode}),indent=2)+'\n')
    with (case/'stdout.log').open('x') as stdout,(case/'stderr.log').open('x') as stderr:r=subprocess.run(cmd,cwd=root,env=e,stdout=stdout,stderr=stderr)
    if r.returncode:raise RuntimeError(f'{name} failed; see retained logs')
    stats=next(json.loads(l) for l in (case/'stdout.log').read_text().splitlines() if l.startswith('{') and 'runs_seconds' in l);scores=[]
    for i in range(runs):
        pred=case/(f'predictions.run{i+1}.json' if runs>1 else 'predictions.json');cmd_score=[python,'supership/score_submission.py','--gt','data/SuperShip/reference/annotations/instances_reference.json','--submission',str(pred)]
        scored=subprocess.run(cmd_score,cwd=root,env=e,capture_output=True,text=True);(case/f'score{i+1}.log').write_text(scored.stdout+scored.stderr)
        if scored.returncode:raise RuntimeError(f'{name} scoring failed')
        ap=float(re.search(r'AP@0\.50\s+([\d.]+)',scored.stdout).group(1));assert ap>=.7935*.98;scores.append(ap)
    if mode=='nsys':
        export=['/home/ubuntu/.local/opt/nsight-systems-2024.2.3/target-linux-x64/nsys','export','--type','sqlite','--output',str(case/'inference.sqlite'),str(case/'inference.nsys-rep')]
        subprocess.run(export,cwd=root,check=True,capture_output=True)
        summarize=[python,'tools/reference/summarize_nsys.py',str(case/'inference.sqlite'),str(case/'summary.json')];subprocess.run(summarize,cwd=root,check=True)
        (case/'extra-commands.json').write_text(json.dumps(dict(export=export,summarize=summarize),indent=2)+'\n')
    record=dict(name=name,timings=stats,reference_ap50=scores);records.append(record);(exp/'io-runs.json').write_text(json.dumps(dict(source_commit=source,runs=records),indent=2)+'\n');print(json.dumps(record),flush=True)
