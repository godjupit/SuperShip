"""Ten alternating pairs using official single-run worker timing and scoring."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from run_kernel_sweep import PYTHON, digest, execute, score, version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    os.chdir(ROOT)
    identifier = dt.datetime.now().strftime('%Y%m%d-%H%M%S') + '-kernel-paired10'
    exp, out = ROOT / 'experiments' / identifier, ROOT / 'output' / identifier
    exp.mkdir(); out.mkdir(parents=True)
    configs = {'control': json.loads(args.control.read_text()),
               'candidate': json.loads(args.candidate.read_text())}
    plans = []
    for pair in range(1, 11):
        order = ['control', 'candidate'] if pair % 2 else ['candidate', 'control']
        for name in order:
            relative = f'pair{pair:02d}-{name}'
            detail, artifact = exp / relative, out / relative
            detail.mkdir(); artifact.mkdir()
            config = configs[name] | {'TRITON_CACHE_DIR': str(artifact / 'triton-cache')}
            command = [PYTHON, 'supership/benchmark_submission.py', '--image-dir',
                       'data/SuperShip/reference/images', '--meta-file',
                       'data/SuperShip/reference/reference_images_meta.json', '--output-file',
                       str(artifact / 'prediction.json'), '--runs', '1', '--',
                       'env', 'PYTHON_BIN=' + PYTHON, 'bash', 'run.sh', '--worker']
            (detail / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
            (detail / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
            plans.append(dict(pair=pair, name=name, directory=relative, command=command))
    (exp / 'plan.json').write_text(json.dumps(plans, indent=2) + '\n')
    (exp / 'notes.md').write_text('# Kernel candidate ten-pair confirmation\n\n'
        'Status planned. AB/BA alternation, independent worker initialization for every run, '
        'same public 200 images and official timing/validation. Per-run config/command versioned '
        'before execution. GPU0 RTX4090 exclusive. Full validation precision is measured in '
        'the candidate parent; not measured in these single reference runs. No competition submission '
        'from concatenated paired logs.\n')
    with (ROOT / 'OPTIMIZATION_EXPERIMENTS.md').open('a') as f:
        f.write(f'\n## {dt.date.today()}｜{identifier}｜planned\n\n'
                f'GPU0 RTX4090 exclusive; Codex /root; [10对交错确认](experiments/{identifier}/notes.md).\n')
    version([exp, ROOT / 'OPTIMIZATION_EXPERIMENTS.md'], 'Register ten alternating kernel candidate pairs')
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    results = []
    for plan in plans:
        detail, artifact = exp / plan['directory'], out / plan['directory']
        env = os.environ | json.loads((detail / 'config.json').read_text())
        text = execute(plan['command'], env, artifact / 'benchmark.log')
        timing = json.loads(next(line for line in reversed(text.splitlines())
                                 if line.startswith('{"runs_seconds"')))
        ap = score(artifact / 'prediction.json',
                   'data/SuperShip/reference/annotations/instances_reference.json',
                   artifact / 'score.log', env)
        result = dict(pair=plan['pair'], name=plan['name'], seconds=timing['median_seconds'],
                      reference_ap50=ap, source_commit=source, source_dirty=False,
                      artifact_directory=str(artifact), status='success' if ap >= .7935*.98 else 'rejected_precision')
        results.append(result)
        (out / 'progress.json').write_text(json.dumps(results, indent=2) + '\n')
        print('PAIR', plan['pair'], plan['name'], result['seconds'], ap, flush=True)
    control = [r['seconds'] for r in results if r['name'] == 'control']
    candidate = [r['seconds'] for r in results if r['name'] == 'candidate']
    comparisons = [dict(pair=i+1, control=control[i], candidate=candidate[i],
                        difference_seconds=control[i]-candidate[i]) for i in range(10)]
    # Paired bootstrap quantifies run variability without treating a fast single run as proof.
    import numpy as np
    differences = np.array([p['difference_seconds'] for p in comparisons])
    rng = np.random.default_rng(42)
    bootstrap = np.median(rng.choice(differences, size=(10000, 10), replace=True), axis=1)
    summary = dict(source_commit=source, status='completed', results=results, pairs=comparisons,
                   control_median_seconds=statistics.median(control),
                   candidate_median_seconds=statistics.median(candidate),
                   median_reduction_percent=(1-statistics.median(candidate)/statistics.median(control))*100,
                   wins=sum(a < b for a, b in zip(candidate, control)),
                   paired_median_difference_seconds=statistics.median(differences),
                   paired_bootstrap_median_difference_95ci=np.quantile(bootstrap, [.025,.975]).tolist(),
                   bootstrap_seed=42, bootstrap_resamples=10000, validation_ap50=None, hidden_ap50=None,
                   competition_submitted=False, artifact_directory=str(out),
                   weight_sha256=digest('weights/baseline.pth'),
                   metadata_sha256=digest('data/SuperShip/reference/reference_images_meta.json'))
    for result, plan in zip(results, plans):
        artifact = out / plan['directory']
        result['artifacts_sha256'] = {p.name: digest(p) for p in artifact.iterdir() if p.is_file()}
        (exp / plan['directory'] / 'metrics.json').write_text(json.dumps(result, indent=2) + '\n')
    (exp / 'metrics.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('SUMMARY', json.dumps({k:v for k,v in summary.items() if k not in ['results','pairs']}), flush=True)
    with (exp / 'notes.md').open('a') as f:
        f.write(f'\nCompleted; source `{source}`; control median {summary["control_median_seconds"]:.9f}s, '
                f'candidate {summary["candidate_median_seconds"]:.9f}s, '
                f'{summary["wins"]}/10 pairs faster. Full measurements and checksum values in metrics.json. '
                'Large artifacts local only; software/weight configuration matches the parent sweep.\n')
    ledger = ROOT / 'OPTIMIZATION_EXPERIMENTS.md'
    text = ledger.read_text().replace(f'{identifier}｜planned', f'{identifier}｜completed')
    text += f'\n10对：control={summary["control_median_seconds"]:.9f}s，candidate={summary["candidate_median_seconds"]:.9f}s，改善{summary["median_reduction_percent"]:.2f}%，{summary["wins"]}/10更快；完整逐轮精度和bootstrap区间见详细记录。\n'
    ledger.write_text(text)
    version([exp, ledger], 'Record all ten alternating kernel confirmation pairs')


if __name__ == '__main__':
    main()
