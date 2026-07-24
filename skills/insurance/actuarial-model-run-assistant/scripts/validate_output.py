#!/usr/bin/env python3
"""Deterministic output validation for actuarial-model-run-assistant.

Enforces the R2 guardrails before the run packet is presented:
  1. Per-origin ultimate == latest + ibnr (within tolerance) for computable rows.
  2. total_ultimate == Σ ultimate and total_ibnr == Σ ibnr (within tolerance).
  3. No reserve-setting / booking / adequacy-certification language.
  4. Standing disclaimer present.

Usage: python validate_output.py run.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.05
DISCLAIMER_RE = re.compile(r"not a booked reserve", re.I)
PROHIBITED = [
    r"\b(set|book(ed)?) the reserve\b", r"\breserve is (set|booked|adequate|sufficient)\b",
    r"\bcarried reserve\b", r"\breserv(e|ing) decision\b", r"\bcertif(y|ied)\b.{0,30}adequa",
    r"\bwe (have )?(set|booked) a reserve\b",
]


def validate(p: dict) -> list[str]:
    errors = []
    su = si = 0.0
    for o in p.get("per_origin") or []:
        u, latest, ibnr = o.get("ultimate"), o.get("latest"), o.get("ibnr")
        if u is None or ibnr is None:
            continue
        if latest is not None and abs(u - (latest + ibnr)) > TOL:
            errors.append(f"origin {o.get('origin')}: ultimate {u} != latest {latest} + ibnr {ibnr}")
        su += u
        si += ibnr
    if p.get("total_ultimate") is not None and abs(su - p["total_ultimate"]) > max(TOL, abs(su) * 1e-6):
        errors.append(f"total_ultimate {p['total_ultimate']} != sum(ultimate) {round(su, 2)}")
    if p.get("total_ibnr") is not None and abs(si - p["total_ibnr"]) > max(TOL, abs(si) * 1e-6):
        errors.append(f"total_ibnr {p['total_ibnr']} != sum(ibnr) {round(si, 2)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"reserve-setting/adequacy language detected: {m.group(0)!r} (R2 indicates, actuary books)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (indication for review only / not a booked reserve)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
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
