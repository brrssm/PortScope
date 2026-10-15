"""Export scan reports to JSON and CSV."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from portscope.scanner import ScanReport

CSV_FIELDS = ["target", "ip", "scan_timestamp", "port", "status", "response_time_ms", "error"]


def _prepare(path: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def export_json(report: ScanReport, path: str) -> None:
    """Write the report as pretty-printed JSON."""
    data = {
        "target": report.target,
        "ip": report.ip,
        "scan_timestamp": report.timestamp,
        "timeout_seconds": report.timeout,
        "duration_seconds": report.duration_seconds,
        "summary": {
            "open": report.count("open"),
            "closed": report.count("closed"),
            "filtered_or_unknown": report.count("filtered_or_unknown"),
        },
        "results": [asdict(r) for r in report.results],
    }
    with _prepare(path).open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def export_csv(report: ScanReport, path: str) -> None:
    """Write one CSV row per scanned port."""
    with _prepare(path).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in report.results:
            writer.writerow(
                {
                    "target": report.target,
                    "ip": report.ip,
                    "scan_timestamp": report.timestamp,
                    "port": r.port,
                    "status": r.status,
                    "response_time_ms": "" if r.response_time_ms is None else r.response_time_ms,
                    "error": r.error or "",
                }
            )
