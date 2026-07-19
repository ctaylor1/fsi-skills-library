#!/usr/bin/env python3
"""Deterministic output validation for ransomware-readiness-assessor (R3 fail-closed screen).

Validates the final readiness pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. Checks:
  1. Every fired finding has >= 1 cited evidence row.
  2. suggested_priority equals the deterministic mapping from fired_findings.
  3. No readiness-decision / attestation / risk-acceptance / remediation-execution / filing /
     closure language in the narrative, notes, or finding reasons (R3 stages recommendations;
     it never decides, attests, executes, files, or closes).
  4. Every staged remediation is a candidate ("staged_for_approval" / "pending_approval" /
     "recommended") that references a fired finding — never an executed/completed action
     (fail closed on autonomous action).
  5. The standing disclaimer is present.
  6. context_prompts are included when any finding fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"privileged_mfa_gap", "segmentation_gap", "backup_coverage_gap",
              "backup_immutability_gap", "restore_test_stale", "exercise_overdue"}
STAGED_OK = {"staged_for_approval", "pending_approval", "recommended"}
DISCLAIMER = ("Ransomware-readiness assessment: evidence and staged remediation "
              "recommendations only; not a readiness decision or attestation. No remediation "
              "has been executed and no assessment has been filed or closed.")

# Prohibited: language asserting the skill decided/attested/accepted-risk/executed/filed/closed.
# R3 decision-support stages recommendations for a human control owner; it never acts.
DECISION_PATTERNS = [
    r"\breadiness (is |was )?(attested|certified|approved|assured)\b",
    r"\b(we |i )?(attest|certify) (that )?(the )?(org|organization|firm|service)?\s*(is )?(ransomware[- ]?)?ready\b",
    r"\bcertify(?:ing)? readiness\b", r"\battestation (is )?signed\b", r"\bsigned the attestation\b",
    r"\bsign-?off (is )?(complete|given|granted)\b", r"\bassessment (is )?(signed off|attested)\b",
    r"\bis (fully |now )?ransomware[- ]ready\b", r"\bdeclared (the org|the service|it)?\s*ready\b",
    r"\bpasses the (readiness )?assessment\b",
    r"\brisk (is |was )?(accepted|formally accepted)\b", r"\b(we|i) accept the risk\b",
    r"\bremediation (is |was |has been )?(complete|completed|applied|done|executed)\b",
    r"\bgaps? (were|have been|are) (closed|fixed|remediated)\b",
    r"\b(we|i) (have )?remediated\b", r"\bhas been remediated\b",
    r"\bbackups? (were|have been|are now) (made )?immutable\b",
    r"\bre-?segmented the network\b", r"\bmfa (was |has been )?enabled\b",
    r"\bfiled the (report|assessment|attestation)\b", r"\bfiled with (the )?regulator\b",
    r"\bsubmitted the (regulatory )?(report|filing|assessment)\b",
    r"\bassessment (is )?(closed|complete and signed)\b", r"\bclosed the assessment\b",
    r"\b(assessment|review) closed\b", r"\bcase closed\b",
]


def _expected_priority(fired: list[str]) -> str:
    if len(fired) >= 3 or (ESCALATORS & set(fired)):
        return "Elevated"
    return "Review" if fired else "Informational"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    fired = [f["finding"] for f in findings if f.get("fired")]

    # 1. evidence + citations on every fired finding
    for f in findings:
        if f.get("fired"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"fired finding {f['finding']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired finding {f['finding']} evidence row missing citation")

    # 2. deterministic priority tie-out
    exp = _expected_priority(fired)
    if pack.get("suggested_priority") != exp:
        errors.append(f"suggested_priority {pack.get('suggested_priority')!r} != deterministic {exp!r} for fired={fired}")

    # 3. no decision/attestation/execution/filing/closure language (scan narrative + notes +
    #    finding reasons, NOT the disclaimer field which legitimately names those as negatives)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"decision/action language detected: {m.group(0)!r} (R3 stages recommendations; it does not decide/attest/execute/file/close)")

    # 4. staged remediations must be candidates only, tied to a fired finding
    for sr in pack.get("staged_remediations") or []:
        rid = sr.get("remediation_id", "?")
        status = str(sr.get("status", "")).lower()
        if status not in STAGED_OK:
            errors.append(f"staged_remediation {rid} status {sr.get('status')!r} is not a staged candidate "
                          f"(autonomous action is prohibited; must be one of {sorted(STAGED_OK)})")
        rf = sr.get("related_finding")
        if rf not in fired:
            errors.append(f"staged_remediation {rid} related_finding {rf!r} is not a fired finding")

    # 5. standing disclaimer present
    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    # 6. context prompts when findings fired
    if fired and not pack.get("context_prompts"):
        errors.append("findings fired but no context_prompts included")

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
