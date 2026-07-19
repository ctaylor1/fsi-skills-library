#!/usr/bin/env python3
"""Deterministic output validation for regulatory-change-impact-analyzer.

Validates the final impact-assessment pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. This is the R3 prohibited-decision screen: it fails
closed on any autonomous regulated decision, applicability determination, change closure,
regulatory filing, or attestation language, and on missing adjudication controls.

Checks:
  1. Every raised finding has >= 1 cited evidence row.
  2. recommended_disposition equals the deterministic mapping from raised_findings.
  3. No prohibited decision / closure / filing / attestation language (narrative + reasons).
  4. The standing disclaimer is present.
  5. mandatory_adjudication is asserted true.
  6. open_questions (adjudication prompts) are included when any obligation is applicable.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"overdue_or_retroactive", "authority_conflict"}
DISCLAIMER = ("Impact assessment and evidence only; not a compliance determination. "
              "Applicability, disposition, and closure require human adjudication. No "
              "regulatory decision, filing, or system-of-record change has been made.")

# Positive decision / closure / filing / attestation assertions an R3 skill must NOT make.
DECISION_PATTERNS = [
    r"\bwe are (fully )?compliant\b", r"\bthe firm is (fully )?compliant\b",
    r"\b(is|are) (now )?compliant\b", r"\bconfirmed compliant\b", r"\bcertif(y|ies|ied) compliance\b",
    r"\battest(s|ing|ed)? (to )?compliance\b", r"\bno further action (is )?required\b",
    r"\bclos(e|ing|ed) (the|this) (change|item|obligation)\b", r"\bmark(ed)? (as )?(compliant|closed|complete)\b",
    r"\bdispositioned? as (compliant|no.?impact|closed)\b", r"\bnot applicable[,;.]? clos",
    r"\bfile (the|a|this) (report|filing|submission)\b", r"\bsubmit (the|this) (filing|report|attestation)\b",
    r"\bfiled with the regulator\b", r"\bsign(ed)?.?off\b", r"\bwe (hereby )?certify\b",
    r"\bapproved for closure\b", r"\bdecision:? (compliant|close|no impact)\b",
]


def _expected_disposition(pack: dict) -> str:
    raised = set(pack.get("raised_findings") or [])
    applicable = "applicable_in_scope" in raised
    if not applicable:
        return "Informational"
    if (ESCALATORS & raised) or len(raised) >= 3:
        return "Priority"
    return "Assess"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    raised = [f["finding"] for f in findings if f.get("raised")]

    for f in findings:
        if f.get("raised"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"raised finding {f['finding']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"raised finding {f['finding']} evidence row missing citation")

    exp = _expected_disposition(pack)
    if pack.get("recommended_disposition") != exp:
        errors.append(f"recommended_disposition {pack.get('recommended_disposition')!r} != deterministic {exp!r} for raised={raised}")

    # scan free text (narrative + notes + finding reasons), but NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r} (R3 recommends with evidence; a human adjudicates)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if pack.get("mandatory_adjudication") is not True:
        errors.append("mandatory_adjudication must be true (R3 requires human adjudication before disposition/closure)")

    applicable = "applicable_in_scope" in raised
    if applicable and not (pack.get("open_questions")):
        errors.append("applicable obligations present but no open_questions (adjudication prompts) included")

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
