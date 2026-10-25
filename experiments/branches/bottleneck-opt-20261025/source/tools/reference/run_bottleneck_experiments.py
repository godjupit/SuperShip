"""Independent opt-in hypotheses with original official timing and precision checks."""
import argparse,datetime,hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PY='/home/ubuntu/.cache/supership-venv/bin/python'
PARENT='20261025-180401-bottleneck-sweep'
CASES={'combined-c1':{'CUDA_DEVICE_MAX_CONNECTIONS':'1','EARLY_INPUT_RECYCLE':'1','BULK_RESULTS':'1','DEFORM_ATTN_IMPL':'triton'},'connections1':{'CUDA_DEVICE_MAX_CONNECTIONS':'1'},'async-alloc':{'PYTORCH_CUDA_ALLOC_CONF':'backend:cudaMallocAsync'},'cached':{'DEFORM_VALUE_CACHE':'1'},'cached-cpu':{'DEFORM_VALUE_CACHE':'1','EARLY_INPUT_RECYCLE':'1','BULK_RESULTS':'1'},'control':{},'recycle':{'EARLY_INPUT_RECYCLE':'1'},'bulk':{'BULK_RESULTS':'1'},
       'fused':{'DEFORM_ATTN_IMPL':'triton'},'cpu':{'EARLY_INPUT_RECYCLE':'1','BULK_RESULTS':'1'},
       'fused-bulk':{'BULK_RESULTS':'1','DEFORM_ATTN_IMPL':'triton'},
       'combined':{'EARLY_INPUT_RECYCLE':'1','BULK_RESULTS':'1','DEFORM_ATTN_IMPL':'triton'}}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def commit(paths,message):
 subprocess.run(['git','add',*map(str,paths)],cwd=ROOT,check=True)
 subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
 subprocess.run(['git','commit','-m',message],cwd=ROOT,check=True)
def execute(cmd,env,path):
 if path.exists():raise FileExistsError(path)
 with path.open('w') as f:result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 if result.returncode:raise RuntimeError(f'exit {result.returncode}: {path}')
 return path.read_text()
def main():
 p=argparse.ArgumentParser();p.add_argument('cases',nargs='+',choices=CASES);a=p.parse_args();os.chdir(ROOT)
 for case in a.cases:
  identifier=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-bottleneck-'+case
  exp=ROOT/'experiments'/identifier;out=ROOT/'output'/identifier;exp.mkdir();out.mkdir(parents=True)
  config=json.loads((ROOT/'experiments'/PARENT/'config.json').read_text())|CASES[case]
  config['CUDA_DEVICE_MAX_CONNECTIONS']=CASES[case].get('CUDA_DEVICE_MAX_CONNECTIONS','8')
  config['PYTORCH_CUDA_ALLOC_CONF']=CASES[case].get('PYTORCH_CUDA_ALLOC_CONF','backend:native')
  config['DEFORM_VALUE_CACHE']=CASES[case].get('DEFORM_VALUE_CACHE','0')
  config['TRITON_CACHE_DIR']=str(ROOT/'output'/PARENT/'triton-cache')
  (exp/'config.json').write_text(json.dumps(config,indent=2)+'\n');env=os.environ|config
  commands={}
  for split,runs in [('reference',3),('val',1)]:
   meta='data/SuperShip/reference/reference_images_meta.json' if split=='reference' else 'data/SuperShip/val/annotations/instances_val.json'
   commands[split]=[PY,'supership/benchmark_submission.py','--image-dir',f'data/SuperShip/{split}/images','--meta-file',meta,'--output-file',str(out/(split+'.json')),'--runs',str(runs),'--','env','PYTHON_BIN='+PY,'bash','run.sh','--worker']
  (exp/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  (exp/'notes.md').write_text(f'# Bottleneck hypothesis: {case}\n\nStatus planned; parent {PARENT}; single RTX4090 GPU0 exclusive; source/config versioned before execution. Original official READY timing includes all outputs/fsync and process-group exit. No competition submission by this script.\n')
  ledger=ROOT/'OPTIMIZATION_EXPERIMENTS.md'
  with ledger.open('a') as f:f.write(f'\n## 2026-10-25｜{identifier}｜running\n\nCodex /root；exp/bottleneck-opt-20261025；GPU0 RTX4090独占。父{PARENT}；[{case}](experiments/{identifier}/notes.md)。\n')
  commit([exp,ledger],f'Register bottleneck experiment {case} before timing')
  source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
  metric=dict(case=case,experiment=identifier,status='running',source_commit=source,parent_experiment=PARENT,started=datetime.datetime.now().isoformat(),gpu='RTX4090 single GPU0',timing_scope='Original READY to process-group exit, including inputs and fsync',hidden_ap50=None,competition_submitted=False,artifact_directory=str(out),reference_images=200,validation_images=1030)
  print('START',identifier,flush=True)
  def score(pred,split,label):
   gt=f'data/SuperShip/{split}/annotations/instances_{split}.json'
   text=execute([PY,'supership/score_submission.py','--gt',gt,'--submission',str(pred)],env,out/(label+'.log'))
   return float(re.search(r'AP@0.50\s+([0-9.]+)',text).group(1))
  try:
   text=execute(commands['reference'],env,out/'reference-benchmark.log')
   metric.update(json.loads(next(l for l in reversed(text.splitlines()) if l.startswith('{"runs_seconds"'))))
   metric['reference_ap50']=[score(out/f'reference.run{i}.json','reference',f'reference-score{i}') for i in range(1,4)]
   metric['reference_precision_pass']=min(metric['reference_ap50'])>=.7935*.98
   sys.path.insert(0,str(ROOT));from supership.submission import validate_output
   metric['reference_detection_counts']=[validate_output(str(out/f'reference.run{i}.json'),'data/SuperShip/reference/reference_images_meta.json') for i in range(1,4)]
   if metric['reference_precision_pass']:
    text=execute(commands['val'],env,out/'validation-benchmark.log');metric['validation_timing']=json.loads(next(l for l in reversed(text.splitlines()) if l.startswith('{"runs_seconds"')))
    metric['validation_ap50']=score(out/'val.json','val','validation-score')
    metric['validation_detection_count']=validate_output(str(out/'val.json'),'data/SuperShip/val/annotations/instances_val.json')
   metric['validation_precision_pass']=metric.get('validation_ap50',0)>=.917*.98
   metric['status']='completed' if metric['validation_precision_pass'] else 'completed'
   metric['precision_qualified']=metric['reference_precision_pass'] and metric['validation_precision_pass']
  except Exception as error:
   metric.update(status='completed',error=str(error),precision_qualified=False)
   print('FAILED',identifier,str(error),flush=True)
  metric['finished']=datetime.datetime.now().isoformat()
  metric['sha256']={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'weights/baseline.pth',ROOT/'supership/benchmark_submission.py',ROOT/'supership/submission.py',ROOT/'data/SuperShip/reference/reference_images_meta.json',ROOT/'data/SuperShip/val/annotations/instances_val.json']}
  metric['artifacts_sha256']={str(p.relative_to(ROOT)):sha(p) for p in out.iterdir() if p.is_file()}
  (exp/'metrics.json').write_text(json.dumps(metric,indent=2)+'\n')
  with (exp/'notes.md').open('a') as f:f.write(f'\nCompleted; runtime source `{source}`; config and commands unchanged during execution, generated evidence only untracked. Precision qualified={metric["precision_qualified"]}. All per-run timings/AP50, full validation/tail coverage, failures and checksums in metrics.json; large artifacts local only. Hidden unmeasured.\n')
  s=ledger.read_text().replace(identifier+'｜running',identifier+'｜completed');s+=f'\n{case}: three runs={metric.get("runs_seconds")}, median={metric.get("median_seconds")}, reference AP50={metric.get("reference_ap50")}, validation AP50={metric.get("validation_ap50")}, qualified={metric["precision_qualified"]}, error={metric.get("error")}.\n';ledger.write_text(s)
  commit([exp,ledger],f'Record all bottleneck {case} timings and precision results')
  print('RESULT',json.dumps({k:v for k,v in metric.items() if k in ('case','experiment','runs_seconds','median_seconds','reference_ap50','validation_ap50','precision_qualified','error')}),flush=True)
if __name__=='__main__':main()
