#!/usr/bin/env python3
"""Deterministic input validation for trade-confirmation-explainer.

Validates a single trade confirmation against the documented schema BEFORE explaining it.
Fails closed on structural problems (missing required Rule 10b-10 fields, bad dates, unknown
side/capacity, missing citation). Warns (does not fail) on data-quality gaps the explanation
must surface (derivable principal, undisclosed commission/markup, missing yield on debt).

Input schema (JSON) — one confirmation:
{
  "account_id": "str (masked, last 4)",
  "confirmation_id": "str",
  "trade_date": "YYYY-MM-DD",
  "settlement_date": "YYYY-MM-DD",
  "side": "buy|sell",
  "capacity": "agent|principal",
  "currency": "USD",
  "instrument": {"instrument_id","id_type","description","security_type",
                 "source":{"system","ref"}},        # or top-level "source"
  "quantity": num, "price": num, "price_factor": num(opt, default 1.0),
  "principal": num(opt; derivable from quantity*price*price_factor),
  "commission": num(opt), "markup": num(opt), "markdown": num(opt),
  "fees": [{"type","amount"}] (opt) | "fees_total": num(opt),
  "accrued_interest": num(opt), "yield": num(opt),
  "net_amount": num,
  "source": {"system","ref"}    # citation; may live on instrument instead
}

Usage:
  python validate_input.py confirmation.json
  python validate_input.py --selftest        # validate the bundled fixture
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("account_id", "confirmation_id", "trade_date", "settlement_date",
                "side", "capacity", "currency", "net_amount")
SIDES = {"buy", "sell"}
CAPACITIES = {"agent", "principal"}
DEBT_TYPES = {"bond", "note", "debt", "fixed income", "fixed_income", "municipal", "treasury"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _citation(doc: dict) -> dict:
    src = doc.get("source") or (doc.get("instrument") or {}).get("source") or {}
    return src if isinstance(src, dict) else {}


def _fees_total(doc: dict):
    if doc.get("fees_total") is not None:
        return _num(doc.get("fees_total"))
    fees = doc.get("fees")
    if isinstance(fees, list):
        total = 0.0
        for f in fees:
            a = _num((f or {}).get("amount"))
            if a is None:
                return None
            total += a
        return total
    return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing required field '{k}'")
    if errors:
        return errors, warnings

    for k in ("trade_date", "settlement_date"):
        if not DATE_RE.match(str(doc[k])):
            errors.append(f"{k} must be YYYY-MM-DD, got {doc[k]!r}")
    if DATE_RE.match(str(doc["trade_date"])) and DATE_RE.match(str(doc["settlement_date"])):
        if str(doc["settlement_date"]) < str(doc["trade_date"]):
            errors.append(
                f"settlement_date {doc['settlement_date']} precedes trade_date {doc['trade_date']}")

    side = str(doc["side"]).lower()
    if side not in SIDES:
        errors.append(f"side must be one of {sorted(SIDES)}, got {doc['side']!r}")
    cap = str(doc["capacity"]).lower()
    if cap not in CAPACITIES:
        errors.append(f"capacity must be one of {sorted(CAPACITIES)}, got {doc['capacity']!r}")

    instr = doc.get("instrument") or {}
    if not instr.get("instrument_id") or not instr.get("description"):
        errors.append("instrument must include 'instrument_id' and 'description'")
    src = _citation(doc)
    if not (src.get("system") and src.get("ref")):
        errors.append("source must include 'system' and 'ref' (citation to the confirmation)")

    qty = _num(doc.get("quantity"))
    px = _num(doc.get("price"))
    factor = _num(doc.get("price_factor")) or 1.0
    principal = _num(doc.get("principal"))
    if principal is None:
        if qty is not None and px is not None:
            warnings.append("principal missing; derivable from quantity*price*price_factor")
        else:
            errors.append("principal missing and not derivable (need quantity and price)")
    elif qty is not None and px is not None:
        derived = qty * px * factor
        if abs(derived - principal) > max(0.01, abs(principal) * 0.005):
            warnings.append(
                f"principal {principal} != quantity*price*price_factor {derived:.2f} (>0.5%); "
                f"set 'price_factor' (e.g. 0.01 for bonds quoted per 100) if intentional")

    if cap == "agent" and _num(doc.get("commission")) is None:
        warnings.append("capacity 'agent' but no commission disclosed — confirm the agency charge")
    if cap == "principal" and _num(doc.get("markup")) is None and _num(doc.get("markdown")) is None:
        warnings.append(
            "capacity 'principal' but no markup/markdown disclosed — Rule 10b-10 markup disclosure may apply")

    sec_type = str(instr.get("security_type") or "").lower()
    if sec_type in DEBT_TYPES and _num(doc.get("yield")) is None:
        warnings.append("debt security but no yield disclosed — Rule 10b-10 requires yield for debt trades")

    if _fees_total(doc) is None and (doc.get("fees") is not None or doc.get("fees_total") is not None):
        warnings.append("fees present but not summable — provide numeric 'amount' per fee or 'fees_total'")

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
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "confirmation_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif len(argv) >= 1:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    return _report(*validate(doc))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
