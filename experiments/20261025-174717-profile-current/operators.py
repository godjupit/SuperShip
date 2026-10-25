"""Attribute eager operators to modules at the same shapes; not graph timing."""
import argparse,json,os,sys,collections
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);a=p.parse_args()
if Path(a.output).exists() or Path(a.output).with_suffix('.trace.json').exists():p.error('Output exists; choose unique paths')
os.environ.update(json.loads(Path(a.config).read_text()));sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import torch
from supership.fast_worker import Runtime
runtime=Runtime()
# All real input access starts after initialization. This separate diagnostic has no READY score.
items=json.loads(Path('data/SuperShip/reference/reference_images_meta.json').read_text())['images'][:runtime.batch]
sizes=[runtime.load_image(item,'data/SuperShip/reference/images',runtime.host_arrays[0][i]) for i,item in enumerate(items)]
with torch.inference_mode():
 runtime.images.copy_(runtime.host[0],non_blocking=True);runtime.sizes.copy_(torch.tensor(sizes,dtype=torch.float32),non_blocking=True)
 runtime.forward();torch.cuda.synchronize()
 stacks=collections.defaultdict(list)
 def pre(name):
  def hook(module,args):
   context=torch.profiler.record_function('module::'+name);context.__enter__();stacks[id(module)].append(context)
  return hook
 def post(module,args,result):stacks[id(module)].pop().__exit__(None,None,None)
 handles=[]
 for name,module in runtime.model.named_modules():
  handles.extend([module.register_forward_pre_hook(pre(name)),module.register_forward_hook(post)])
 with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA],record_shapes=True) as profile:
  runtime.forward();torch.cuda.synchronize()
 for h in handles:h.remove()
 events=[]
 for event in profile.events():
  if event.name in ('aten::copy_','aten::_to_copy','aten::clone','aten::contiguous','aten::cat','aten::linear','aten::add','aten::mul'):
   parent=event.cpu_parent;modules=[]
   while parent is not None:
    if parent.name.startswith('module::'):modules.append(parent.name[8:])
    parent=parent.cpu_parent
   events.append(dict(operator=event.name,shapes=event.input_shapes,module=modules[0] if modules else '<preprocess/postprocess>',module_chain=modules,cpu_us=event.cpu_time_total,cuda_us=event.device_time_total))
 Path(a.output).write_text(json.dumps(dict(scope='Eager diagnostic for attribution only; hooks/profiler overhead; GPU graph formal ranking comes from Nsight',events=events),indent=2)+'\n')
 profile.export_chrome_trace(str(Path(a.output).with_suffix('.trace.json')))
 runtime.pool.shutdown(wait=True)
print('operators',len(events))
