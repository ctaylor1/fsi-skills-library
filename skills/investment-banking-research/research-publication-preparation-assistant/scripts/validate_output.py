#!/usr/bin/env python3
"""Deterministic output validation for research-publication-preparation-assistant.

Enforces the R3 guardrails before the pre-publication packet is presented:
  1. Every gap and flag carries a citation.
  2. suggested_disposition is review-only (ready-for-compliance-review | gaps-for-review).
  3. A restricted-list flag must NOT coexist with ready-for-compliance-review.
  4. No publish / approval / rating-determination language.
  5. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"ready-for-compliance-review", "gaps-for-review"}
DISCLAIMER_RE = re.compile(r"not a publication", re.I)
PROHIBITED = [
    r"\bwe publish\b", r"\bpublish the note\b", r"\bnote is approved\b", r"\bcleared for publication\b",
    r"\bwe rate it\b", r"\bthe rating is set\b", r"\bapproved for distribution\b", r"\bdistribute the note\b",
]


def validate(p: dict) -> list[str]:
    errors = []
    for g in p.get("gaps") or []:
        if not (g.get("citation") or "").strip():
            errors.append(f"gap {g.get('check','?')}: missing citation")
    restricted = False
    for f in p.get("flags") or []:
        if not (f.get("citation") or "").strip():
            errors.append(f"flag {f.get('check','?')}: missing citation")
        if f.get("check") == "restricted_list":
            restricted = True
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    if restricted and p.get("suggested_disposition") == "ready-for-compliance-review":
        errors.append("restricted-list flag present but disposition is ready-for-compliance-review (restricted is a hard stop)")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"publish/approval/rating language detected: {m.group(0)!r} (R3 checks, human publishes/approves/rates)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (pre-publication prep only / nothing published)")
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
