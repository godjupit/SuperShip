"""Run registered complete three-round cases; retain failures and sanitized receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime

exp = Path(__file__).resolve().parent
root = exp.parents[1]
out = root / 'output' / exp.name
out.mkdir(parents=True, exist_ok=True)
p = argparse.ArgumentParser()
p.add_argument('--select', nargs='*')
p.add_argument('--submit', action='store_true')
a = p.parse_args()
results = out / 'results.json'
state = json.loads(results.read_text()) if results.exists() else dict(best_seconds=.266237340, cases=[])
plan = json.loads((exp / 'plan.json').read_text())
for variant in (a.select or plan):
    assert variant in plan
    name = datetime.now().strftime('%Y%m%d-%H%M%S-') + variant
    command = [sys.executable, str(exp / 'run_case.py'), variant, '--name', name,
               '--runs', '3', '--combined-log', '--split', 'reference']
    run = subprocess.run(command, cwd=root, capture_output=True, text=True)
    case = out / name
    (case / 'driver.log').write_text(run.stdout + run.stderr)
    m = json.loads((case / 'metrics.json').read_text())
    record = dict(variant=variant, case=name, status=m['status'], submitted=False)
    if run.returncode == 0:
        record.update(median_seconds=m['median_seconds'], runs_seconds=m['runs_seconds'],
                      ap50=[s['ap50'] for s in m['scores']], precision_pass=m['precision_pass'],
                      log_sha256=m['log_sha256'], source_commit=m['source_commit'])
        if a.submit and m['precision_pass'] and m['median_seconds'] < state['best_seconds']:
            script = Path('/home/ubuntu/SuperShip-main 2/.local/submit.sh')
            cred = script.parent / '.thuscc_credentials'
            assert hashlib.sha256(script.read_bytes()).hexdigest() == 'b6dc5a8cf976fab3e9e0cc9c290521e63ab353fcc263612875e4dc56b9419cdd'
            values = dict(line.split('=', 1) for line in cred.read_text().splitlines() if '=' in line)
            assert values.get('username') == 'ruc2602' and cred.stat().st_mode & 0o777 == 0o600
            log = case / 'supership.out'
            assert hashlib.sha256(log.read_bytes()).hexdigest() == m['log_sha256']
            env = os.environ.copy()
            env['THUSCC_CREDENTIALS_FILE'] = str(cred)
            upload = subprocess.run(['bash', str(script), 'SUPERSHIP', str(log)],
                                    cwd=script.parents[1], env=env, capture_output=True, text=True, timeout=90)
            receipt = upload.stdout + upload.stderr
            for key, value in values.items():
                if key.lower() in ('password', 'passwd', 'token', 'secret') and value:
                    receipt = receipt.replace(value, '<redacted>')
            receipt = re.sub(r'\x1b\[[0-9;]*m', '', receipt)
            (case / 'submission-receipt.txt').write_text(receipt)
            record['submitted'] = upload.returncode == 0 and 'Submission Accepted' in receipt
            record['account'] = 'ruc2602'
            if record['submitted']:
                state['best_seconds'] = m['median_seconds']
            else:
                state['cases'].append(record)
                results.write_text(json.dumps(state, indent=2) + '\n')
                raise RuntimeError('submission failed; sanitized receipt retained')
    state['cases'].append(record)
    results.write_text(json.dumps(state, indent=2) + '\n')
    print(json.dumps(record), flush=True)
