#!/usr/bin/env python3
"""Deterministic input validation for settlement-report-summarizer.

Validates a merchant settlement/payout report against the documented schema BEFORE
summarizing. Fails closed on structural problems; warns (does not fail) on data-quality
gaps the summary must surface (unvalued lines, currency mismatches, unknown categories).

Input schema (JSON):
{
  "merchant_id": "str",              # masked (last 4)
  "report_id": "str",
  "processor": "str"(opt),
  "as_of_date": "YYYY-MM-DD",        # settlement/statement date
  "period": {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"}(opt),
  "settlement_currency": "USD",
  "funding": {"expected_net":num,"funding_date":"YYYY-MM-DD","bank_account":"str"}(opt),
  "lines": [
    {"line_id","category","description","card_brand"(opt),"count"(opt),
     "gross_amount"(opt),"fee_amount"(opt),"net_amount"(opt),"currency",
     "settlement_date"(opt),"source":{"system","ref"}}
  ]
}

Signed-amount convention: credits to the merchant are positive; refunds, chargebacks,
fees, and reserves are negative. The category taxonomy is documented in
../references/domain-rules.md.

Usage:
  python validate_input.py settlement.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("merchant_id", "report_id", "as_of_date", "settlement_currency", "lines")
REQUIRED_LINE = ("line_id", "category", "description", "currency", "source")
KNOWN_CATEGORIES = {
    "gross_sales", "refunds", "chargebacks", "interchange_fees", "scheme_fees",
    "processor_fees", "other_fees", "fees", "adjustments", "reserve_held",
    "reserve_released", "cash_advance", "net_settlement",
}
AMOUNT_FIELDS = ("gross_amount", "fee_amount", "net_amount")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of_date"])):
        errors.append(f"as_of_date must be YYYY-MM-DD, got {doc['as_of_date']!r}")

    lines = doc.get("lines") or []
    if not isinstance(lines, list) or not lines:
        errors.append("lines must be a non-empty list")
        return errors, warnings

    base_ccy = doc["settlement_currency"]
    settlement_dates = set()
    for i, ln in enumerate(lines):
        tag = f"lines[{i}] ({ln.get('line_id', '?')})"
        for k in REQUIRED_LINE:
            if k not in ln or ln[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        src = ln.get("source") or {}
        if not (src.get("system") and src.get("ref")):
            errors.append(f"{tag}: source must include 'system' and 'ref' (citation)")

        cat = ln.get("category")
        if cat and cat not in KNOWN_CATEGORIES:
            warnings.append(f"{tag}: unknown category {cat!r} - map to the documented taxonomy or list as 'other'")

        has_amount = any(_num(ln.get(f)) is not None for f in AMOUNT_FIELDS)
        if not has_amount:
            warnings.append(f"{tag}: no gross/fee/net amount - report as 'not valued' and exclude from the tie-out")

        gross = _num(ln.get("gross_amount"))
        fee = _num(ln.get("fee_amount"))
        net = _num(ln.get("net_amount"))
        # For a pure fee line, net is expected to be the negative of the stated fee.
        if fee is not None and net is not None and gross is None:
            if abs((-abs(fee)) - net) > max(0.01, abs(net) * 0.005):
                warnings.append(f"{tag}: net_amount {net} is not the negative of fee_amount {fee} - confirm sign convention")

        if ln.get("currency") and base_ccy and ln["currency"] != base_ccy:
            warnings.append(f"{tag}: currency {ln['currency']} != settlement {base_ccy} - requires cited FX to include in the settlement total")
        if ln.get("settlement_date"):
            settlement_dates.add(ln["settlement_date"])

    if len(settlement_dates) > 1:
        errors.append(f"lines carry multiple settlement dates {sorted(settlement_dates)} - do not merge batches; confirm a single settlement")

    funding = doc.get("funding") or {}
    if funding and funding.get("funding_date") and not DATE_RE.match(str(funding["funding_date"])):
        errors.append(f"funding.funding_date must be YYYY-MM-DD, got {funding['funding_date']!r}")

    return errors, warnings


def _report(errors, warnings) -> int:
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "settlement_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif len(argv) >= 1:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
