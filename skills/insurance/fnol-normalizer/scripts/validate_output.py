#!/usr/bin/env python3
"""Deterministic output validation for fnol-normalizer.

Enforces the R3 guardrails before the normalized record is presented:
  1. Every exception carries a non-empty citation.
  2. suggested_disposition is review-only (normalized | exceptions-for-review).
  3. No coverage / liability / reserve / claim-adjudication language.
  4. Standing disclaimer present.

Usage: python validate_output.py record.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"normalized", "exceptions-for-review"}
DISCLAIMER_RE = re.compile(r"not a coverage, liability, or reserve determination", re.I)
PROHIBITED = [
    r"\bcoverage (is|applies|does not apply)\b", r"\bcovered under\b", r"\bdeny coverage\b",
    r"\bassign(ed)? liability\b", r"\bat fault\b", r"\bset the reserve\b", r"\breserve is\b",
    r"\bopen(ed)? the claim\b", r"\brout(e|ed) the claim\b",
]


def validate(p: dict) -> list[str]:
    errors = []
    for e in p.get("exceptions") or []:
        if not (e.get("citation") or "").strip():
            errors.append(f"exception {e.get('field','?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"coverage/liability/reserve language detected: {m.group(0)!r} (R3 normalizes, human adjudicates)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (normalization only / no claim opened or adjudicated)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "record_example.json"
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
