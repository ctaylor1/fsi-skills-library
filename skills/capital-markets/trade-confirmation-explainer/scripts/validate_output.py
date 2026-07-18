#!/usr/bin/env python3
"""Deterministic output validation for trade-confirmation-explainer.

Confirms the explanation is internally consistent, complete against the key Rule 10b-10
disclosures, fully cited, and free of advice/recommendation/opinion language BEFORE it is
presented or delivered. R1 is informational only: any advice phrasing fails closed.

Checks:
  1. Completeness — the required disclosure fields are present and non-empty.
  2. Principal tie-out — principal == quantity * price * price_factor (+/- cents).
  3. Net-amount tie-out — net_amount == principal + accrued + direction*charges_total.
  4. Citation coverage — principal and net_amount carry non-empty citations.
  5. No-advice screen — narrative/notes contain no advice, recommendation, or value
     judgment about the trade, price, broker, or charges.
  6. Standing disclaimer present.

Explanation schema: see scripts/calculate_or_transform.py.

Usage:
  python validate_output.py explanation.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

CENTS_TOL = 0.01
REQUIRED = ("trade_date", "settlement_date", "side", "capacity", "quantity", "price",
            "principal", "net_amount")

ADVICE_PATTERNS = [
    r"\brecommend(s|ed|ing)?\b", r"\bwe (suggest|advise|recommend)\b",
    r"\byou (should|ought to|might want to|could)\b",
    r"\bshould (buy|sell|hold|consider|switch|keep|reduce|increase|have)\b",
    r"\b(buy|sell) (this|these|more|now|back|again)\b",
    r"\b(good|bad|great|poor|fair|unfair|reasonable|excessive|attractive) (trade|price|deal|investment|execution|choice|option)\b",
    r"\btoo (high|low|expensive|much|cheap|risky)\b",
    r"\b(over|under)-?paid\b", r"\bover-?charged\b",
    r"\bbetter (price|deal|option|choice|broker|rate)\b",
    r"\b(switch|change) (brokers?|firms?|advis(?:e|o)rs?)\b",
    r"\b(dispute|challenge|contest) (the|this) (trade|confirmation|charge|commission|price)\b",
    r"\b(was|is) (a )?(good|bad|smart|poor|wise|risky|safe) (idea|move|decision|trade|buy|sell)\b",
    r"\byou (made|lost) money\b",
]
DISCLAIMER_RE = re.compile(
    r"informational (explanation |summary )?only.*(not (investment )?advice|not a recommendation)", re.I)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _close(a, b, tol=CENTS_TOL):
    return a is not None and b is not None and abs(a - b) <= tol


def validate(s: dict) -> list[str]:
    errors: list[str] = []

    for k in REQUIRED:
        if s.get(k) in (None, ""):
            errors.append(f"missing required disclosure field '{k}'")

    qty = _num(s.get("quantity"))
    px = _num(s.get("price"))
    factor = _num(s.get("price_factor"))
    if factor is None:
        factor = 1.0
    principal = _num(s.get("principal"))
    if qty is not None and px is not None and principal is not None:
        derived = round(qty * px * factor, 2)
        if not _close(principal, derived, max(0.01, abs(derived) * 0.005)):
            errors.append(f"principal {principal} != quantity*price*price_factor {derived:.2f}")

    charges = s.get("charges") or {}
    commission = _num(charges.get("commission")) or 0.0
    fees_total = _num(charges.get("fees_total")) or 0.0
    accrued = _num(s.get("accrued_interest")) or 0.0
    charges_total = round(commission + fees_total, 2)
    side = str(s.get("side", "")).lower()
    direction = 1 if side == "buy" else -1 if side == "sell" else 0
    net = _num(s.get("net_amount"))
    if direction == 0:
        errors.append(f"unknown side {s.get('side')!r}; cannot verify net-amount tie-out")
    elif principal is not None and net is not None:
        expected = round(principal + accrued + direction * charges_total, 2)
        if not _close(net, expected):
            errors.append(
                f"net_amount {net} != principal {principal} {'+' if direction >= 0 else '-'} "
                f"charges {charges_total} (+ accrued {accrued}) = {expected}")

    citations = s.get("citations") or {}
    for field in ("principal", "net_amount"):
        if not str(citations.get(field, "")).strip():
            errors.append(f"missing citation for '{field}'")

    text = " ".join(str(s.get(k, "")) for k in ("narrative", "notes"))
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(
                f"advice/recommendation/judgment language detected: {m.group(0)!r} "
                f"(R1 is informational only)")
    if not DISCLAIMER_RE.search(str(s.get("narrative", "")) + " " + str(s.get("disclaimer", ""))):
        errors.append(
            "missing standing disclaimer: "
            "'Informational explanation only; not investment advice or a recommendation.'")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "explanation_example.json"
        s = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        s = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        s = json.loads(sys.stdin.read())
    errors = validate(s)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
