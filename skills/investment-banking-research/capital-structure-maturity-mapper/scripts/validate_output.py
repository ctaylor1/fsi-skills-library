#!/usr/bin/env python3
"""Deterministic output validation for capital-structure-maturity-mapper.

Enforces the R2 guardrails before the map is presented:
  1. Σ by_seniority == total_debt and Σ maturity_wall == total_debt (within tolerance).
  2. secured_unsecured sums to total_debt.
  3. No financing-advice / recommendation language.
  4. Standing disclaimer present.

Usage: python validate_output.py map.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_RE = re.compile(r"not financing advice", re.I)
PROHIBITED = [
    r"\bwe recommend\b", r"\bshould refinance\b", r"\bshould issue\b", r"\bshould raise\b",
    r"\boptimal capital structure\b", r"\badvise .{0,20}to issue\b", r"\bwe suggest .{0,20}(refinanc|issu)",
    r"\bbest structure\b",
]
TOL = 0.05


def _sum(d):
    return round(sum(float(v) for v in (d or {}).values()), 2)


def validate(p: dict) -> list[str]:
    errors = []
    total = p.get("total_debt")
    if total is not None:
        for key in ("by_seniority", "maturity_wall", "secured_unsecured"):
            s = _sum(p.get(key))
            if abs(s - total) > max(TOL, abs(total) * 1e-6):
                errors.append(f"sum({key}) {s} != total_debt {total}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"advice/recommendation language detected: {m.group(0)!r} (R2 describes, banker advises)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (descriptive map only / not financing advice)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "map_example.json"
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
