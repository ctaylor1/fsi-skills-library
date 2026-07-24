#!/usr/bin/env python3
"""Deterministic output validation for desk-pnl-risk-attribution-pack.

Enforces the R3 guardrails before the attribution packet is presented:
  1. explained + residual == reported_pnl (within tolerance).
  2. suggested_disposition is review-only (tied | breaks-for-review).
  3. No P&L adjustment / sign-off / certification language.
  4. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"tied", "breaks-for-review"}
DISCLAIMER_RE = re.compile(r"not a P&L adjustment", re.I)
PROHIBITED = [
    r"\badjusted the p&l\b", r"\brestated the p&l\b", r"\bwe signed off\b", r"\bbooked the adjustment\b",
    r"\battest(ed)? the p&l\b", r"\bcertif(y|ied) the p&l\b", r"\bapprov(e|ed) the p&l\b",
    r"\bsign off the p&l\b",
]
TOL = 0.05


def validate(p: dict) -> list[str]:
    errors = []
    rep, exp, res = p.get("reported_pnl"), p.get("explained"), p.get("residual")
    if None not in (rep, exp, res) and abs((exp + res) - rep) > TOL:
        errors.append(f"explained {exp} + residual {res} != reported_pnl {rep}")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"P&L adjustment/sign-off language detected: {m.group(0)!r} (R3 evidences, product control adjusts/signs off)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (attribution evidence only / no P&L adjusted or certified)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "packet_example.json"
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
