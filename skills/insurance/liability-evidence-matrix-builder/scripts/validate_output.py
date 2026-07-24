#!/usr/bin/env python3
"""Deterministic output validation for liability-evidence-matrix-builder.

Enforces the R3 guardrails before the matrix is presented:
  1. Every supporting/contradicting cell carries an evidence citation.
  2. suggested_disposition is review-only (matrix-complete | gaps-for-review).
  3. No liability / fault / negligence language.
  4. Standing disclaimer present.

Usage: python validate_output.py matrix.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"matrix-complete", "gaps-for-review"}
DISCLAIMER_RE = re.compile(r"not a liability, fault, or negligence determination", re.I)
PROHIBITED = [
    r"\bis liable\b", r"\bat fault\b", r"\bwe find fault\b", r"\bliability rests\b",
    r"\bassign(ed)? liability\b", r"\bis negligent\b", r"\bbreached the duty\b", r"\bfault lies with\b",
]


def validate(p: dict) -> list[str]:
    errors = []
    for row in p.get("matrix") or []:
        for cell in (row.get("supporting") or []) + (row.get("contradicting") or []):
            if not (cell.get("citation") or "").strip():
                errors.append(f"fact {row.get('fact_id','?')}: evidence cell missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"liability/fault language detected: {m.group(0)!r} (R3 maps evidence, adjuster determines liability)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (evidence mapping only / no liability determined)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "matrix_example.json"
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
