"""Read only this diagnostic worker's exit-time kernel stacks (requires root)."""
import json,sys,time
from pathlib import Path
marker=Path(sys.argv[1]);pid=sys.argv[2];output=Path(sys.argv[3]);deadline=time.monotonic()+180
while not marker.exists():
 if time.monotonic()>deadline:sys.exit('marker timeout')
 time.sleep(.005)
rows=[];deadline=time.monotonic()+.4
while time.monotonic()<deadline:
 row={'ns':time.monotonic_ns(),'tasks':[]}
 try:tasks=list(Path('/proc',pid,'task').iterdir())
 except FileNotFoundError:break
 for task in tasks:
  data={'tid':task.name}
  for field in ['comm','wchan','stack','stat']:
   try:data[field]=(task/field).read_text()
   except (FileNotFoundError,ProcessLookupError,PermissionError) as e:data[field]=type(e).__name__
  row['tasks'].append(data)
 rows.append(row);time.sleep(.002)
output.write_text(json.dumps(rows,indent=2)+'\n')
