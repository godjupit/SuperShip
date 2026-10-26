"""Alternate two complete workers; one-run logs are diagnostics, never uploaded."""
import argparse,itertools,json,statistics,subprocess,sys
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('baseline');p.add_argument('candidate');p.add_argument('--pairs',type=int,default=8);a=p.parse_args()
root=Path.cwd();exp=root/'experiments/20261026-075543-continued-sweep';out=root/'output'/exp.name;records=[]
for index in range(a.pairs):
 order=[a.baseline,a.candidate] if index%2==0 else [a.candidate,a.baseline]
 pair=dict(pair=index+1,order=order)
 for variant in order:
  gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip();assert not gpu,'GPU occupied'
  name=datetime.now().strftime('pair-%Y%m%d-%H%M%S-')+str(index+1)+'-'+variant
  command=[sys.executable,str(exp/'run_case.py'),variant,'--runs','1','--combined-log','--name',name]
  subprocess.run(command,cwd=root,check=True,stdout=subprocess.DEVNULL)
  m=json.loads((out/name/'metrics.json').read_text());assert m['precision_pass']
  pair[variant]=dict(case=name,seconds=m['median_seconds'],ap50=m['scores'][0]['ap50'],sha256=m['scores'][0]['sha256'],command=command)
 records.append(pair);(out/'paired.json').write_text(json.dumps(dict(baseline=a.baseline,candidate=a.candidate,pairs=records),indent=2)+'\n');print(json.dumps(pair),flush=True)
b=[r[a.baseline]['seconds'] for r in records];c=[r[a.candidate]['seconds'] for r in records];d=[x-y for x,y in zip(b,c)]
# Exact two-sided sign-flip randomization test; descriptive, no cherry-picked pairs.
observed=abs(statistics.mean(d));count=sum(abs(statistics.mean([v*s for v,s in zip(d,signs)]))>=observed-1e-12 for signs in itertools.product([-1,1],repeat=len(d)))
summary=dict(baseline=a.baseline,candidate=a.candidate,pairs=records,baseline_median_seconds=statistics.median(b),candidate_median_seconds=statistics.median(c),median_paired_difference_seconds=statistics.median(d),wins=sum(x>0 for x in d),pair_count=len(d),two_sided_sign_flip_p=count/(2**len(d)),all_outputs_byte_identical=all(r[a.baseline]['sha256']==r[a.candidate]['sha256'] for r in records),scope='alternating complete one-run workers; no submissions; does not replace intact three-round Accepted log')
(out/'paired.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='pairs'}),flush=True)
