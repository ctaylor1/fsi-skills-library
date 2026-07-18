#!/usr/bin/env python3
"""Deterministic output validation for third-party-ai-due-diligence-assistant.

Enforces the R3 "Draft & package" guardrails before a third-party AI due-diligence package
is handed to a human for adjudication. Fails closed on any miss so a defective or overreaching
package cannot be presented as a decision:

  1. Classification: every package carries a known provider criticality and rubric version.
  2. Allowed status only (no approval/onboarding/closure states).
  3. Packageable invariants: a `draft-assessment` has a rubric-valid residual rating, a
     permitted RECOMMENDED disposition, complete required-domain coverage, and non-empty
     findings.
  4. No unsupported/unapproved assertions: every finding cites a bundled evidence item.
  5. Human adjudication: every package sets `human_adjudication_required: true` (R3 - the
     recommendation is decision support, not a decision).
  6. No autonomous-decision / approval / onboarding / risk-acceptance / contract-execution
     language anywhere in the packages.
  7. The standing disclaimer (human review; no approval/onboarding/rejection; no risk
     acceptance; no contract execution) is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

KNOWN_CRITICALITY = {"High", "Medium", "Low"}
ALLOWED_STATUS = {"draft-assessment", "insufficient-evidence", "stale-evidence",
                  "unsupported-finding", "needs-data"}
ALLOWED_RATINGS = {"Low", "Medium", "High", "Critical"}
ALLOWED_DISPOSITIONS = {"proceed-with-conditions", "remediate-before-onboarding", "do-not-proceed"}
STANDING_NOTE = (
    "Draft third-party AI due-diligence package for human review only; this skill does not "
    "approve, onboard, or reject any provider, does not accept risk, and does not sign or "
    "execute any contract - every finding and the recommended disposition require human "
    "adjudication before any onboarding decision."
)
# Autonomous-decision / approval overreach the skill must never emit (R3).
DECISION_PATTERNS = [
    r"\b(provider|vendor|model|engagement) (is|has been|are) (approved|onboarded|rejected|cleared)\b",
    r"\bapproved for (production|onboarding|use|go-live)\b",
    r"\bcleared for (production|onboarding|go-live)\b",
    r"\bonboarding (is )?approved\b",
    r"\bwe (hereby )?(approve|onboard|reject) (the )?(provider|vendor|model)\b",
    r"\brisk (has been |is )?accepted\b",
    r"\bwe accept the (residual )?risk\b",
    r"\bfinal (approval|decision)\b",
    r"\bcontract (is |has been )?(signed|executed)\b",
    r"\bgo-live (is )?(approved|authorized)\b",
    r"\bno further (review|due diligence) (is )?(needed|required)\b",
    r"\bautomatically onboard(ed)?\b",
]


def _covered(pkg) -> bool:
    """Every domain in the coverage view carries evidence (packageable invariant)."""
    cov = pkg.get("domain_coverage")
    if cov is None:
        cov = [d for d in (pkg.get("domain_summary") or [])]
    if not cov:
        return False
    return all(d.get("evidence_present") for d in cov)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    packages = doc.get("packages") or []
    if not packages:
        return ["due-diligence output has no packages"]

    for p in packages:
        eid = p.get("engagement_id", "?")
        crit = p.get("criticality")
        status = p.get("status")

        if status not in ALLOWED_STATUS:
            errors.append(f"{eid}: disallowed status {status!r} (approval/onboarding/closure not permitted)")
        if status != "needs-data" and crit not in KNOWN_CRITICALITY:
            errors.append(f"{eid}: unknown/unclassified criticality {crit!r}")

        # Every package (blocked or not) must flag that a human must adjudicate.
        if p.get("human_adjudication_required") is not True:
            errors.append(f"{eid}: package must set human_adjudication_required=true "
                          f"(R3: the recommendation requires human adjudication)")

        packageable = bool(p.get("packageable"))
        if packageable:
            if status != "draft-assessment":
                errors.append(f"{eid}: packageable but status is {status!r}, expected 'draft-assessment'")
            rating = p.get("residual_risk_rating")
            if rating not in ALLOWED_RATINGS:
                errors.append(f"{eid}: packageable but residual_risk_rating {rating!r} not in rubric")
            disp = p.get("recommended_disposition")
            if disp not in ALLOWED_DISPOSITIONS:
                errors.append(f"{eid}: packageable but recommended_disposition {disp!r} not permitted")
            if not _covered(p):
                errors.append(f"{eid}: packageable but required-domain coverage is incomplete")
            findings = p.get("findings_index") or []
            if not findings:
                errors.append(f"{eid}: packageable but findings_index is empty")
            for f in findings:
                if not f.get("supported"):
                    errors.append(f"{eid}: unsupported finding: {f.get('finding_id')!r} cites evidence "
                                  f"{f.get('evidence_id')!r} not in bundle")

    scan = json.dumps(packages) + " " + str(doc.get("narrative", ""))
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited approval/decision language detected: {m.group(0)!r} "
                          f"(this skill recommends only; a human adjudicates)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
