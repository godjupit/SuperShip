"""Pair entry/return probes for this worker, in an isolated tracing instance."""
import os,sys,time
from pathlib import Path
marker=Path(sys.argv[1]);pid=sys.argv[2];output=Path(sys.argv[3]);deadline=time.monotonic()+180
while not marker.with_suffix('.ready').exists():
 if time.monotonic()>deadline:sys.exit('ready timeout')
 time.sleep(.005)
base=Path('/sys/kernel/tracing');trace=base/'instances'/('supership-events-'+pid);group='supership_exit_'+pid
functions=['exit_mmap','exit_files','unmap_vmas','free_pgtables','unmap_single_vma','__mmu_notifier_invalidate_range_start','uvm_va_space_mm_shutdown']
created=[];trace.mkdir()
def put(name,value):(trace/name).write_text(value)
def probe(value):
 with (base/'kprobe_events').open('a') as f:f.write(value+'\n')
try:
 put('tracing_on','0');put('buffer_size_kb','8192');put('set_event_pid',' '.join(p.name for p in Path('/proc',pid,'task').iterdir()))
 for i,fn in enumerate(functions):
  entry='p'+str(i);ret='r'+str(i)
  extra=' start=+0(%si):x64 end=+8(%si):x64' if fn=='unmap_single_vma' else ''
  probe(f'p:{group}/{entry} {fn}{extra}');created.append(entry)
  probe(f'r128:{group}/{ret} {fn}');created.append(ret)
 put(f'events/{group}/enable','1');put('tracing_on','1');marker.with_suffix('.armed').touch()
 while Path('/proc',pid).exists() and time.monotonic()<deadline:time.sleep(.002)
 put('tracing_on','0');output.write_text((trace/'trace').read_text())
finally:
 put('tracing_on','0')
 if (trace/'events'/group/'enable').exists():put(f'events/{group}/enable','0')
 trace.rmdir()
 for event in reversed(created):probe(f'-:{group}/{event}')
