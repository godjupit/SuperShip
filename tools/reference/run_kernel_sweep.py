"""Version, benchmark, score and optionally submit independent kernel experiments."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PYTHON = '/home/ubuntu/.cache/supership-venv/bin/python'
BASE_CONFIG = ROOT / 'experiments/20261023-235500-main-fastest-merge/config.json'
OPTIONS = dict(KERNEL_WEIGHT_HALF='0', KERNEL_AFFINE_HALF='0', KERNEL_ENCODER_LAYOUT='0',
               KERNEL_LINEAR1X1='0', FEATURE_CAT='torch')
CASES = {
    'control': {},
    'weight-half': dict(KERNEL_WEIGHT_HALF='1'),
    'affine-half': dict(KERNEL_AFFINE_HALF='1'),
    'concat-half': dict(FEATURE_CAT='triton_half'),
    'encoder-layout': dict(KERNEL_ENCODER_LAYOUT='1'),
    'linear1x1': dict(KERNEL_LINEAR1X1='1'),
    'weights-affine': dict(KERNEL_WEIGHT_HALF='1', KERNEL_AFFINE_HALF='1'),
    'weights-affine-layout': dict(KERNEL_WEIGHT_HALF='1', KERNEL_AFFINE_HALF='1', KERNEL_ENCODER_LAYOUT='1'),
    'weights-affine-concat': dict(KERNEL_WEIGHT_HALF='1', KERNEL_AFFINE_HALF='1', FEATURE_CAT='triton_half'),
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute(command, env, path, timeout=600):
    with path.open('w') as output:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=output,
                                stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'exit {result.returncode}; see {path}')
    return path.read_text()


def version(paths, message):
    subprocess.run(['git', 'add', *[str(p) for p in paths]], cwd=ROOT, check=True)
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    subprocess.run(['git', 'commit', '-m', message], cwd=ROOT, check=True)


def submit(log, response):
    # Local credentials stay outside versioned files and commands.
    local = Path('/home/ubuntu/SuperShip-main 2/.local')
    env = os.environ | {'THUSCC_CREDENTIALS_FILE': str(local / '.thuscc_credentials')}
    before = digest(log)
    text = execute(['bash', str(local / 'submit.sh'), 'SUPERSHIP', str(log)],
                   env, response, timeout=180)
    if digest(log) != before or 'Submission Accepted' not in text:
        raise RuntimeError(f'submission not accepted or log changed: {response}')
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def score(prediction, gt, output, env):
    text = execute([PYTHON, 'supership/score_submission.py', '--gt', gt,
                    '--submission', str(prediction)], env, output)
    return float(re.search(r'AP@0.50\s+([0-9.]+)', text).group(1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cases', nargs='+', choices=list(CASES))
    parser.add_argument('--submit', action='store_true')
    args = parser.parse_args()
    os.chdir(ROOT)
    best = dict(median_seconds=0.330820520,
                log='/home/ubuntu/SuperShip-main 2/output/20261023-235500-main-fastest-merge/reference-benchmark.log',
                origin='20261023-235500-main-fastest-merge')
    for prior in ROOT.glob('experiments/*-kernel-*/metrics.json'):
        data = json.loads(prior.read_text())
        if (data.get('validation_precision_pass') and data.get('reference_precision_pass')
                and data.get('median_seconds', 1e9) < best['median_seconds']):
            candidate = Path(data['artifact_directory']) / 'supership.out'
            if candidate.exists():
                best = dict(median_seconds=data['median_seconds'], log=str(candidate), origin=prior.parent.name)
    for name in args.cases:
        stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
        identifier = f'{stamp}-kernel-{name}'
        exp, out = ROOT / 'experiments' / identifier, ROOT / 'output' / identifier
        exp.mkdir(); out.mkdir(parents=True)
        config = json.loads(BASE_CONFIG.read_text()) | OPTIONS | CASES[name]
        (exp / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
        config["TRITON_CACHE_DIR"] = str(out / "triton-cache")
        (exp / "config.json").write_text(json.dumps(config, indent=2) + "\n")
        env = os.environ | config
        reference_cmd = [PYTHON, 'supership/benchmark_submission.py', '--image-dir',
                         'data/SuperShip/reference/images', '--meta-file',
                         'data/SuperShip/reference/reference_images_meta.json', '--output-file',
                         str(out / 'reference.json'), '--runs', '3', '--',
                         'env', 'PYTHON_BIN=' + PYTHON, 'bash', 'run.sh', '--worker']
        validation_cmd = [PYTHON, 'supership/benchmark_submission.py', '--image-dir',
                          'data/SuperShip/val/images', '--meta-file',
                          'data/SuperShip/val/annotations/instances_val.json', '--output-file',
                          str(out / 'validation.json'), '--runs', '1', '--',
                          'env', 'PYTHON_BIN=' + PYTHON, 'bash', 'run.sh', '--worker']
        (exp / 'commands.json').write_text(json.dumps(dict(reference=reference_cmd,
                                           validation=validation_cmd), indent=2) + '\n')
        (exp / 'notes.md').write_text(f'# Kernel experiment: {name}\n\nStatus planned. '
            'Parent main 121df82; sweep 20261024-000500-kernel-sweep. '
            'Effective config and exact commands are adjacent. Uses original official READY timing '
            'and output validator; no input access before READY.\n')
        with (ROOT / 'OPTIMIZATION_EXPERIMENTS.md').open('a') as f:
            f.write(f'\n## {dt.date.today()}｜{identifier}｜planned\n\n'
                    f'Codex /root, GPU0 RTX4090 exclusive, exp/kernel-sweep-20261024; '
                    f'[{name}](experiments/{identifier}/notes.md).\n')
        version([exp, ROOT / 'OPTIMIZATION_EXPERIMENTS.md'], f'Register kernel experiment {name}')
        source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        metric = dict(name=name, status='running', source_commit=source, source_dirty=False,
                      parent_experiment='20261023-235500-main-fastest-merge',
                      artifact_directory=str(out), started=dt.datetime.now().isoformat(),
                      gpu='RTX4090 single GPU0', driver='550.142', python='3.12.8',
                      torch='2.6.0+cu124', cuda='12.4', cudnn=90100, triton='3.2.0', opencv='4.11.0',
                      reference_images=200, validation_images=1030, hidden_ap50=None,
                      timing_scope='Official READY to process-group exit including input, fsync; init excluded',
                      weight_file='weights/baseline.pth', weight_sha256=digest('weights/baseline.pth'),
                      reference_metadata_sha256=digest('data/SuperShip/reference/reference_images_meta.json'),
                      validation_metadata_sha256=digest('data/SuperShip/val/annotations/instances_val.json'),
                      official_timer_sha256=digest('supership/benchmark_submission.py'),
                      official_validator_sha256=digest('supership/submission.py'),
                      reference_precision_pass=False, validation_precision_pass=False,
                      validation_ap50=None, submitted=False)
        print('START', identifier, flush=True)
        try:
            text = execute(reference_cmd, env, out / 'supership.out')
            metric.update(json.loads(next(line for line in reversed(text.splitlines())
                                         if line.startswith('{"runs_seconds"'))))
            aps = [score(out / f'reference.run{i}.json',
                         'data/SuperShip/reference/annotations/instances_reference.json',
                         out / f'score{i}.log', env) for i in range(1, 4)]
            metric['reference_ap50_per_run'] = aps
            metric['reference_precision_pass'] = min(aps) >= 0.7935 * .98
            if metric['reference_precision_pass']:
                execute(validation_cmd, env, out / 'validation.out')
                metric['validation_ap50'] = score(out / 'validation.json',
                    'data/SuperShip/val/annotations/instances_val.json', out / 'validation-score.log', env)
                metric['validation_precision_pass'] = metric['validation_ap50'] >= 0.9170 * .98
            metric['status'] = 'success' if metric['validation_precision_pass'] else 'rejected_precision'
            valid = metric['reference_precision_pass'] and metric['validation_precision_pass']
            if valid and name != 'control' and args.submit:
                response = submit(out / 'supership.out', out / 'submission-response.txt')
                metric['submitted'] = True
                (exp / 'submission-response.txt').write_text(response)
                if metric['median_seconds'] >= best['median_seconds']:
                    restored = submit(Path(best['log']), out / 'restore-best-response.txt')
                    (exp / 'restore-best-response.txt').write_text(restored)
                    metric['restored_best'] = best.copy()
            if valid and metric['median_seconds'] < best['median_seconds']:
                best = dict(median_seconds=metric['median_seconds'], log=str(out / 'supership.out'), origin=identifier)
        except Exception as error:
            metric['status'] = 'failed'
            metric['error'] = str(error)
            print('FAIL', name, str(error), flush=True)
        metric['finished'] = dt.datetime.now().isoformat()
        metric['artifacts_sha256'] = {p.name: digest(p) for p in out.iterdir() if p.is_file()}
        (exp / 'metrics.json').write_text(json.dumps(metric, indent=2) + '\n')
        with (exp / 'notes.md').open('a') as f:
            f.write(f'\nRuntime source `{source}`, tracked code/config committed; no patch. '
                    f'Status {metric["status"]}. All timings, scores, versions, checksum values and '
                    'local-only raw artifact paths are in metrics.json. Phases overlap; only official '
                    'end-to-end time is a performance score. Hidden precision unmeasured.\n')
        ledger = ROOT / 'OPTIMIZATION_EXPERIMENTS.md'
        text = ledger.read_text().replace(f'{identifier}｜planned', f'{identifier}｜{metric["status"]}')
        text += (f'\n{name}: runs={metric.get("runs_seconds")}, median={metric.get("median_seconds")}, '
                 f'reference AP50={metric.get("reference_ap50_per_run")}, validation AP50='
                 f'{metric.get("validation_ap50")}, submitted={metric["submitted"]}. '
                 f'Error={metric.get("error")}.\n')
        ledger.write_text(text)
        version([exp, ledger], f'Record kernel experiment {name} results and submission status')
        subprocess.run(['git', 'push', 'origin', 'HEAD'], check=True)
        print('RESULT', name, metric.get('median_seconds'), metric.get('validation_ap50'),
              metric['status'], 'submitted', metric['submitted'], flush=True)
    print('BEST', json.dumps(best), flush=True)


if __name__ == '__main__':
    main()
