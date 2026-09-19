#!/usr/bin/env python3
"""Deterministic output validation for insurance-rate-form-filing-packager.

Enforces the R3 guardrails before the gap packet is presented:
  1. Every gap carries a non-empty citation.
  2. suggested_disposition is review-only (ready-for-review | gaps-for-review).
  3. No submission / rate-approval / compliance-certification language.
  4. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED = {"ready-for-review", "gaps-for-review", "incomplete"}
DISCLAIMER_RE = re.compile(r"not a filing submission.*(no filing has been submitted|not.*certification)", re.I)
PROHIBITED = [
    r"\b(we|i) (have )?(submitted|filed) the filing\b", r"\bfiling (is|has been) (submitted|filed)\b",
    r"\bfiling is (approved|compliant|approvable)\b", r"\brate is approved\b",
    r"\b(we )?approv(e|ed) the (rate|filing)\b", r"\bcertif(y|ied)\b.{0,30}complian",
]


def validate(p: dict) -> list[str]:
    errors = []
    from insurance_contract import validate_artifact
    errors.extend(validate_artifact(p.get("artifact"), input_doc=p.get("calculation_inputs"), output=p))
    for g in p.get("gaps") or []:
        if not (g.get("citation") or "").strip():
            errors.append(f"gap {g.get('rule','?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED)}")
    try:
        from calculate_or_transform import compute
        expected = compute(p["calculation_inputs"])
        for key in ('checks_run', 'not_evaluable', 'not_applicable', 'gaps', 'suggested_disposition'):
            if p.get(key) != expected[key]:
                errors.append(f"{key} does not reproduce calculation_inputs")
    except (KeyError, ValueError, TypeError) as exc:
        errors.append(f"missing or invalid calculation_inputs: {exc}")
    scan = json.dumps({k: v for k, v in p.items() if k not in {"disclaimer", "calculation_inputs", "artifact"}}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"submission/approval/certification language detected: {m.group(0)!r} (R3 evidences gaps, does not submit/approve/certify)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (gap evidence only / no filing submitted or rate approved)")
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
