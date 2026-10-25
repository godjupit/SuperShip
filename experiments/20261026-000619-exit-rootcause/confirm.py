"""Serial AB/BA full-protocol comparison; official timer/scorer remain unchanged."""
import argparse,hashlib,json,os,re,statistics,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--pairs',type=int,default=6);p.add_argument('--validation',action='store_true');a=p.parse_args()
out=root/'output'/exp.name/a.name;out.mkdir(parents=True,exist_ok=False)
env=os.environ.copy();env.update(json.loads((exp/'config.json').read_text()));env.pop('GLIBC_TUNABLES',None)
python=env['PYTHON_BIN'];source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
records=[]
def run(label,index,split):
    case=out/f'{index:02}-{label}-{split}';case.mkdir();pred=case/'predictions.json';e=env.copy();e['HOST_THP']='1' if label=='candidate' else '0'
    meta='data/SuperShip/reference/reference_images_meta.json' if split=='reference' else 'data/SuperShip/val/annotations/instances_val.json'
    gt='data/SuperShip/reference/annotations/instances_reference.json' if split=='reference' else meta
    cmd=[python,'supership/benchmark_submission.py','--image-dir',f'data/SuperShip/{split if split=="reference" else "val"}/images','--meta-file',meta,'--output-file',str(pred),'--runs','1','--','bash','run.sh','--worker']
    score=[python,'supership/score_submission.py','--gt',gt,'--submission',str(pred)]
    (case/'command.json').write_text(json.dumps(dict(source_commit=source,command=cmd,score=score,env_overrides={**json.loads((exp/'config.json').read_text()),'HOST_THP':e['HOST_THP']},removed_env=['GLIBC_TUNABLES']),indent=2)+'\n')
    r=subprocess.run(cmd,cwd=root,env=e,capture_output=True,text=True)
    (case/'stdout.log').write_text(r.stdout);(case/'stderr.log').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    stats=json.loads(r.stdout.splitlines()[-1]);assert re.search(r'processed '+('200' if split=='reference' else '1030')+r' images',r.stderr),r.stderr
    scored=subprocess.run(score,cwd=root,env=e,capture_output=True,text=True);(case/'score.log').write_text(scored.stdout+scored.stderr)
    if scored.returncode:raise RuntimeError(scored.stderr)
    ap=float(re.search(r'AP@0\.50\s+([\d.]+)',scored.stdout).group(1))
    record=dict(label=label,index=index,split=split,seconds=stats['runs_seconds'][0],ap50=ap,prediction_sha256=hashlib.sha256(pred.read_bytes()).hexdigest(),case=str(case.relative_to(root)))
    records.append(record);(out/'results.json').write_text(json.dumps(dict(source_commit=source,records=records),indent=2)+'\n');print(json.dumps(record),flush=True)
for pair in range(a.pairs):
    for label in (['control','candidate'] if pair%2==0 else ['candidate','control']):run(label,pair,'reference')
if a.validation:
    for label in ['control','candidate']:run(label,0,'validation')
for label in ['control','candidate']:
    values=[r['seconds'] for r in records if r['label']==label and r['split']=='reference'];print(label,values,'median',statistics.median(values),flush=True)
