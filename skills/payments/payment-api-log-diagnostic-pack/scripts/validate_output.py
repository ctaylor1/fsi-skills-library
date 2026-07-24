#!/usr/bin/env python3
"""Deterministic output validation for payment-api-log-diagnostic-pack.

Enforces the R2 + PCI guardrails before the diagnostic pack is presented:
  1. PAN-leakage screen — no 13–19 digit sequence anywhere in the output.
  2. Every classified entry has a category.
  3. No remediation / config-change language.
  4. Standing disclaimer present.

Usage: python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

PAN_RE = re.compile(r"\b\d{13,19}\b")
DISCLAIMER_RE = re.compile(r"no configuration has been changed", re.I)
PROHIBITED = [
    r"\bchanged the config\b", r"\bdeployed the fix\b", r"\bdisabled the rule\b",
    r"\brotated the key\b", r"\bwe fixed\b", r"\bapplied the patch\b", r"\bremediat(e|ed)\b",
]


def validate(p: dict) -> list[str]:
    errors = []
    blob = json.dumps(p)
    leak = PAN_RE.search(blob)
    if leak:
        errors.append(f"PAN-leakage screen failed: unredacted 13-19 digit sequence in output ({leak.group(0)[:4]}…)")
    for e in p.get("classified_entries") or []:
        if not (e.get("category") or "").strip():
            errors.append(f"entry {e.get('request_id','?')}: missing category")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"remediation/config-change language detected: {m.group(0)!r} (R2 investigates, does not remediate)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (diagnostic only / no configuration changed)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
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
