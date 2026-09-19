import copy
import json
from decimal import Decimal
from pathlib import Path
import unittest
from calculate_or_transform import compute


class Phase1Tests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/statement_example.json").read_text())

    def test_decimal_costs(self):
        d = copy.deepcopy(self.doc)
        d["transactions"] = d["transactions"][:1]
        d["transactions"][0].update(amount="10.00", interchange_fee="0.10", assessment_fee="0.20", processor_fee="0.00")
        d["processor"]["monthly_fees"] = []
        r = compute(d)
        self.assertEqual(Decimal(r["totals"]["total_fees"]), Decimal("0.30"))
        self.assertEqual(r["effective_rate_bps"], "300.00")
        self.assertIsNone(r["total_estimated_savings"])

    def test_missing_fixed_not_zero(self):
        d = copy.deepcopy(self.doc)
        d.pop("processor", None)
        r = compute(d)
        self.assertIsNone(r["totals"]["total_fees"])
        self.assertIsNone(r["effective_rate_bps"])

    def test_currency_and_duplicate(self):
        for change in ["currency", "duplicate", "missing"]:
            d = copy.deepcopy(self.doc)
            if change == "currency":
                d["transactions"][0]["currency"] = "EUR"
            if change == "duplicate":
                d["transactions"].append(d["transactions"][0])
            if change == "missing":
                d["transactions"][0]["interchange_fee"] = None
            with self.assertRaises(ValueError):
                compute(d)

    def test_unknown_level(self):
        d = copy.deepcopy(self.doc)
        d["transactions"][0].pop("level", None)
        r = compute(d)
        self.assertTrue(r["unknowns"])
        self.assertEqual(r["opportunities"], [])

    def test_tampered_total(self):
        from validate_output import validate

        r = compute(self.doc)
        r["totals"]["total_fees"] = "0"
        self.assertTrue(validate(r))


if __name__ == "__main__":
    unittest.main()
