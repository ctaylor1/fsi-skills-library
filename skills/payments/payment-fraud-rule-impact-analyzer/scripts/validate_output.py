#!/usr/bin/env python3
"""Deterministic output validation for payment-fraud-rule-impact-analyzer.

Enforces the R3 guardrails before the impact estimate is presented:
  1. Confusion cells sum to labeled_size, for both current and proposed.
  2. blocked_now/blocked_proposed within [0, sample_size].
  3. No rule-deployment / live block-allow-decision language.
  4. Standing disclaimer present.

Usage: python validate_output.py estimate.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_RE = re.compile(r"not a rule deployment", re.I)
PROHIBITED = [
    r"\bdeployed the rule\b", r"\brolled out( the rule)?\b", r"\benabl(e|ed) .{0,20}in production\b",
    r"\bwe blocked\b", r"\bblock this customer\b", r"\bdeny the transaction\b",
    r"\bturn(ed)? on the rule\b", r"\bship(ped)? the rule\b",
]


def _sum_conf(c):
    return sum(int(c.get(k, 0)) for k in ("caught_fraud", "missed_fraud", "false_positives", "true_allows"))


def validate(p: dict) -> list[str]:
    errors = []
    labeled = p.get("labeled_size")
    for key in ("confusion_now", "confusion_proposed"):
        c = p.get(key)
        if isinstance(c, dict) and labeled is not None and _sum_conf(c) != labeled:
            errors.append(f"{key} cells sum to {_sum_conf(c)} != labeled_size {labeled}")
    n = p.get("sample_size")
    for key in ("blocked_now", "blocked_proposed"):
        v = p.get(key)
        if v is not None and n is not None and not (0 <= v <= n):
            errors.append(f"{key} {v} out of range [0, {n}]")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"deployment/live-decision language detected: {m.group(0)!r} (R3 estimates, human deploys/decides)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (sample estimate only / not a deployment or decision)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "estimate_example.json"
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
