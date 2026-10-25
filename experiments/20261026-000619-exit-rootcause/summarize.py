"""Preserve compact evidence and checksums; raw artifacts stay outside Git."""
import hashlib,json,os,platform,re,statistics,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent;out=root/'output'/exp.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paired=json.loads((out/'paired6/results.json').read_text());final=json.loads((out/'final-three/results.json').read_text());memory={k:json.loads((out/('memory32-'+v)/'memory.json').read_text()) for k,v in [('control','control'),('candidate','candidate-v2')]}
reference=[r for r in paired['records'] if r['split']=='reference'];times={k:[r['seconds'] for r in reference if r['label']==k] for k in ['control','candidate']};med={k:statistics.median(v) for k,v in times.items()}
wins=sum(times['candidate'][i]<times['control'][i] for i in range(6))
probes={}
for d in sorted(out.iterdir()):
 if not d.is_dir() or not (d/'stdout.log').exists() or d.name.startswith('memory32-'):continue
 stdout=(d/'stdout.log').read_text();stderr=(d/'stderr.log').read_text() if (d/'stderr.log').exists() else ''
 result=dict(command=json.loads((d/'command.json').read_text()) if (d/'command.json').exists() else None)
 for line in stdout.splitlines():
  if line.startswith('{'):
   data=json.loads(line)
   if 'runs_seconds' in data:result['timing']=data
   if data.get('diagnostic')=='parent-observation':result['parent']=data
 boundaries=[json.loads(line) for line in stderr.splitlines() if line.startswith('{') and 'worker-boundary' in line]
 result['boundaries']=boundaries
 if 'parent' in result and len(boundaries)==len(result['parent']['exits']):result['exit_tail_ms']=[(e['end_ns']-b['before_exit_ns'])/1e6 for e,b in zip(result['parent']['exits'],boundaries)]
 result['status']='completed' if 'timing' in result else 'abandoned';probes[d.name]=result
metrics=dict(experiment=exp.name,formal=paired,paired_times_seconds=times,paired_medians_seconds=med,speedup_percent=100*(1-med['candidate']/med['control']),candidate_wins=wins,pairs=6,final_three=final,memory=memory,diagnostics=probes,hidden_ap50=None,submission=json.loads((out/'final-three/submission.json').read_text()))
(exp/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
import torch,cv2,triton
cpu=next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name'))
env=dict(python=sys.version,torch=torch.__version__,cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),opencv=cv2.__version__,triton=triton.__version__,kernel=platform.release(),libc=platform.libc_ver(),cpu=cpu,cpu_affinity=sorted(os.sched_getaffinity(0)),gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],text=True).strip(),thp=Path('/sys/kernel/mm/transparent_hugepage/enabled').read_text().strip())
(exp/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
assets={}
for p in [root/'weights/baseline.pth',root/'data/SuperShip/reference/reference_images_meta.json',root/'data/SuperShip/reference/annotations/instances_reference.json',root/'data/SuperShip/val/annotations/instances_val.json',root/'supership/benchmark_submission.py',root/'supership/submission.py',root/'supership/score_submission.py',root/'COMPETITION.md']:
 assets[str(p.relative_to(root))]=sha(p)
for split in ['reference','val']:
 directory=root/f'data/SuperShip/{split}/images';rows=[f'{sha(p)}  {p.name}' for p in sorted(directory.iterdir()) if p.is_file()];manifest='\n'.join(rows)+'\n';(out/f'{split}-image-sha256.txt').write_text(manifest);assets[split+'_images']=dict(count=len(rows),sorted_manifest_sha256=hashlib.sha256(manifest.encode()).hexdigest())
(exp/'data-checksums.json').write_text(json.dumps(assets,indent=2)+'\n')
(exp/'submission-receipt.txt').write_text((out/'final-three/submission-receipt.txt').read_text())
artifacts={str(p.relative_to(out)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()}
(exp/'artifacts-sha256.json').write_text(json.dumps(dict(local_only=True,primary_location='/home/ubuntu/SuperShip-main 2/output/'+exp.name,original_location=str(out),artifacts=artifacts),indent=2)+'\n')
print(json.dumps(dict(medians=med,speedup=metrics['speedup_percent'],wins=wins,final=final['median_seconds'],data=assets),indent=2))
