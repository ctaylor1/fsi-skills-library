#!/usr/bin/env python3
"""Deterministic output validation for claim-settlement-authority-packet.

Enforces the R3 guardrails before the request packet is presented:
  1. total_exposure == indemnity + expense (within tolerance).
  2. Every completeness gap carries a citation.
  3. suggested_disposition is review-only (packet-ready | gaps-for-review).
  4. No settlement-approval / authority-grant / payment-authorization language.
  5. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"packet-ready", "gaps-for-review"}
DISCLAIMER_RE = re.compile(r"not a settlement approval", re.I)
PROHIBITED = [
    r"\bsettlement approved\b", r"\bauthority granted\b", r"\bwe approve the settlement\b",
    r"\bapproved to settle\b", r"\bauthoriz(e|ed) the payment\b", r"\bsettle at\b",
    r"\bwe grant authority\b", r"\bpay the claimant\b",
]
TOL = 0.05


def validate(p: dict) -> list[str]:
    errors = []
    exp = p.get("exposure") or {}
    ind, ex, tot = exp.get("indemnity_estimate"), exp.get("expense_estimate"), exp.get("total_exposure")
    if None not in (ind, ex, tot) and abs((ind + ex) - tot) > TOL:
        errors.append(f"total_exposure {tot} != indemnity {ind} + expense {ex}")
    for g in p.get("completeness_gaps") or []:
        if not (g.get("citation") or "").strip():
            errors.append(f"gap {g.get('item','?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"approval/authority-grant/payment language detected: {m.group(0)!r} (R3 requests, approver decides)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (request packet only / no settlement approved)")
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
