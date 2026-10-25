"""Isolated ftrace instance, limited to this worker's threads; diagnostic only."""
import json,os,sys,time
from pathlib import Path
marker=Path(sys.argv[1]);pid=sys.argv[2];output=Path(sys.argv[3]);deadline=time.monotonic()+180
while not marker.with_suffix('.ready').exists():
 if time.monotonic()>deadline:sys.exit('ready timeout')
 time.sleep(.005)
trace=Path('/sys/kernel/tracing/instances')/('supership-exit-'+pid)
trace.mkdir()
def put(name,value):(trace/name).write_text(value)
try:
 put('tracing_on','0');put('buffer_size_kb','4096');put('set_ftrace_pid',' '.join(p.name for p in Path('/proc',pid,'task').iterdir()))
 put('current_tracer','function');put('set_ftrace_filter','exit_mmap\nexit_files\nnv_free_system_pages\nnv_free_pages\nset_pages_array_wb\n')
 put('tracing_on','1');marker.with_suffix('.armed').touch()
 while Path('/proc',pid).exists() and time.monotonic()<deadline:time.sleep(.002)
 put('tracing_on','0');output.write_text((trace/'trace').read_text())
finally:
 put('tracing_on','0');put('current_tracer','nop');trace.rmdir()
