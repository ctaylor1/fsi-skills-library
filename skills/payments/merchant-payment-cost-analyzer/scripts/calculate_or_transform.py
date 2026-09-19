#!/usr/bin/env python3
"""Observed merchant-cost decomposition; no default savings or pricing benchmarks."""

import json
import sys
from pathlib import Path
from decimal import Decimal
from payment_contract import money, require_currency, stable_hash

DISCLAIMER = "Observed cost analysis only; no savings estimate, contract decision or external action. Source references are supplied evidence, not independent verification."


def compute(doc):
    currency = require_currency(doc.get("currency"))
    rows = doc.get("transactions")
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonempty transactions required")
    for field in ("merchant_id", "statement_period"):
        if not doc.get(field):
            raise ValueError(field + " required")
    ids = set()
    totals = {k: Decimal(0) for k in ("volume", "interchange", "assessments", "processor_markup")}
    unknown = []
    for row in rows:
        if not row.get("txn_id") or row["txn_id"] in ids:
            raise ValueError("unique transaction identifiers required")
        ids.add(row["txn_id"])
        if not row.get("source_ref"):
            raise ValueError("transaction source_ref required")
        if row.get("currency", currency) != currency:
            raise ValueError("mixed currency statement; partition before analysis")
        if row.get("status", "settled") != "settled":
            raise ValueError("only supplied settled-sale records supported")
        if money(row.get("amount")) <= 0:
            raise ValueError("positive settled sale amount required")
        for output, field in (
            ("volume", "amount"),
            ("interchange", "interchange_fee"),
            ("assessments", "assessment_fee"),
            ("processor_markup", "processor_fee"),
        ):
            totals[output] += money(row.get(field))
        if row.get("level") is None:
            unknown.append(
                {
                    "txn_id": row["txn_id"],
                    "issue": "credential/data level unknown; no qualification or savings inferred",
                }
            )
    fixed = (doc.get("processor") or {}).get("monthly_fees")
    if fixed is None:
        totals["monthly_fixed"] = None
        totals["total_fees"] = None
        unknown.append({"issue": "fixed-fee evidence absent; total cost and all-in effective rate unknown"})
    else:
        if not isinstance(fixed, list):
            raise ValueError("monthly_fees must be a list; [] explicitly asserts none")
        for row in fixed:
            if row.get("currency", currency) != currency:
                raise ValueError("mixed currency fixed fee")
            if not row.get("source_ref"):
                raise ValueError("fixed fee source_ref required")
        totals["monthly_fixed"] = sum((money(r.get("amount")) for r in fixed), Decimal(0))
        totals["total_fees"] = (
            totals["interchange"] + totals["assessments"] + totals["processor_markup"] + totals["monthly_fixed"]
        )

    def bps(value):
        return None if value is None else str((value / totals["volume"] * 10000).quantize(Decimal("0.01")))

    return {
        "analysis_id": "cost-" + stable_hash(doc)[:20],
        "merchant_id": doc["merchant_id"],
        "statement_period": doc["statement_period"],
        "currency": currency,
        "source_snapshot": doc,
        "input_hash": stable_hash(doc),
        "totals": {k: None if v is None else str(v) for k, v in totals.items()},
        "txn_count": len(rows),
        "effective_rate_bps": bps(totals["total_fees"]),
        "implied_markup_bps": bps(totals["processor_markup"]),
        "denominator": "supplied settled-sale volume; not order or authorization attempts",
        "unknowns": unknown,
        "evidence_status": "supplied",
        "opportunities": [],
        "total_estimated_savings": None,
        "limitations": [
            "Statement classification is supplied, not a contract/rate-schedule audit.",
            "No counterfactual savings, qualification or annualization computed.",
            "Refund/FX/tax/chargeback components require separately classified evidence.",
        ],
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/statement_example.json"
        if "--selftest" in argv
        else Path(argv[0])
    )
    try:
        print(json.dumps(compute(json.loads(path.read_text())), indent=2))
        return 0
    except (ValueError, TypeError, KeyError) as exc:
        print("ERROR", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
