"""Reproduce baseline, stage timings or CUDA trace with explicit saved config.

Example: python tools/profile_fast544.py --config experiments/ID/config.json
         --output-dir output/ID/stages --mode stages
Baseline and stages default to three independent workers; trace defaults to one.
The official timer and validator are used without modification.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--mode', choices=['baseline', 'stages', 'trace'], default='baseline')
    parser.add_argument('--runs', type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = json.loads(Path(args.config).read_text())
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, **config}
    env.pop('FAST_PROFILE', None)
    if args.mode == 'stages':
        env['FAST_PROFILE'] = '1'
    python = config.get('PYTHON_BIN', sys.executable)
    runs = args.runs or (1 if args.mode == 'trace' else 3)
    command = [python, 'supership/benchmark_submission.py',
               '--image-dir', 'data/SuperShip/reference/images',
               '--meta-file', 'data/SuperShip/reference/reference_images_meta.json',
               '--output-file', str(output / 'predictions.json'), '--runs', str(runs), '--']
    command += ([python, 'supership/profile_fast_worker.py'] if args.mode == 'trace'
                else ['bash', 'run.sh', '--worker'])
    (output / 'command.json').write_text(json.dumps(dict(
        command=command, config=config, cwd=str(root), mode=args.mode,
    ), indent=2) + '\n')
    with (output / 'benchmark.log').open('w') as log:
        subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    print((output / 'benchmark.log').read_text())
    for index in range(1, runs + 1):
        prediction = output / (f'predictions.run{index}.json' if runs > 1 else 'predictions.json')
        with (output / f'score{index}.log').open('w') as log:
            subprocess.run([python, 'supership/score_submission.py', '--gt',
                            'data/SuperShip/reference/annotations/instances_reference.json',
                            '--submission', str(prediction)], cwd=root, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)


if __name__ == '__main__':
    main()
