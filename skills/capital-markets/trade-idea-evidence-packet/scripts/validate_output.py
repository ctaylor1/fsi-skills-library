#!/usr/bin/env python3
"""Deterministic output validation for trade-idea-evidence-packet.

Enforces the R3 guardrails before the packet is presented:
  1. Every cited evidence point and every gap/flag carries a citation.
  2. suggested_disposition is review-only (packet-ready | gaps-for-review).
  3. A restricted (hard-stop) flag must NOT coexist with packet-ready.
  4. No specific-client-recommendation / suitability-determination language.
  5. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"packet-ready", "gaps-for-review"}
DISCLAIMER_RE = re.compile(r"not a recommendation to any specific client", re.I)
PROHIBITED = [
    r"\brecommend to (the )?client\b", r"\bsuitable for (the )?client\b", r"\bwe recommend buying\b",
    r"\byou should buy\b", r"\bis suitable for\b", r"\badvise the client to\b", r"\btailored recommendation\b",
    r"\bwe recommend (the )?client\b",
]


def validate(p: dict) -> list[str]:
    errors = []
    for e in p.get("evidence") or []:
        if not (e.get("citation") or "").strip():
            errors.append(f"evidence point {e.get('point_id','?')}: uncited (not valid evidence)")
    for g in p.get("gaps") or []:
        if not (g.get("citation") or "").strip():
            errors.append(f"gap {g.get('check','?')}: missing citation")
    restricted = False
    for f in p.get("suitability_flags") or []:
        if not (f.get("citation") or "").strip():
            errors.append(f"flag {f.get('check','?')}: missing citation")
        if f.get("check") == "restricted_product":
            restricted = True
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    if restricted and p.get("suggested_disposition") == "packet-ready":
        errors.append("restricted-product flag present but disposition is packet-ready (restricted is a hard stop)")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"client-recommendation/suitability language detected: {m.group(0)!r} (R3 packages evidence, human/compliance recommends/decides suitability)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (internal evidence only / not a client recommendation)")
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
