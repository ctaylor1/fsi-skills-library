#!/usr/bin/env python3
"""Deterministic output validation for financial-document-version-comparator.

  1. Every change carries a section location + citation.
  2. suggested_disposition is review-only (clean | changes-for-review).
  3. No legal-significance / materiality / approval / disclosure-sufficiency language.
  4. Standing disclaimer present.

Usage: python validate_output.py changelog.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"clean", "changes-for-review"}
PROHIBITED = [
    r"\bis (a )?material\b", r"\bnot material\b", r"\bmaterially\b", r"\blegally significant\b",
    r"\b(we )?approv(e|ed) the document\b", r"\bdisclosure is (adequate|sufficient|insufficient)\b",
    r"\bpublish(ed)? the (document|version|research)\b", r"\bis disclosure-sufficient\b",
]
DISCLAIMER_RE = re.compile(r"not a judgment of legal significance", re.I)


def validate(p: dict) -> list[str]:
    errors = []
    for c in p.get("changes") or []:
        if not c.get("section_id"):
            errors.append(f"change {c.get('type','?')}: missing section_id location")
        if not (c.get("citation") or "").strip():
            errors.append(f"change {c.get('type','?')}/{c.get('section_id','?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"significance/approval/disclosure-sufficiency language detected: {m.group(0)!r} (R2 locates changes, does not judge/approve)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (change-location only / no significance judgment)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "changelog_example.json"
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
