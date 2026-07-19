#!/usr/bin/env python3
"""Deterministic output validation for operational-resilience-scenario-tester.

Validates the final scenario-test pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Fails closed on any miss. Checks:
  1. Every scenario with an evaluable tolerance outcome (within/breach) has >= 1 recovery
     evidence and >= 1 cited evidence row.
  2. Every recorded response decision is complete (owner_role + timestamp + evidence_ref).
  3. suggested_disposition equals the deterministic mapping from the scenario set.
  4. No R3-prohibited conclusion language: no resilience self-assessment sign-off, compliance
     determination, regulatory filing/submission, attestation, or case/exercise closure.
  5. The standing disclaimer is present.
  6. remediation_actions are included when any breach or high-severity lesson is present.

This is a decision-support (R3) screen: the pack may present evidence and a suggested review
disposition ONLY; the resilience conclusion, sign-off, filing, and closure remain human.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_MARK = "human adjudication required"
HIGH_LESSON = {"high", "severe", "critical"}

# Positive conclusions an R3 decision-support skill must NOT assert (it evidences, it does
# not decide, sign off, file, or close). The disclaimer field is exempt from this scan.
DETERMINATION_PATTERNS = [
    r"\bwe (attest|certify|conclude|confirm|approve)\b",
    r"\bsign(?:ed|s)?[ -]?off\b",
    r"\bfully compliant\b",
    r"\b(?:is|are|remain) compliant\b",
    r"\bnon-?compliant\b",
    r"\bmeets all (?:regulatory )?(?:requirements|obligations)\b",
    r"\bno further action (?:is )?required\b",
    r"\bfile (?:the |a )?(?:regulatory )?(?:report|return|notification)\b",
    r"\bsubmit(?:ted)? to (?:the )?regulator\b",
    r"\bclose (?:the |this )?(?:case|exercise|test|programme|finding)\b",
    r"\bthe (?:firm|service|bank) (?:is|will remain) (?:fully )?resilient\b",
    r"\bself-assessment (?:is )?(?:complete|approved|signed)\b",
    r"\bboard (?:has )?(?:attested|approved|signed)\b",
    r"\bwe (?:can|will) remain within (?:our|all) impact tolerances\b",
]


def _disposition(scenarios: list) -> str:
    """Identical mapping to calculate_or_transform._disposition (see domain-rules.md)."""
    outcomes = [s.get("outcome") for s in scenarios]
    lesson_sev = [str(l.get("severity", "")).lower()
                  for s in scenarios for l in s.get("lessons", [])]
    if "breach" in outcomes or any(x in HIGH_LESSON for x in lesson_sev):
        return "Escalate"
    review = (
        any(s.get("coverage", {}).get("missing_dimensions") for s in scenarios)
        or any(x == "medium" for x in lesson_sev)
        or any(s.get("thin_margin") for s in scenarios)
        or any(s.get("quality_flags") for s in scenarios)
        or any(s.get("decision_gaps") for s in scenarios)
        or "not_evaluable" in outcomes
    )
    return "Review" if review else "Informational"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    scenarios = pack.get("scenarios") or []
    if not scenarios:
        errors.append("pack has no scenarios")

    lesson_sev_all = []
    breach_present = False
    for s in scenarios:
        sid = s.get("scenario_id", "?")
        outcome = s.get("outcome")
        if outcome == "breach":
            breach_present = True
        if outcome in ("within", "breach"):
            if not s.get("recovery_evidence_count"):
                errors.append(f"scenario {sid} has an evaluable outcome but no recovery evidence")
            if not (s.get("evidence") or []):
                errors.append(f"scenario {sid} has an evaluable outcome but no cited evidence")
            for row in (s.get("evidence") or []):
                if not (str(row.get("citation") or "").strip()):
                    errors.append(f"scenario {sid} evidence row missing citation")
        for d in (s.get("decisions") or []):
            if not d.get("complete", False):
                errors.append(f"scenario {sid} decision {d.get('decision_id')} is incomplete "
                              f"(needs owner_role + timestamp + evidence_ref)")
        if s.get("decision_gaps"):
            errors.append(f"scenario {sid} has decision gaps: {s['decision_gaps']}")
        lesson_sev_all += [str(l.get("severity", "")).lower() for l in s.get("lessons", [])]

    exp = _disposition(scenarios)
    if pack.get("suggested_disposition") != exp:
        errors.append(f"suggested_disposition {pack.get('suggested_disposition')!r} != "
                      f"deterministic {exp!r} for the scenario set")

    # scan free text (narrative + notes + scenario titles/gaps), NOT the disclaimer field
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    for s in scenarios:
        text_parts.append(str(s.get("title", "")))
        text_parts += [str(g) for g in (s.get("gaps") or [])]
    text = " ".join(text_parts)
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited conclusion language detected: {m.group(0)!r} "
                          f"(R3 evidences and recommends; it does not decide, sign off, file, or close)")

    disclaimer_text = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER_MARK not in disclaimer_text:
        errors.append("missing standing disclaimer (must state human adjudication is required)")

    high_present = any(x in HIGH_LESSON for x in lesson_sev_all)
    if (breach_present or high_present) and not (pack.get("remediation_actions")):
        errors.append("breach or high-severity lesson present but no remediation_actions included")

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
