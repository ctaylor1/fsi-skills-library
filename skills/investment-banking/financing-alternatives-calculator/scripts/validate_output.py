#!/usr/bin/env python3
"""Deterministic output validation for financing-alternatives-calculator.

Enforces the R2 guardrails before the worksheet is presented:
  1. Per debt row: total_cost_over_term == annual_interest*term + upfront_fees (within tolerance).
  2. No recommendation / ranking language.
  3. Standing disclaimer present.

Usage: python validate_output.py worksheet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_RE = re.compile(r"not a recommendation", re.I)
PROHIBITED = [
    r"\bwe recommend\b", r"\bcheapest option\b", r"\bbest option\b", r"\bshould choose\b",
    r"\boptimal financing\b", r"\bgo with the\b", r"\bis the winner\b", r"\bwe suggest .{0,15}(loan|bond|equity)",
]
TOL = 0.5


def validate(p: dict) -> list[str]:
    errors = []
    for r in p.get("alternatives") or []:
        if r.get("type") == "equity":
            continue
        terms = r.get("terms_used") or {}
        term = terms.get("term_years")
        ai, uf, tot = r.get("annual_interest"), r.get("upfront_fees"), r.get("total_cost_over_term")
        if None in (ai, uf, tot, term):
            continue
        expected = ai * float(term) + uf
        if abs(expected - tot) > TOL:
            errors.append(f"{r.get('alt_id')}: total_cost_over_term {tot} != interest*term+fees {round(expected, 2)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"recommendation/ranking language detected: {m.group(0)!r} (R2 computes, banker advises)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (illustrative comparison only / not a recommendation)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "worksheet_example.json"
        p = json.loads(pth.read_text(encoding="utf-8"))
    elif argv:
        p = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        p = json.loads(sys.stdin.read())
    errors = validate(p)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
