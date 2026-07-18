#!/usr/bin/env python3
"""Deterministic entitlement computation for corporate-action-interpreter.

Given a validated corporate-action NOTICE and an eligible position, compute the
entitlement for each outcome (one outcome for a mandatory event; one per option for a
voluntary / mandatory-with-options event). This is descriptive arithmetic on the stated
terms only — it does NOT choose an option, decide participation, or compute tax. Whole
vs. fractional shares are reported separately so cash-in-lieu is never silently invented.

Entitlement bases:
  shares_after      = quantity * ratio_new / ratio_old   (SPLF, SPLR)
  additional_shares = quantity * ratio_new / ratio_old   (DVSE, BONU)
  shares            = quantity * ratio_new / ratio_old    (stock option of DVOP/EXOF)
  cash              = quantity * rate_per_share           (DVCA, CAPG, cash option)

Usage:
  python calculate_or_transform.py notice.json     # print computed entitlements (JSON)
  python calculate_or_transform.py --selftest       # recompute the bundled fixture and check
Exit 0 if computation is internally consistent, 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

RATIO_EVENT_BASIS = {"SPLF": "shares_after", "SPLR": "shares_after",
                     "DVSE": "additional_shares", "BONU": "additional_shares"}
RATE_EVENT_BASIS = {"DVCA": "cash", "CAPG": "cash", "INTR": "cash", "REDM": "cash"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _shares(qty, rn, ro):
    if qty is None or rn is None or not ro:
        return None
    return qty * rn / ro


def _split_whole_frac(val):
    whole = int(val // 1)
    frac = round(val - whole, 10)
    return whole, frac


def _option_entitlement(opt, qty):
    """Return an entitlement dict for one option, or None if terms are insufficient."""
    rate = _num(opt.get("rate_per_share"))
    rn, ro = _num(opt.get("ratio_new")), _num(opt.get("ratio_old"))
    if rate is not None:
        return {"basis": "cash", "unit": "currency", "value": round(qty * rate, 2)}
    val = _shares(qty, rn, ro)
    if val is not None:
        whole, frac = _split_whole_frac(val)
        ent = {"basis": "shares", "unit": "shares", "value": round(val, 6),
               "whole_shares": whole, "fractional": frac}
        if frac > 0:
            ent["fractional_handling"] = opt.get("fractional_handling") or "cash-in-lieu (rate not stated in notice; confirm with agent)"
        return ent
    return None


def compute(notice: dict) -> dict:
    ev = notice.get("event_type")
    terms = notice.get("terms") or {}
    qty = _num((notice.get("eligible_position") or {}).get("quantity"))
    out = {
        "event_id": notice.get("event_id"),
        "event_type": ev,
        "eligible_quantity": qty,
        "entitlements": [],
        "options": [],
        "notes": [],
    }
    if qty is None:
        out["notes"].append("no eligible_position.quantity — entitlements not computed")
        return out

    options = notice.get("options") or []
    if options:
        for opt in options:
            ent = _option_entitlement(opt, qty)
            entry = {"option_id": opt.get("option_id"), "option_code": opt.get("option_code"),
                     "default": bool(opt.get("default")), "entitlement": ent}
            if ent is None:
                out["notes"].append(f"option {opt.get('option_id')}: terms insufficient to compute")
            out["options"].append(entry)
        return out

    rn, ro = _num(terms.get("ratio_new")), _num(terms.get("ratio_old"))
    rate = _num(terms.get("rate_per_share"))
    if ev in RATIO_EVENT_BASIS:
        val = _shares(qty, rn, ro)
        if val is not None:
            whole, frac = _split_whole_frac(val)
            ent = {"basis": RATIO_EVENT_BASIS[ev], "unit": "shares", "value": round(val, 6),
                   "whole_shares": whole, "fractional": frac}
            if frac > 0:
                ent["fractional_handling"] = terms.get("fractional_handling") or "cash-in-lieu (confirm with agent)"
            out["entitlements"].append(ent)
        else:
            out["notes"].append(f"{ev}: terms lack ratio_new/ratio_old — not computed")
    elif ev in RATE_EVENT_BASIS:
        if rate is not None:
            out["entitlements"].append({"basis": "cash", "unit": "currency", "value": round(qty * rate, 2)})
        else:
            out["notes"].append(f"{ev}: terms lack rate_per_share — not computed")
    else:
        out["notes"].append(f"{ev}: no deterministic entitlement formula — interpret narratively and flag for review")
    return out


def _selftest() -> int:
    fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "notice_example.json"
    notice = json.loads(fixture.read_text(encoding="utf-8"))
    result = compute(notice)
    errors: list[str] = []
    by_id = {o["option_id"]: o for o in result["options"]}
    # Expected: CASH option 001 -> 500 * 0.24 = 120.00; STOCK option 002 -> 500 * 1/40 = 12.5.
    cash = by_id.get("001", {}).get("entitlement") or {}
    if cash.get("value") != 120.00:
        errors.append(f"option 001 cash value {cash.get('value')} != 120.00")
    stock = by_id.get("002", {}).get("entitlement") or {}
    if stock.get("value") != 12.5:
        errors.append(f"option 002 shares value {stock.get('value')} != 12.5")
    if stock.get("whole_shares") != 12 or stock.get("fractional") != 0.5:
        errors.append(f"option 002 whole/frac {stock.get('whole_shares')}/{stock.get('fractional')} != 12/0.5")
    for e in errors:
        print("ERROR", e)
    print(f"corporate-action transform self-test: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    if argv:
        notice = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        notice = json.loads(sys.stdin.read())
    print(json.dumps(compute(notice), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
