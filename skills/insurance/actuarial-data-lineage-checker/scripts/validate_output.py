#!/usr/bin/env python3
"""Deterministic output validation for actuarial-data-lineage-checker.

  1. Every break carries a citation.
  2. suggested_disposition is review-only (clean | breaks-for-review).
  3. No data-alteration / assumption-selection / reserve-certification language.
  4. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"clean", "breaks-for-review"}
PROHIBITED = [
    r"\bcorrected the (data|records?)\b", r"\badjusted the source\b", r"\bfixed the (data|value)\b",
    r"\bset the assumption\b", r"\bselected the (method|assumption)\b",
    r"\bcertif(y|ied) the reserve\b", r"\breserve data (is|has been) certified\b",
    r"\bwe (altered|overwrote|updated the source)\b",
]
DISCLAIMER_RE = re.compile(r"no source data has been altered", re.I)


def validate(p: dict) -> list[str]:
    errors = []
    for b in p.get("breaks") or []:
        if not (b.get("citation") or "").strip():
            errors.append(f"break {b.get('type','?')}/{b.get('key','?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"data-alteration/assumption/certification language detected: {m.group(0)!r} (R2 reconciles, does not alter/certify)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (no source data altered / no reserve certified)")
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
