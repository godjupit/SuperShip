"""Derive exclusive CPU stages and independent overlapping GPU evidence."""
import collections,hashlib,json,statistics,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];exp=Path(__file__).resolve().parent;out=root/'output'/exp.name

def group(source):
    if 'loaded = [job.result()' in source:return 'input_future_wait'
    if 'event.synchronize()' in source:return 'gpu_output_event_wait'
    if 'results = bulk_results' in source:return 'bulk_format'
    if 'orjson.dumps' in source:return 'json_serialize'
    if 'os.fsync' in source:return 'fsync'
    if 'f.write(payload)' in source or 'f.flush()' in source:return 'write_flush'
    if 'self.graph.replay()' in source:return 'graph_launch_host'
    if 'copy_(' in source:return 'transfer_submit_host'
    if 'schedule(' in source:return 'schedule_host'
    if 'collect(' in source:return 'snapshot_collect'
    if 'self.pool.shutdown' in source:return 'thread_shutdown'
    if 'metadata = ' in source:return 'metadata'
    return 'other_host'

runs=json.loads((exp/'runs.json').read_text());data=dict(formal=runs['runs'][0],source_commit=runs['source_commit'],boundary=[],line=[],io=[],gpu=[])
for mode in ['boundary','line','io']:
    case=out/mode;observer=next(json.loads(l) for l in (case/'stdout.log').read_text().splitlines() if l.startswith('{') and '"parent"' in l)
    marks=[json.loads(l) for l in (case/'stderr.log').read_text().splitlines() if l.startswith('{') and 'before_exit_ns' in l]
    timer=next(json.loads(l) for l in (case/'stdout.log').read_text().splitlines() if l.startswith('{') and 'runs_seconds' in l)
    for i,p in enumerate(sorted(case.glob('*.stages.json'))):
        d=json.loads(p.read_text());row=dict(round=i+1,runtime_ms=d['runtime_ms'],exit_ms=(observer['exits'][i]['end_ns']-marks[i]['before_exit_ns'])/1e6,diagnostic_dump_ms=(marks[i]['before_exit_ns']-d['run_finished_ns'])/1e6,total_ms=timer['runs_seconds'][i]*1000)
        row['protocol_misc_ms']=row['total_ms']-row['runtime_ms']-row['exit_ms']-row['diagnostic_dump_ms']
        if mode=='line':
            stages=collections.defaultdict(float)
            for line in d['lines']:stages[group(line['source'])]+=line['milliseconds']
            row['line_accounted_ms']=sum(stages.values())
            intervals=d['intervals'];span=(intervals[-1][2]-intervals[0][1])/1e6
            assert abs(row['line_accounted_ms']-span)<1e-5
            residual=row['runtime_ms']-row['line_accounted_ms'];assert 0<=residual<5
            stages['outside_frame_context_and_probe']=residual
            row['main_thread_exclusive_ms']=dict(stages)
            load=d['loads'];row['load_service_sum_ms']=sum((b-a)/1e6 for a,b,*_ in load);row['load_wall_span_ms']=(max(b for a,b,*_ in load)-min(a for a,b,*_ in load))/1e6
            cv=collections.defaultdict(list)
            for n,a,b in d['cv_calls']:cv[n].append((b-a)/1e6)
            row['cv_thread_service']={k:dict(calls=len(v),sum_ms=sum(v),median_ms=statistics.median(v),max_ms=max(v)) for k,v in cv.items()}
        if mode=='io':
            for k in ['io_delta','cpu_user_ms','cpu_system_ms','major_faults']:row[k]=d[k]
            row['mean_cpu_cores']=(d['cpu_user_ms']+d['cpu_system_ms'])/d['runtime_ms']
        data[mode].append(row)
for name in ['nsys1','nsys2']:
    d=json.loads((out/name/'summary.json').read_text());data['gpu'].append(dict(name=name,**d,gpu_idle_gaps_ms=d['first_to_last_gpu_activity_ms']-d['gpu_activity_union_ms']))
data['accuracy']=dict(reference_ap50=[r['reference_ap50'] for r in runs['runs']],validation_ap50_parent=.9058,validation_measured_this_experiment=False,hidden_ap50=None)
data['caveats']=['CPU future wait overlaps GPU execution and is not pure GPU idle time.','Nsight activity coverage is not SM utilization.','Do not add CPU stage totals to GPU kernel or transfer totals.','Line probes perturb scheduling and dump diagnostics before exit; formal baseline remains separate.','Warm-cache IO counters do not predict cold-disk or hidden-set behavior.']
(exp/'summary.json').write_text(json.dumps(data,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=json.loads((root/'experiments/20261026-000619-exit-rootcause/data-checksums.json').read_text())
for name in ['weights/baseline.pth','data/SuperShip/reference/reference_images_meta.json','data/SuperShip/reference/annotations/instances_reference.json','supership/benchmark_submission.py','supership/submission.py','supership/score_submission.py','COMPETITION.md']:assert sha(root/name)==parent[name],name
images=root/'data/SuperShip/reference/images';manifest='\n'.join(f'{sha(p)}  {p.name}' for p in sorted(images.iterdir()) if p.is_file())+'\n';assert hashlib.sha256(manifest.encode()).hexdigest()==parent['reference_images']['sorted_manifest_sha256']
(exp/'checksums.json').write_text(json.dumps(dict(parent_asset_manifest=parent,source_runtime_unchanged_from='6a774ee',source_files={str(p.relative_to(root)):sha(p) for prefix in ['engine','supership'] for p in sorted((root/prefix).rglob('*.py'))},artifacts={str(p.relative_to(out)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()},raw_primary='/home/ubuntu/SuperShip-main 2/output/'+exp.name,raw_original=str(out),local_only=True),indent=2)+'\n')
print(json.dumps(dict(boundary=data['boundary'],io=data['io'],line_stages=[r['main_thread_exclusive_ms'] for r in data['line']],gpu=[{k:r[k] for k in ['kernel_sum_ms','gpu_activity_union_ms','first_to_last_gpu_activity_ms','gpu_idle_gaps_ms']} for r in data['gpu']]),indent=2))
