"""Score a COCO-format submission against released COCO ground truth.

Usage:
  python supership/score_submission.py \
    --gt data/SuperShip/reference/annotations/instances_reference.json \
    --submission output/reference_submission.json
"""
import argparse

from faster_coco_eval import COCO, COCOeval_faster


def per_class_ap(coco_eval):
    """AP@[.5:.95] per category (area=all, maxDets=100)."""
    precision = coco_eval.eval['precision']  # [T, R, K, A, M]
    names = {c['id']: c['name'] for c in coco_gt.loadCats(coco_eval.params.catIds)}
    out = {}
    for k, cat_id in enumerate(coco_eval.params.catIds):
        p = precision[:, :, k, 0, -1]
        p = p[p > -1]
        out[f'{cat_id}:{names[cat_id]}'] = float(p.mean()) if p.size else float('nan')
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gt', required=True, help='COCO ground-truth JSON')
    parser.add_argument('--submission', required=True)
    args = parser.parse_args()

    coco_gt = COCO(args.gt)
    coco_dt = coco_gt.loadRes(args.submission)
    E = COCOeval_faster(coco_gt, cocoDt=coco_dt, iouType='bbox', print_function=print)
    E.evaluate()
    E.accumulate()
    E.summarize()

    names = ['mAP@[.5:.95]', 'AP@0.50', 'AP@0.75', 'AP (small)', 'AP (medium)',
             'AP (large)', 'AR@1', 'AR@10', 'AR@100', 'AR (small)',
             'AR (medium)', 'AR (large)']
    print('\nheadline metrics:')
    for n, v in zip(names, E.stats):
        print(f'  {n:<14s} {v:.4f}')

    print('\nper-class AP@[.5:.95]:')
    for k, v in per_class_ap(E).items():
        print(f'  {k:<30s} {v:.4f}')
