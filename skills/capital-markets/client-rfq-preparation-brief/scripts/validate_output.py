#!/usr/bin/env python3
"""Deterministic output validation for client-rfq-preparation-brief.

Enforces the R3 guardrails before the brief is presented:
  1. Every suitability flag and completeness gap carries a citation.
  2. suggested_disposition is review-only (ready-for-review | review-required).
  3. No pricing / quote / commitment / execution language.
  4. Standing disclaimer present.

Usage: python validate_output.py brief.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"ready-for-review", "review-required"}
DISCLAIMER_RE = re.compile(r"not a quote, a price", re.I)
PROHIBITED = [
    r"\bwe quote\b", r"\bthe price is\b", r"\bfirm bid\b", r"\bfirm offer\b", r"\bwe commit\b",
    r"\bexecuted the trade\b", r"\bfilled at\b", r"\bprice it at\b", r"\bwe can do it at\b",
    r"\bwe(?:'ll| will) show\b.{0,10}\bat\b",
]


def validate(p: dict) -> list[str]:
    errors = []
    for f in p.get("suitability_flags") or []:
        if not (f.get("citation") or "").strip():
            errors.append(f"flag {f.get('flag','?')}: missing citation")
    for g in p.get("completeness_gaps") or []:
        if not (g.get("citation") or "").strip():
            errors.append(f"gap {g.get('section','?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"pricing/commitment language detected: {m.group(0)!r} (R3 prepares context, does not price/commit)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (preparation brief only / not a quote or commitment)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "brief_example.json"
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
