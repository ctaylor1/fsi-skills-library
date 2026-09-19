#!/usr/bin/env python3
"""Deterministic output validation for insurance-data-reconciler.

  1. Every break carries a citation.
  2. suggested_disposition is review-only (clean | breaks-for-review).
  3. No data-alteration / assumption-selection / reserve-certification language.
  4. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from collections import Counter
from insurance_contract import amount, validate_artifact, stable_hash

ALLOWED = {"clean", "breaks-for-review", "partial-not-evaluable"}
PROHIBITED = [
    r"\bcorrected the (data|records?)\b", r"\badjusted the source\b", r"\bfixed the (data|value)\b",
    r"\bset the assumption\b", r"\bselected the (method|assumption)\b",
    r"\bcertif(y|ied) the reserve\b", r"\breserve data (is|has been) certified\b",
    r"\bwe (altered|overwrote|updated the source)\b",
]
DISCLAIMER_RE = re.compile(r"no source data has been altered", re.I)


def validate(p: dict, input_doc=None) -> list[str]:
    if not isinstance(p, dict):
        return ["output must be an object"]
    errors = validate_artifact(p.get("artifact"), input_doc=input_doc, output=p)
    if not isinstance(p.get("breaks"), list) or not all(isinstance(b, dict) for b in p["breaks"]):
        return errors + ["breaks must be a list of objects"]
    if p.get("break_counts") != dict(Counter(b.get("type") for b in p["breaks"])):
        errors.append("break_counts do not reconcile")
    if p.get("suggested_disposition") == "clean":
        if p["breaks"] or p.get("completeness") != "complete" or p.get("evaluability") != "evaluable" or any(v != "evaluable" for v in (p.get("checks") or {}).values()):
            errors.append("clean cannot describe missing, non-evaluable or broken data")
    if input_doc is not None:
        from calculate_or_transform import compute
        try:
            if stable_hash(compute(input_doc)) != stable_hash(p):
                errors.append("output differs from recomputed reconciliation")
        except (TypeError, ValueError) as exc:
            errors.append(f"input cannot be recomputed: {exc}")
    for b in p.get("breaks") or []:
        if not (b.get("citation") or "").strip():
            errors.append(f"break {b.get('type','?')}/{b.get('key','?')}: missing citation")
        if b.get("type") in {"duplicate", "duplicate_prior"}:
            observations = b.get("observations")
            if not isinstance(observations, list) or len(observations) < 2 or not all(isinstance(item, dict) for item in observations):
                errors.append("duplicate finding requires evidence for every conflicting observation")
                continue
            expected_side = "current" if b["type"] == "duplicate" else "prior"
            refs = []
            for item in observations:
                if item.get("side") != expected_side or not item.get("source_ref") or not isinstance(item.get("basis"), dict):
                    errors.append("duplicate observation requires side, source reference and financial basis")
                else:
                    refs.append(item["source_ref"])
                try:
                    amount(item.get("value"))
                except ValueError:
                    errors.append("duplicate observation requires its finite supplied value")
            refs = list(dict.fromkeys(refs))
            if b.get("source_refs") != refs or b.get("citation") != " | ".join(refs):
                errors.append("duplicate citations must retain all observation source references")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"data-alteration/assumption/certification language detected: {m.group(0)!r} (R2 reconciles, does not alter/certify)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (no source data altered / no reserve certified)")
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
