from pathlib import Path
import json,collections,subprocess,os,sys,hashlib,datetime,statistics,platform,shutil
root=Path(__file__).resolve().parents[2];os.chdir(root)
id=Path(__file__).resolve().parent.name;exp=root/'experiments'/id;out=root/'output'/id;py='/home/ubuntu/.cache/supership-venv/bin/python'
# Preserve rejected profiler output locally; its threaded timing totals are inconsistent.
for i in range(1,4):
 if (exp/f'stages{i}.json').exists():shutil.move(exp/f'stages{i}.json',out/f'cprofile-rejected-stages{i}.json')
x=json.loads((out/'operators.json').read_text());groups=collections.defaultdict(lambda:dict(calls=0,cuda_us=0.,cpu_us=0.,shapes=[]))
for v in x['events']:
 k=(v['operator'],v['module']);g=groups[k];g['calls']+=1;g['cuda_us']+=v['cuda_us'];g['cpu_us']+=v['cpu_us']
 if v['shapes'] not in g['shapes']:g['shapes'].append(v['shapes'])
ops=[dict(operator=k[0],module=k[1],**v) for k,v in groups.items()];ops.sort(key=lambda v:v['cuda_us'],reverse=True)
(exp/'operator-summary.json').write_text(json.dumps(dict(scope=x['scope'],warning='Nested operators include child time; do not sum clone/_to_copy/copy_ times or treat eager timing as graph score',operators=ops),indent=2)+'\n')
boundaries={}
for name in ['boundary','exit-observed']:
 text=(out/f'{name}.log').read_text();rows=[json.loads(l) for l in text.splitlines() if l.startswith('{"diagnostic": "worker-boundary"')];timing=next(json.loads(l) for l in text.splitlines() if l.startswith('{"runs_seconds"'))
 checks=[]
 for i in range(1,4):
  cmd=[py,'supership/score_submission.py','--gt','data/SuperShip/reference/annotations/instances_reference.json','--submission',str(out/f'{name}.run{i}.json')]
  result=subprocess.run(cmd,capture_output=True,text=True,check=True);(out/f'{name}-score{i}.log').write_text(result.stdout+result.stderr)
  import re
  sys.path.insert(0,str(root));from supership.submission import validate_output
  checks.append(dict(ap50=float(re.search(r'AP@0.50\s+([0-9.]+)',result.stdout).group(1)),detections=validate_output(str(out/f'{name}.run{i}.json'),'data/SuperShip/reference/reference_images_meta.json')))
 for row,t in zip(rows,timing['runs_seconds']):row['official_diagnostic_seconds']=t;row['outside_runtime_seconds']=t-row['runtime_seconds']
 if name=='exit-observed':
  parent=next(json.loads(l) for l in text.splitlines() if l.startswith('{"diagnostic": "parent-observation"'))
  for row,request,exit in zip(rows,parent['requests'],parent['exits']):
   row['send_to_received_seconds']=(row['request_received_ns']-request['send_started_ns'])/1e9
   row['before_exit_to_parent_observed_seconds']=(exit['end_ns']-row['before_exit_ns'])/1e9
  timing['parent_observation']=parent
 boundaries[name]=dict(scope='Diagnostic boundary worker; core unchanged, timestamp output added; not substituted for formal scores',**timing,rows=rows,checks=checks)
(exp/'boundary-metrics.json').write_text(json.dumps(boundaries,indent=2)+'\n')
env=json.loads(subprocess.check_output([py,'-c',"import json,torch,cv2,triton,platform;print(json.dumps(dict(python=platform.python_version(),torch=torch.__version__,cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),opencv=cv2.__version__,triton=triton.__version__)))"],text=True))
env['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],text=True).strip();env['nsys']=subprocess.check_output(['/home/ubuntu/.local/opt/nsight-systems-2024.2.3/bin/nsys','--version'],text=True).strip();env['cpu']=next(l.split(':',1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name'));env['affinity']=sorted(os.sched_getaffinity(0));env['loadavg']=list(os.getloadavg());env['overrides']={k:os.environ[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES','CUDA_MODULE_LOADING','PYTORCH_CUDA_ALLOC_CONF','DEVICE','MODEL_CONFIG','MODEL_WEIGHTS'] if k in os.environ}
(exp/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
# Input corpus checksums remain independent of timings; performed only after all GPU tests.
checksums={}
for split in ['reference','val']:
 h=hashlib.sha256();count=0;size=0
 for p in sorted((root/'data/SuperShip'/split/'images').rglob('*')):
  if p.is_file():
   data=p.read_bytes();digest=hashlib.sha256(data).hexdigest();relative=str(p.relative_to(root/'data/SuperShip'/split/'images'));h.update((relative+'\0'+digest+'\n').encode());count+=1;size+=len(data)
 checksums[split]=dict(image_files=count,bytes=size,manifest_sha256=h.hexdigest(),method='SHA256 of sorted UTF-8 relative_path + NUL + per-file SHA256 hex + newline')
(exp/'dataset-checksums.json').write_text(json.dumps(checksums,indent=2)+'\n')
print('EXIT SEGMENTS',[(r['runtime_seconds'],r['before_exit_to_parent_observed_seconds'],r['send_to_received_seconds']) for r in boundaries['exit-observed']['rows']]);print('ENV',env);print('DATA',checksums)
