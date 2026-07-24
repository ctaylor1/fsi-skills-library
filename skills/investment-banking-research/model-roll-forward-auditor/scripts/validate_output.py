#!/usr/bin/env python3
"""Deterministic output validation for model-roll-forward-auditor.

Enforces the R2 guardrails before the audit is presented:
  1. Per numeric item: residual == current_opening - prior_ending (within tolerance).
  2. suggested_disposition is review-only (tied | breaks-for-review).
  3. No valuation / model-approval / correctness-confirmation language.
  4. Standing disclaimer present.

Usage: python validate_output.py audit.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"tied", "breaks-for-review"}
DISCLAIMER_RE = re.compile(r"not a model approval", re.I)
PROHIBITED = [
    r"\bmodel is approved\b", r"\bwe approve the model\b", r"\bfair value is\b", r"\bvaluation is\b",
    r"\bthe model is correct\b", r"\bsign off on the model\b", r"\bmodel is validated\b",
    r"\bwe validate the model\b",
]
EPS = 1e-6


def validate(p: dict) -> list[str]:
    errors = []
    for it in p.get("line_items") or []:
        pe, co, res = it.get("prior_ending"), it.get("current_opening"), it.get("residual")
        if None in (pe, co, res):
            continue
        if abs((co - pe) - res) > EPS:
            errors.append(f"{it.get('line_item')}: residual {res} != current_opening {co} - prior_ending {pe}")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"valuation/model-approval language detected: {m.group(0)!r} (R2 checks continuity, deal team approves/values)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (continuity check only / no model approved or valued)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "audit_example.json"
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
