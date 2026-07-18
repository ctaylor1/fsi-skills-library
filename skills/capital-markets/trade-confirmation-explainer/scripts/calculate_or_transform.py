#!/usr/bin/env python3
"""Deterministic computation for trade-confirmation-explainer.

Turns a validated confirmation into a normalized explanation object and ties out the money.
This is descriptive arithmetic only — it reproduces the amounts already on the confirmation
so the plain-language explanation is internally consistent. It never opines on the trade.

Canonical tie-out (documented in references/domain-rules.md):
  principal      = quantity * price * price_factor
  charges_total  = commission + fees_total            (markup/markdown are embedded in the
                                                        principal/price on principal trades and
                                                        are disclosed, not re-added)
  direction      = +1 for buy, -1 for sell
  expected_net   = principal + accrued_interest + direction * charges_total
A buy debits the customer (principal + charges); a sell credits the customer
(principal - charges). Accrued interest is paid to the seller in both directions.

Usage:
  python calculate_or_transform.py confirmation.json     # prints the explanation JSON
  python calculate_or_transform.py --selftest            # tie out the bundled fixture
Exit 0 if the computation ties (0 errors), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

CENTS_TOL = 0.01


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _fees_total(doc: dict) -> float:
    if doc.get("fees_total") is not None:
        return _num(doc.get("fees_total"), 0.0)
    fees = doc.get("fees")
    if isinstance(fees, list):
        return round(sum(_num((f or {}).get("amount"), 0.0) for f in fees), 2)
    return 0.0


def _citation(doc: dict) -> str:
    src = doc.get("source") or (doc.get("instrument") or {}).get("source") or {}
    if not isinstance(src, dict) or not (src.get("system") and src.get("ref")):
        return ""
    as_of = doc.get("trade_date", "")
    return f"{src['system']}:{src['ref']}@{as_of}"


def transform(doc: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    qty = _num(doc.get("quantity"))
    px = _num(doc.get("price"))
    factor = _num(doc.get("price_factor"), 1.0)

    principal = _num(doc.get("principal"))
    if principal is None:
        if qty is None or px is None:
            errors.append("cannot derive principal (need quantity and price)")
            principal = 0.0
        else:
            principal = round(qty * px * factor, 2)

    commission = _num(doc.get("commission"), 0.0)
    fees_total = _fees_total(doc)
    accrued = _num(doc.get("accrued_interest"), 0.0)
    charges_total = round(commission + fees_total, 2)

    side = str(doc.get("side", "")).lower()
    direction = 1 if side == "buy" else -1 if side == "sell" else 0
    if direction == 0:
        errors.append(f"unknown side {doc.get('side')!r}; cannot orient the tie-out")

    expected_net = round(principal + accrued + direction * charges_total, 2)
    reported_net = _num(doc.get("net_amount"))
    if reported_net is None:
        errors.append("confirmation missing net_amount to tie out against")
    elif abs(expected_net - reported_net) > CENTS_TOL:
        errors.append(
            f"net_amount {reported_net} does not tie to principal {principal} "
            f"{'+' if direction >= 0 else '-'} charges {charges_total} "
            f"(+ accrued {accrued}) = expected {expected_net}")

    cite = _citation(doc)
    instr = doc.get("instrument") or {}
    explanation = {
        "explanation_id": f"tce-{doc.get('trade_date','')}-{doc.get('confirmation_id','')}",
        "account_id": doc.get("account_id"),
        "confirmation_id": doc.get("confirmation_id"),
        "trade_date": doc.get("trade_date"),
        "settlement_date": doc.get("settlement_date"),
        "side": side,
        "capacity": str(doc.get("capacity", "")).lower(),
        "currency": doc.get("currency"),
        "instrument": {k: instr.get(k) for k in ("instrument_id", "id_type", "description", "security_type")},
        "quantity": qty,
        "price": px,
        "price_factor": factor,
        "principal": principal,
        "charges": {
            "commission": commission,
            "markup": _num(doc.get("markup"), 0.0),
            "markdown": _num(doc.get("markdown"), 0.0),
            "fees_total": fees_total,
        },
        "accrued_interest": accrued,
        "net_amount": reported_net if reported_net is not None else expected_net,
        "computed_expected_net": expected_net,
        "citations": {"principal": cite, "net_amount": cite, "charges": cite},
        "disclaimer": "Informational explanation only; not investment advice or a recommendation.",
    }
    return explanation, errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "confirmation_example.json"
        doc = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())

    explanation, errors = transform(doc)
    if "--selftest" not in argv:
        print(json.dumps(explanation, indent=2))
    for e in errors:
        print("ERROR", e)
    print(f"computation check: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
