import csv
import json
import os
import tempfile
import unittest

from portscope.exporter import CSV_FIELDS, export_csv, export_json
from portscope.scanner import PortResult, ScanReport


def make_report() -> ScanReport:
    return ScanReport(
        target="localhost", ip="127.0.0.1", timestamp="2026-01-01T00:00:00+00:00", timeout=1.0,
        results=[PortResult(22, "open", 0.5), PortResult(23, "closed", 0.3),
                 PortResult(24, "filtered_or_unknown", None, "timed out")],
        duration_seconds=0.1,
    )


class TestExporter(unittest.TestCase):
    def test_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "r.json")  # parent dir is created automatically
            export_json(make_report(), path)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertEqual(data["target"], "localhost")
        self.assertEqual(data["scan_timestamp"], "2026-01-01T00:00:00+00:00")
        self.assertEqual(data["summary"], {"open": 1, "closed": 1, "filtered_or_unknown": 1})
        self.assertEqual(data["results"][0]["port"], 22)
        self.assertIsNone(data["results"][2]["response_time_ms"])

    def test_csv(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "r.csv")
            export_csv(make_report(), path)
            with open(path, newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
        self.assertEqual(list(rows[0].keys()), CSV_FIELDS)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["status"], "open")
        self.assertEqual(rows[2]["response_time_ms"], "")
        self.assertEqual(rows[2]["error"], "timed out")

    def test_bad_path_raises_oserror(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(OSError):
                export_json(make_report(), d)  # a directory is not a writable file


if __name__ == "__main__":
    unittest.main()
