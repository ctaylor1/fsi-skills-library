#!/usr/bin/env python3
"""Deterministic output validation for stablecoin-payment-controls-reviewer.

Validates the final findings pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. R3 fail-closed checks:
  1. Every finding (status fail|gap) has >= 1 cited evidence row.
  2. suggested_disposition equals the deterministic mapping from controls_evaluated.
  3. No prohibited decision / approval / attestation / closure / filing language
     (narrative + notes + control reasons).
  4. The standing disclaimer is present.
  5. remediation_prompts are included when any finding exists.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

CRITICAL = {
    "reserve_backing_ratio", "reserve_asset_quality", "reserve_attestation_current",
    "custody_qualified_custodian", "sanctions_wallet_screening", "travel_rule",
    "onchain_ledger_recon",
}
ESCALATE_FAIL_COUNT = 3
DISCLAIMER = ("Control-review evidence only; not a compliance determination, launch "
              "approval, or attestation. No finding has been closed and no filing or "
              "system-of-record change has been made.")

# Prohibited R3 assertions: regulated decision, approval, attestation, closure, filing.
PROHIBITED_PATTERNS = [
    r"\bwe approve\b", r"\bapproved for (launch|production|go[- ]?live|release)\b",
    r"\bcleared? (for|to) (launch|production|go[- ]?live)\b",
    r"\bcertif(y|ied) (as )?compliant\b", r"\bwe attest\b", r"\battest that\b",
    r"\bissue an attestation\b", r"\bsigned? off\b", r"\bsign-off\b",
    r"\bcontrols are adequate\b", r"\bcontrols are compliant\b", r"\bfully compliant\b",
    r"\bcompliant with (the )?(genius act|mica|nydfs)\b", r"\bno (sanctions )?violations?\b",
    r"\bfit for (launch|production)\b", r"\bpasses (the )?(audit|exam|examination)\b",
    r"\bcase closed\b", r"\bclose (the )?(case|review|finding)\b", r"\bfinding closed\b",
    r"\bmark(ed)? (as )?remediated\b", r"\bwaive (the )?(finding|control|deficiency)\b",
    r"\bfile (the )?attestation\b", r"\b(submit|file) (the report )?(to|with) (the )?regulator\b",
    r"\bpost to (the )?register\b", r"\b(write|update) .{0,12}system of record\b",
]


def _expected_disposition(evaluated: list[dict]) -> str:
    fails = [c for c in evaluated if c.get("status") == "fail"]
    defects = [c for c in evaluated if c.get("status") in ("fail", "gap")]
    critical_defect = any(
        c.get("id") in CRITICAL and c.get("status") in ("fail", "gap", "not_evaluable")
        for c in evaluated)
    if critical_defect or len(fails) >= ESCALATE_FAIL_COUNT:
        return "Material Gaps - Escalate"
    if defects:
        return "Findings - Remediation Recommended"
    return "Controls Evidenced"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    evaluated = pack.get("controls_evaluated") or []
    findings = [c for c in evaluated if c.get("status") in ("fail", "gap")]

    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('id')} ({f.get('status')}) has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f.get('id')} evidence row missing citation")

    exp = _expected_disposition(evaluated)
    if pack.get("suggested_disposition") != exp:
        errors.append(
            f"suggested_disposition {pack.get('suggested_disposition')!r} != deterministic {exp!r}")

    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
        + [str(c.get("reason", "")) for c in evaluated])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(
                f"prohibited decision/closure/filing language detected: {m.group(0)!r} "
                f"(R3 evidences and recommends; a human adjudicates)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " "
                                  + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if findings and not pack.get("remediation_prompts"):
        errors.append("findings present but no remediation_prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
