#!/usr/bin/env python3
"""Deterministic output validation for transaction-cost-estimator.

  1. Component bps sum to total_bps (within tolerance); total_ccy ties to total_bps x notional.
  2. methodology_version present; market-impact uncertainty range present.
  3. No execution / venue / broker / algo advice or best-execution assertion.
  4. Standing disclaimer present.

Usage: python validate_output.py tca.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL_BPS = 0.01
ADVICE_PATTERNS = [
    r"\b(route|execute|cancel|amend) (the )?order\b", r"\bwe (routed|executed|cancelled|amended)\b",
    r"\b(use|recommend|select|prefer) (venue|broker|algo|the dark pool)\b",
    r"\bbest execution (was|is) (achieved|met|optimal)\b", r"\bwas best ex\b",
    r"\bshould (route|execute|use) \b",
]
DISCLAIMER_RE = re.compile(r"not execution.*advice.*no order has been (routed|routed, executed)", re.I)


def validate(p: dict) -> list[str]:
    errors = []
    comp = p.get("components") or {}
    total = p.get("total_bps")
    if total is None or not comp:
        return ["output missing components or total_bps"]
    csum = round(sum((c.get("bps") or 0.0) for c in comp.values()), 4)
    if abs(csum - total) > TOL_BPS:
        errors.append(f"component bps sum {csum} != total_bps {total}")
    notional = p.get("notional")
    if notional is not None and p.get("total_ccy") is not None:
        expected_ccy = round(total / 10000.0 * notional, 2)
        if abs(expected_ccy - p["total_ccy"]) > max(0.01, abs(expected_ccy) * 0.001):
            errors.append(f"total_ccy {p['total_ccy']} != total_bps/10000*notional {expected_ccy}")
    if not p.get("methodology_version"):
        errors.append("missing methodology_version")
    if not p.get("total_bps_range"):
        errors.append("missing market-impact uncertainty range (total_bps_range)")

    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"execution/venue/best-ex advice language detected: {m.group(0)!r} (R2 estimates, does not act/advise)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (estimate-only / no order routed or executed)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "tca_example.json"
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
