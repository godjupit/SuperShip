"""Reproduce the named follow-up sweeps with immutable logs and per-run records.

Usage: PYTHON_BIN=... SUBMIT_RESULTS=1 python tools/reference/run_further_experiments.py cvtcolor async
Without SUBMIT_RESULTS=1, only benchmark and score locally.
Formal submission follows this repository's authorized workflow; local credentials are never logged.
"""
import datetime, hashlib, json, os, pathlib, re, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
os.chdir(ROOT)
PY=os.environ.get('PYTHON_BIN', sys.executable)
STAMP=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
BASE=dict(INPUT_SIZE='640',PIPELINE='fast',PRECISION='fp16',BACKEND='cuda_graph',BATCH_SIZE='8',NUM_WORKERS='8',PIPELINE_DEPTH='3',SCORE_THRESHOLD='0.05',IMAGE_DECODER='opencv',VECTORIZED_RESULTS='1',CHANNELS_LAST='1',MODEL_DEPLOY='0',FAST_EXIT='1',TORCH_THREADS='1',JPEG_REDUCTION='2',RESIZE_ANTIALIAS='1',OPENCV_COPY_MODE='strided',ASYNC_OUTPUT='0',DECODER_LAYERS='0',CUDNN_BENCHMARK='0',PYTHON_BIN=PY)
CASES=[('control',{}),('cvtcolor',dict(OPENCV_COPY_MODE='cvtcolor')),('direct',dict(OPENCV_COPY_MODE='direct')),('async',dict(ASYNC_OUTPUT='1')),('async-cvtcolor',dict(ASYNC_OUTPUT='1',OPENCV_COPY_MODE='cvtcolor')),('async-cvtcolor-b16',dict(ASYNC_OUTPUT='1',OPENCV_COPY_MODE='cvtcolor',BATCH_SIZE='16')),('async-cvtcolor-w4',dict(ASYNC_OUTPUT='1',OPENCV_COPY_MODE='cvtcolor',NUM_WORKERS='4')),('async-cvtcolor-cudnn',dict(ASYNC_OUTPUT='1',OPENCV_COPY_MODE='cvtcolor',CUDNN_BENCHMARK='1')),('decoder2',dict(ASYNC_OUTPUT='1',OPENCV_COPY_MODE='cvtcolor',DECODER_LAYERS='2')),('decoder1',dict(ASYNC_OUTPUT='1',OPENCV_COPY_MODE='cvtcolor',DECODER_LAYERS='1'))]
CASES += [
 ('decoder2-score004', dict(DECODER_LAYERS='2', SCORE_THRESHOLD='0.04', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
 ('decoder1-score004', dict(DECODER_LAYERS='1', SCORE_THRESHOLD='0.04', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
 ('decoder1-score003', dict(DECODER_LAYERS='1', SCORE_THRESHOLD='0.03', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
 ('size576-half', dict(INPUT_SIZE='576', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
 ('size576-full', dict(INPUT_SIZE='576', JPEG_REDUCTION='1', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
 ('size512-full', dict(INPUT_SIZE='512', JPEG_REDUCTION='1', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
]
CASES += [
 ('size512-half', dict(INPUT_SIZE='512', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
 ('size544-half', dict(INPUT_SIZE='544', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
 ('size576-decoder2', dict(INPUT_SIZE='576', DECODER_LAYERS='2', SCORE_THRESHOLD='0.04', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
 ('size576-decoder1', dict(INPUT_SIZE='576', DECODER_LAYERS='1', SCORE_THRESHOLD='0.04', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
]
CASES += [
 ('confirm-control', {}),
 ('confirm-size544', dict(INPUT_SIZE='544', ASYNC_OUTPUT='1', OPENCV_COPY_MODE='cvtcolor', CUDNN_BENCHMARK='1')),
]
if len(sys.argv)>1:
    unknown = set(sys.argv[1:]) - {case[0] for case in CASES}
    if unknown:
        raise SystemExit(f'Unknown cases: {sorted(unknown)}')
    CASES=[case for case in CASES if case[0] in sys.argv[1:]]
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
patch=subprocess.check_output(['git','diff','--binary','--','supership'])
weight_sha=hashlib.sha256((ROOT/'weights/baseline.pth').read_bytes()).hexdigest()
meta_sha=hashlib.sha256((ROOT/'data/SuperShip/reference/reference_images_meta.json').read_bytes()).hexdigest()
manifest=ROOT/'output'/f'further-{STAMP}.json'
manifest.parent.mkdir(exist_ok=True)
results=[]
restore=ROOT/'output/submissions/20261022-official-fast-opencv-half-score005/supership.out'
best_time=0.476629654
best_log=restore
for prior in (ROOT/'experiments').glob('*further-*/metrics.json'):
    data=json.loads(prior.read_text())
    if data.get('submitted') and data.get('validation_precision_pass', True) and data.get('median_seconds', 1e9)<best_time:
        best_time=data['median_seconds']
        best_log=pathlib.Path(data['artifact_directory'])/'supership.out'

def execute(cmd, env, log, timeout=240):
    with log.open('w') as output:
        result=subprocess.run(cmd,env=env,stdout=output,stderr=subprocess.STDOUT,text=True,timeout=timeout)
    if result.returncode: raise RuntimeError(f'command failed ({result.returncode}): {log}')
    return log.read_text()

def submit(log, artifact):
    env=dict(os.environ,THUSCC_CREDENTIALS_FILE=os.environ.get('THUSCC_CREDENTIALS_FILE', str(ROOT/'.local/.thuscc_credentials')))
    text=execute(['bash',os.environ.get('THUSCC_SUBMIT_SCRIPT', str(ROOT/'.local/submit.sh')),'SUPERSHIP',str(log)],env,artifact,120)
    if 'Submission Accepted' not in text: raise RuntimeError(f'submission rejected; see {artifact}')
    return text

for name, extra in CASES:
    identifier=f'{STAMP}-further-{name}'
    exp=ROOT/'experiments'/identifier;exp.mkdir()
    out=ROOT/'output/submissions'/identifier;out.mkdir(parents=True)
    env=BASE|extra
    process_env=os.environ|env
    (exp/'config.json').write_text(json.dumps(env,indent=2)+'\n')
    if patch: (exp/'source.patch').write_bytes(patch)
    metric=dict(name=name,status='running',source_commit=commit,source_dirty=bool(patch),weight_sha256=weight_sha,metadata_sha256=meta_sha,hardware='NVIDIA RTX 4090, single GPU',torch='2.6.0+cu124',opencv='4.11.0',python=subprocess.check_output([PY,'--version'],text=True).strip(),started=datetime.datetime.now().isoformat(),timing_scope='official worker protocol, READY to process group exit, includes fsync; initialization excluded',artifact_directory=str(out),validation_ap50=None,hidden_ap50=None)
    cmd=[PY,'supership/benchmark_submission.py','--image-dir','data/SuperShip/reference/images','--meta-file','data/SuperShip/reference/reference_images_meta.json','--output-file',str(out/'reference_submission.json'),'--runs','3','--','bash','run.sh','--worker']
    metric['command']=cmd
    print('START',identifier,flush=True)
    try:
        text=execute(cmd,process_env,out/'supership.out')
        timing=json.loads([line for line in text.splitlines() if line.startswith('{')][-1])
        metric.update(timing)
        metric['raw_log_sha256']=hashlib.sha256((out/'supership.out').read_bytes()).hexdigest()
        aps=[];sha=[]
        for i in range(1,4):
            prediction=out/f'reference_submission.run{i}.json'
            text=execute(['bash','score_reference.sh',str(prediction)],process_env,out/f'score{i}.log')
            aps.append(float(re.search(r'AP@0.50\s+([0-9.]+)',text).group(1)))
            sha.append(hashlib.sha256(prediction.read_bytes()).hexdigest())
        metric['reference_ap50_per_run']=aps
        metric['prediction_sha256_per_run']=sha
        metric['reference_precision_pass']=min(aps)>=0.7935*0.98
        metric['submitted']=False
        if metric['reference_precision_pass'] and os.environ.get('SUBMIT_RESULTS', '0') == '1':
            metric['submission_response']=submit(out/'supership.out',out/'submission-response.txt')
            metric['submitted']=True
            (exp/'submission-response.txt').write_text(metric['submission_response'])
            if metric['median_seconds']<best_time:
                best_time=metric['median_seconds'];best_log=out/'supership.out'
            else:
                metric['best_restored_response']=submit(best_log,out/'restore-best-response.txt')
        else: metric['submitted']=False
        metric['status']='success'
        print('RESULT',name,metric['median_seconds'],aps,'submitted',metric.get('submitted'),flush=True)
    except Exception as error:
        metric['status']='failed';metric['error']=str(error)
        print('FAILED',name,str(error),flush=True)
    metric['finished']=datetime.datetime.now().isoformat()
    (exp/'metrics.json').write_text(json.dumps(metric,indent=2,ensure_ascii=False)+'\n')
    notes=f'# Further optimization: {name}\n\nSource: `{commit}`, dirty={bool(patch)} (saved source.patch when dirty).\n\nFull effective parameters: config.json. Full command, runtime/precision results, dataset metadata and weight SHA256, and raw artifacts: metrics.json.\n\nMeasured on one RTX 4090 with the unchanged official timer and validator pinned in the repository. No test images or metadata are accessed before READY.\n\nStatus: {metric["status"]}. Validation AP50 and hidden AP50 are unmeasured unless explicitly populated.\n'
    (exp/'notes.md').write_text(notes)
    with (ROOT/'OPTIMIZATION_EXPERIMENTS.md').open('a') as f:
        f.write(f'\n- {STAMP} [{name}](experiments/{identifier}/notes.md): '+('median %.9f s, reference AP50=%s; submitted=%s.'%(metric['median_seconds'],metric['reference_ap50_per_run'],metric['submitted']) if metric['status']=='success' else 'FAILED: '+metric['error'])+'\n')
    results.append(dict(experiment=identifier,**metric))
    manifest.write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
print('MANIFEST',manifest,'BEST',best_time,str(best_log),flush=True)
