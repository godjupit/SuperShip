"""Summarize an inference-only Nsight Systems SQLite export, read-only."""

import argparse
import json
from pathlib import Path
import sqlite3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sqlite", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; choose a new path")
    db = sqlite3.connect(args.sqlite.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    kernels = [dict(row) for row in db.execute("""
        SELECT s.value AS name, count(*) AS calls,
               sum(k.end-k.start)/1e6 AS milliseconds,
               avg(k.end-k.start)/1e3 AS mean_microseconds
        FROM CUPTI_ACTIVITY_KIND_KERNEL k JOIN StringIds s ON s.id=k.demangledName
        GROUP BY s.value ORDER BY milliseconds DESC
    """)]
    total = sum(row["milliseconds"] for row in kernels)
    for row in kernels:
        row["kernel_time_percent"] = row["milliseconds"] / total * 100
    intervals = [tuple(row) for row in db.execute("""
        SELECT start,end FROM CUPTI_ACTIVITY_KIND_KERNEL
        UNION ALL SELECT start,end FROM CUPTI_ACTIVITY_KIND_MEMCPY ORDER BY start
    """)]
    if not intervals:
        parser.error("no GPU activity; verify capture succeeded")
    start, end = intervals[0]
    busy = 0
    for left, right in intervals[1:]:
        if left > end:
            busy += end - start
            start, end = left, right
        else:
            end = max(end, right)
    busy += end - start
    span = max(right for _, right in intervals) - intervals[0][0]
    api = [dict(row) for row in db.execute("""
        SELECT s.value AS name,count(*) AS calls,
               sum(r.end-r.start)/1e6 AS host_duration_ms
        FROM CUPTI_ACTIVITY_KIND_RUNTIME r JOIN StringIds s ON s.id=r.nameId
        GROUP BY s.value ORDER BY host_duration_ms DESC
    """)]
    summary = dict(
        scope="Inference-only cudaProfilerApi range; 200 reference images; not official E2E",
        kernel_count=sum(row["calls"] for row in kernels), kernel_sum_ms=total,
        kernels=kernels,
        short_kernel_calls_under_5us=db.execute(
            "SELECT count(*) FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE end-start<5000"
        ).fetchone()[0],
        gpu_activity_union_ms=busy / 1e6, first_to_last_gpu_activity_ms=span / 1e6,
        gpu_activity_union_fraction=busy / span,
        graph_launches=sum(row["calls"] for row in api if row["name"].startswith("cudaGraphLaunch")),
        graph_kernel_count=db.execute(
            "SELECT count(*) FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE graphNodeId!=0"
        ).fetchone()[0],
        cuda_api=api,
        memcpy=[dict(row) for row in db.execute("""
            SELECT copyKind,count(*) AS calls,sum(bytes) AS bytes,
                   sum(end-start)/1e6 AS milliseconds
            FROM CUPTI_ACTIVITY_KIND_MEMCPY GROUP BY copyKind
        """)],
    )
    args.output.write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
