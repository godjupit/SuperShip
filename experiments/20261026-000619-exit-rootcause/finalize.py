"""Produce an intact independent three-round submission log and score every round."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent
out=root/'output'/exp.name/'final-three';out.mkdir(parents=True,exist_ok=False)
env=os.environ.copy();env.update(json.loads((exp/'config.json').read_text()));env['HOST_THP']='1';env.pop('GLIBC_TUNABLES',None)
python=env['PYTHON_BIN'];cmd=[python,'supership/benchmark_submission.py','--image-dir','data/SuperShip/reference/images','--meta-file','data/SuperShip/reference/reference_images_meta.json','--output-file',str(out/'predictions.json'),'--runs','3','--','bash','run.sh','--worker']
(out/'command.json').write_text(json.dumps(dict(command=cmd,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),env_overrides={**json.loads((exp/'config.json').read_text()),'HOST_THP':'1'},removed_env=['GLIBC_TUNABLES']),indent=2)+'\n')
log=out/'supership.out'
with log.open('x') as stream:r=subprocess.run(cmd,cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT)
if r.returncode:raise RuntimeError('timer failed; inspect intact log')
text=log.read_text();stats=json.loads(text.splitlines()[-1]);assert len(stats['runs_seconds'])==3 and len(re.findall(r'processed 200 images',text))==3
scores=[]
for i in range(1,4):
 pred=out/f'predictions.run{i}.json';scorecmd=[python,'supership/score_submission.py','--gt','data/SuperShip/reference/annotations/instances_reference.json','--submission',str(pred)]
 score=subprocess.run(scorecmd,cwd=root,env=env,capture_output=True,text=True);(out/f'score{i}.log').write_text(score.stdout+score.stderr)
 if score.returncode:raise RuntimeError('scoring failed')
 ap=float(re.search(r'AP@0\.50\s+([\d.]+)',score.stdout).group(1));assert ap>=.7935*.98
 scores.append(dict(round=i,reference_ap50=ap,prediction_sha256=hashlib.sha256(pred.read_bytes()).hexdigest(),score_command=scorecmd))
result=dict(**stats,rounds=scores,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),hidden_ap50=None)
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
