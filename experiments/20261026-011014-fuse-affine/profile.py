"""Profile graph kernels on complete real input, after the READY protocol."""
import json,os,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent;nsys='/home/ubuntu/.local/opt/nsight-systems-2024.2.3/target-linux-x64/nsys'
for name in sys.argv[1:]:
 case=root/'output'/exp.name/('profile-'+name);case.mkdir(parents=True,exist_ok=False);config=json.loads((exp/'variants'/f'{name}.json').read_text());env=os.environ.copy();env.update(config);env['PROFILE_MODE']='nsys';python=config['PYTHON_BIN']
 worker=[nsys,'profile','--trace=cuda,nvtx,osrt','--sample=none','--cpuctxsw=none','--cuda-graph-trace=node','--capture-range=cudaProfilerApi','--capture-range-end=stop','-o',str(case/'inference'),python,'experiments/20261026-002932-profile-thp/worker.py']
 cmd=[python,'supership/benchmark_submission.py','--image-dir','data/SuperShip/reference/images','--meta-file','data/SuperShip/reference/reference_images_meta.json','--output-file',str(case/'predictions.json'),'--runs','1','--',*worker]
 export=[nsys,'export','--type','sqlite','--output',str(case/'inference.sqlite'),str(case/'inference.nsys-rep')];summary=[python,'tools/reference/summarize_nsys.py',str(case/'inference.sqlite'),str(case/'summary.json')];score=[python,'supership/score_submission.py','--gt','data/SuperShip/reference/annotations/instances_reference.json','--submission',str(case/'predictions.json')]
 (case/'command.json').write_text(json.dumps(dict(command=cmd,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),config=config,export=export,summary=summary,score=score),indent=2)+'\n')
 for label,command in [('profile',cmd),('export',export),('summary',summary),('score',score)]:
  with (case/f'{label}.log').open('x') as stream:r=subprocess.run(command,cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT)
  if r.returncode:raise RuntimeError(f'{name} {label} failed')
 ap=float(re.search(r'AP@0\.50\s+([\d.]+)',(case/'score.log').read_text()).group(1));assert ap>=.7935*.98
 d=json.loads((case/'summary.json').read_text());print(json.dumps(dict(name=name,kernel_sum_ms=d['kernel_sum_ms'],kernel_count=d['kernel_count'],gpu_activity_union_ms=d['gpu_activity_union_ms'],ap50=ap)),flush=True)
