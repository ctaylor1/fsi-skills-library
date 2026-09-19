import copy
import json
from pathlib import Path
import unittest
from calculate_or_transform import compute


class Phase1Tests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/logs_example.json").read_text())

    def test_success_not_failure(self):
        d = copy.deepcopy(self.doc)
        d["log_entries"] = [{"request_id": "x", "endpoint": "/charges", "http_status": 200, "message": "success"}]
        r = compute(d)
        self.assertEqual(r["total_failures"], 0)
        self.assertFalse(r["success_denominator_verified"])

    def test_frequency_not_cause(self):
        r = compute(self.doc)
        self.assertIsNone(r["suspected_cause"])
        self.assertIn("not established", r["causality"])

    def test_mask_message(self):
        d = copy.deepcopy(self.doc)
        d["log_entries"][0]["message"] = "PAN 4111111111111111"
        self.assertNotIn("4111111111111111", json.dumps(compute(d)))


    def test_published_timestamp_fields(self):
        d=copy.deepcopy(self.doc)
        d['integration']['window']={'start':'2026-08-01T00:00:00Z','end':'2026-09-01T00:00:00Z'}
        d['log_entries'][0]['ts']='2026-08-15T01:00:00Z'
        r=compute(d)
        self.assertEqual(r['window'],d['integration']['window'])
        self.assertEqual(r['classified_entries'][0]['timestamp'],d['log_entries'][0]['ts'])

if __name__ == "__main__":
    unittest.main()
