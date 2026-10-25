"""One fresh full wrapper benchmark, validation and real-input profile; never submit scores."""
import argparse,datetime,hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PY='/home/ubuntu/.cache/supership-venv/bin/python';NSYS='/home/ubuntu/.local/opt/nsight-systems-2024.2.3/bin/nsys'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from run_bottleneck_experiments import execute,commit,sha

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args();os.chdir(ROOT)
 id=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-bottleneck-final'
 exp=ROOT/'experiments'/id;out=ROOT/'output'/id;exp.mkdir();out.mkdir(parents=True)
 config=json.loads(a.config.read_text());config['TRITON_CACHE_DIR']=str(ROOT/'output/20261025-180401-bottleneck-sweep/triton-cache')
 (exp/'config.json').write_text(json.dumps(config,indent=2)+'\n')
 env=os.environ.copy()
 for key in config:env.pop(key,None)
 env.update(PYTHON_BIN=PY,OUTPUT_FILE=str(out/'reference.json'),RUNS='3',TRITON_CACHE_DIR=config['TRITON_CACHE_DIR'])
 commands=dict(wrapper=['bash','benchmark_bottleneck.sh'],validation=[PY,'supership/benchmark_submission.py','--image-dir','data/SuperShip/val/images','--meta-file','data/SuperShip/val/annotations/instances_val.json','--output-file',str(out/'validation.json'),'--runs','1','--','env','PYTHON_BIN='+PY,'bash','run.sh','--worker'],profile=[NSYS,'profile','--trace=cuda,nvtx,osrt','--sample=none','--cpuctxsw=none','--cuda-graph-trace=node','--capture-range=cudaProfilerApi','--capture-range-end=stop','-o',str(out/'inference'),PY,'tools/reference/profile_fastest_range.py','--config',str(exp/'config.json'),'--output',str(out/'nsys-predictions.json')],export=[NSYS,'export','--type','sqlite','--output',str(out/'inference.sqlite'),str(out/'inference.nsys-rep')],summary=[PY,'tools/reference/summarize_nsys.py',str(out/'inference.sqlite'),str(exp/'nsys-summary.json')])
 (exp/'commands.json').write_text(json.dumps(dict(commands=commands,wrapper_environment={k:env[k] for k in ['PYTHON_BIN','OUTPUT_FILE','RUNS','TRITON_CACHE_DIR']}),indent=2)+'\n')
 (exp/'notes.md').write_text('# Paired-confirmed candidate final wrapper check\n\nStatus running; one fresh full three-run reference log via new wrapper defaults, complete validation with tail, real-input Nsight excludes init. Per-run scores and output checks required. Original timer unchanged. No competition submission by this script. Candidate parents: 20261025-181507-bottleneck-combined-c1, 20261025-181604-bottleneck-paired10.\n')
 ledger=ROOT/'OPTIMIZATION_EXPERIMENTS.md'
 with ledger.open('a') as f:f.write(f'\n## 2026-10-25｜{id}｜running\n\nCodex /root；GPU0 RTX4090独占；新wrapper完整三轮/验证/真实输入profile，[记录](experiments/{id}/notes.md)。不提交竞赛。\n')
 commit([exp,ledger],'Register final bottleneck wrapper validation and profile')
 metric=dict(status='running',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),started=datetime.datetime.now().isoformat(),artifact_directory=str(out),competition_submitted=False,hidden_ap50=None)
 from supership.submission import validate_output
 def score(pred,split,label):
  gt=f'data/SuperShip/{split}/annotations/instances_{split}.json';text=execute([PY,'supership/score_submission.py','--gt',gt,'--submission',str(pred)],os.environ.copy(),out/(label+'.log'))
  meta='data/SuperShip/reference/reference_images_meta.json' if split=='reference' else 'data/SuperShip/val/annotations/instances_val.json'
  return dict(ap50=float(re.search(r'AP@0.50\s+([0-9.]+)',text).group(1)),detections=validate_output(str(pred),meta))
 try:
  print('START',id,flush=True)
  text=execute(commands['wrapper'],env,out/'supership.out');metric.update(json.loads(next(l for l in reversed(text.splitlines()) if l.startswith('{"runs_seconds"'))))
  metric['reference']=[score(out/f'reference.run{i}.json','reference',f'reference-score{i}') for i in range(1,4)]
  fullenv=os.environ|config;text=execute(commands['validation'],fullenv,out/'validation.log');metric['validation_timing']=json.loads(next(l for l in reversed(text.splitlines()) if l.startswith('{"runs_seconds"')));metric['validation']=score(out/'validation.json','val','validation-score')
  metric['precision_qualified']=min(r['ap50'] for r in metric['reference'])>=.7935*.98 and metric['validation']['ap50']>=.917*.98
  for key in ['profile','export','summary']:execute(commands[key],fullenv,out/(key+'.log'))
  metric['profile']=score(out/'nsys-predictions.json','reference','nsys-score');metric['status']='completed'
 except Exception as error:
  metric.update(status='completed',error=str(error));print('ERROR',str(error),flush=True)
 metric['finished']=datetime.datetime.now().isoformat();metric['sha256']={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'weights/baseline.pth',ROOT/'supership/benchmark_submission.py',ROOT/'supership/submission.py',ROOT/'data/SuperShip/reference/reference_images_meta.json',ROOT/'data/SuperShip/val/annotations/instances_val.json']};metric['artifacts_sha256']={str(p.relative_to(ROOT)):sha(p) for p in out.iterdir() if p.is_file()}
 (exp/'metrics.json').write_text(json.dumps(metric,indent=2)+'\n')
 with (exp/'notes.md').open('a') as f:f.write(f'\nCompleted; all raw timings, precision, failures, commands, pinned source `{metric["source_commit"]}` and checksums are adjacent. Generated evidence only untracked during execution. Large artifacts local only.\n')
 s=ledger.read_text().replace(id+'｜running',id+'｜completed');s+=f'\nFinal wrapper median={metric.get("median_seconds")}, runs={metric.get("runs_seconds")}, validation={metric.get("validation")}, qualified={metric.get("precision_qualified")}, error={metric.get("error")}.\n';ledger.write_text(s)
 commit([exp,ledger],'Record final wrapper score and updated real-input GPU profile')
 print('FINAL',json.dumps({k:v for k,v in metric.items() if k not in ['artifacts_sha256','sha256']}),flush=True)
if __name__=='__main__':main()
