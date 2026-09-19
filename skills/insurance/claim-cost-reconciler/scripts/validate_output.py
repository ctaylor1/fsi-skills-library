#!/usr/bin/env python3
"""Deterministic output validation for claim-cost-reconciler.

Enforces the R3 guardrails before the comparison packet is presented:
  1. Every finding carries a non-empty citation.
  2. suggested_disposition is review-only (clean | items-for-review).
  3. No damages / reserve / settlement valuation or payment-approval language.
  4. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from insurance_contract import validate_artifact

ALLOWED = {"clean", "items-for-review", "not-evaluable"}
DISCLAIMER_RE = re.compile(r"not a damages, reserve, or settlement determination", re.I)
PROHIBITED = [
    r"\bset the damages\b",
    r"\bsettlement (value|amount) (is|should be)\b",
    r"\breserve should be\b",
    r"\bwe value the claim\b",
    r"\btotal damages are\b",
    r"\brecommend settling\b",
    r"\bapprov(e|ed) payment\b",
    r"\bpay the claim\b",
]


def _validate(p: dict) -> list[str]:
    errors = []
    expected = "not-evaluable" if p.get("not_evaluable") else "items-for-review" if p.get("findings") else "clean"
    if p.get("suggested_disposition") != expected:
        errors.append("disposition must reflect findings and non-evaluable items")
    if p.get("input_item_count", 0) != p.get("evaluated_item_count", 0) + len(p.get("not_evaluable") or []):
        errors.append("item coverage counts do not reconcile")
    for f in p.get("findings") or []:
        if not (f.get("citation") or "").strip():
            errors.append(f"finding {f.get('type', '?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = " ".join(str(p.get(k, "")) for k in ("narrative", "notes", "conclusion", "decision", "action"))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(
                f"valuation/settlement/payment language detected: {m.group(0)!r} (R3 evidences, adjuster decides)"
            )
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (comparison evidence only / no amount set or approved)")
    return errors


def validate(doc: dict, *args, **kwargs) -> list[str]:
    if not isinstance(doc, dict):
        return ["output must be an object"]
    try:
        errors = _validate(doc, *args, **kwargs)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        errors = ["malformed output: " + str(exc)]
    return errors + validate_artifact(doc.get("artifact"), output=doc)


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
