#!/usr/bin/env python3
"""Deterministic output validation for market-window-readiness-pack.

Enforces the R2 guardrails before the readiness packet is presented:
  1. Every gap carries a non-empty citation.
  2. suggested_disposition is review-only (ready-for-review | gaps-for-review).
  3. No launch-decision / pricing-clearance / market-timing language.
  4. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"ready-for-review", "gaps-for-review"}
DISCLAIMER_RE = re.compile(r"not a launch decision", re.I)
PROHIBITED = [
    r"\bcleared to launch\b", r"\bapproved the launch\b", r"\blaunch now\b", r"\bwindow is open\b",
    r"\btime the market\b", r"\bshould price now\b", r"\bgo to market now\b", r"\bprice the deal now\b",
]


def validate(p: dict) -> list[str]:
    errors = []
    for g in p.get("gaps") or []:
        if not (g.get("citation") or "").strip():
            errors.append(f"gap {g.get('item_id','?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"launch/timing language detected: {m.group(0)!r} (R2 evidences readiness, does not decide launch or advise timing)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (readiness evidence only / not a launch decision)")
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
