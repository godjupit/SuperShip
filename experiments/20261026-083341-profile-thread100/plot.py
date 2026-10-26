"""Plot independent timing views; overlapping rows must not be added."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
exp=Path(__file__).resolve().parent;d=json.loads((exp/'summary.json').read_text());rep=sorted(d['boundary'],key=lambda r:r['total_ms'])[1];line=d['line'][0]['main_thread_exclusive_ms'];gpu=d['gpu'][0]
fig,axes=plt.subplots(3,1,figsize=(11,7.5),gridspec_kw={'hspace':1.25});fig.suptitle('SuperShip thread100-light candidate | RTX 4090 | 200 images',fontsize=14,fontweight='bold')
views=[('Full-process boundary probe',[(f'Runtime {rep["runtime_ms"]:.1f} ms',rep['runtime_ms'],'#3b82f6'),(f'Exit {rep["exit_ms"]:.1f} ms',rep['exit_ms'],'#f97316'),('Protocol + probe',rep['diagnostic_dump_ms']+rep['protocol_misc_ms'],'#94a3b8')]),('GPU timeline only (Nsight)',[(f'GPU active {gpu["gpu_activity_union_ms"]:.1f} ms',gpu['gpu_activity_union_ms'],'#10b981'),(f'Idle gaps {gpu["gpu_idle_gaps_ms"]:.1f} ms',gpu['gpu_idle_gaps_ms'],'#f59e0b')]),('Main thread only (line probe)',[(f'Input futures {line["input_future_wait"]:.1f} ms',line['input_future_wait'],'#3b82f6'),(f'GPU wait {line["gpu_output_event_wait"]:.1f}',line['gpu_output_event_wait'],'#10b981'),('Format / JSON / fsync',line['json_worker_final_wait']+line['json_worker_shutdown']+line['json_join']+line['fsync']+line['write_flush'],'#8b5cf6'),('Other host',sum(line.values())-line['input_future_wait']-line['gpu_output_event_wait']-line['json_worker_final_wait']-line['json_worker_shutdown']-line['json_join']-line['fsync']-line['write_flush'],'#94a3b8')])]
for ax,(title,parts) in zip(axes,views):
 left=0
 for label,value,color in parts:
  ax.barh(0,value,left=left,color=color,height=.55,label=label)
  if value>25:ax.text(left+value/2,0,f'{value:.1f}',ha='center',va='center',color='white',fontsize=10,fontweight='bold')
  left+=value
 ax.set_title(title,loc='left',fontsize=11,pad=30);ax.set_xlim(0,340);ax.set_yticks([]);ax.set_xlabel('Accumulated milliseconds (components grouped; not chronological order)',fontsize=8);ax.spines[['top','right','left']].set_visible(False);ax.legend(loc='lower left',bbox_to_anchor=(0,1.0),ncol=4,fontsize=7,frameon=False)
fig.text(.08,.015,'Independent diagnostic views: do NOT add rows. Input future waits overlap GPU work.\nOfficial uninstrumented median: 259.3 ms; diagnostic schedules and overhead differ.',fontsize=9,color='#475569')
fig.subplots_adjust(top=.84,bottom=.14);fig.savefig(exp/'timing-breakdown.svg',bbox_inches='tight');fig.savefig(exp/'timing-breakdown.png',dpi=150,bbox_inches='tight')
