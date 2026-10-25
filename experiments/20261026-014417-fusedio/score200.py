"""Produce intact three-round logs; submit only improvements to the current best."""
import hashlib,json,os,re,subprocess,sys
from datetime import datetime
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent;out=root/'output'/exp.name
best=.275737156;records=[]
if (out/'fast-score-results.json').exists():
 previous=json.loads((out/'fast-score-results.json').read_text());best=min(best,previous['best_seconds']);records=previous['cases']
credentials=Path('/home/ubuntu/SuperShip-main 2/.local/.thuscc_credentials');script=Path('/home/ubuntu/SuperShip-main 2/.local/submit.sh')
values={}
for line in credentials.read_text().splitlines():
 if '=' in line:
  k,v=line.split('=',1);values[k.strip()]=v.strip()
assert values.get('username')=='ruc2602' and credentials.stat().st_mode&0o777==0o600
assert hashlib.sha256(script.read_bytes()).hexdigest()=='b6dc5a8cf976fab3e9e0cc9c290521e63ab353fcc263612875e4dc56b9419cdd'
for index,variant in enumerate(json.loads((exp/'plan.json').read_text())):
 name='fast-score-'+datetime.now().strftime('%H%M%S')+'-'+str(index)
 r=subprocess.run([sys.executable,str(exp/'run_case.py'),variant,'--name',name,'--runs','3','--combined-log','--split','reference'],cwd=root)
 if r.returncode:
  result=dict(case=name,variant=variant,status='runtime_failed',submitted=False);records.append(result);(out/'fast-score-results.json').write_text(json.dumps(dict(best_seconds=best,cases=records),indent=2)+'\n');print(json.dumps(result),flush=True);continue
 case=out/name;m=json.loads((case/'metrics.json').read_text());assert len(m['runs_seconds'])==3
 result=dict(case=name,variant=variant,median_seconds=m['median_seconds'],runs_seconds=m['runs_seconds'],log_sha256=m['log_sha256'],submitted=False,precision_pass=m['precision_pass'])
 if m['precision_pass'] and m['median_seconds']<best:
  log=case/'supership.out';assert hashlib.sha256(log.read_bytes()).hexdigest()==m['log_sha256']
  env=os.environ.copy();env['THUSCC_CREDENTIALS_FILE']=str(credentials);cmd=['bash',str(script),'SUPERSHIP',str(log)]
  r=subprocess.run(cmd,cwd='/home/ubuntu/SuperShip-main 2',env=env,capture_output=True,text=True,timeout=90);receipt=r.stdout+r.stderr
  for k,v in values.items():
   if v and k.lower() in ['password','passwd','token','secret']:receipt=receipt.replace(v,'<redacted>')
  receipt=re.sub(r'\x1b\[[0-9;]*m','',receipt);(case/'submission-receipt.txt').write_text(receipt)
  result.update(command=cmd,account='ruc2602',return_code=r.returncode,receipt=receipt,submitted=r.returncode==0 and 'Submission Accepted' in receipt)
  (case/'submission.json').write_text(json.dumps(result,indent=2)+'\n')
  print(receipt,flush=True)
  if result['submitted']:best=m['median_seconds']
  else:raise RuntimeError('submission rejected; retained full result')
 records.append(result);(out/'fast-score-results.json').write_text(json.dumps(dict(best_seconds=best,cases=records,scope='intact complete three-round logs; no concatenated rounds; timing parsed only; hidden unmeasured'),indent=2)+'\n')
 print(json.dumps(dict(case=name,median_seconds=m['median_seconds'],submitted=result['submitted'],best_seconds=best)),flush=True)
