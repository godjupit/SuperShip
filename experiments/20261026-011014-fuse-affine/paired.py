"""Balanced ten-pair confirmation with complete timers and all reference scores."""
import json,statistics,subprocess,sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent;out=root/'output'/exp.name
records=[]
for pair in range(10):
 for name in (['control','half-output'] if pair%2==0 else ['half-output','control']):
  case=f'paired10-{pair:02}-{name}'
  subprocess.run([sys.executable,str(exp/'run_case.py'),name,'--name',case,'--runs','1'],cwd=root,check=True)
  metrics=json.loads((out/case/'metrics.json').read_text());assert metrics['precision_pass'];records.append(dict(pair=pair,variant=name,seconds=metrics['runs_seconds'][0],ap50=metrics['scores'][0]['ap50'],case=case,source_commit=metrics['source_commit']))
  (out/'paired10-results.json').write_text(json.dumps(records,indent=2)+'\n')
a=[next(r['seconds'] for r in records if r['pair']==i and r['variant']=='control') for i in range(10)];b=[next(r['seconds'] for r in records if r['pair']==i and r['variant']=='half-output') for i in range(10)];delta=np.array(a)-np.array(b);samples=np.median(np.random.default_rng(20261026).choice(delta,size=(10000,10)),axis=1)
result=dict(control_seconds=a,candidate_seconds=b,control_median=statistics.median(a),candidate_median=statistics.median(b),reduction_percent=100*(1-statistics.median(b)/statistics.median(a)),candidate_wins=int((delta>0).sum()),paired_delta_median=float(np.median(delta)),paired_delta_bootstrap95=np.quantile(samples,[.025,.975]).tolist(),scope='same GPU/data/protocol, ten AB/BA pairs; not hidden-set evidence')
(out/'paired10-summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
