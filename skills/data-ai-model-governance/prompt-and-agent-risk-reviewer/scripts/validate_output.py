#!/usr/bin/env python3
"""Deterministic output validation for prompt-and-agent-risk-reviewer.

Validates the final risk-review pack (the calculate_or_transform core + a narrative) before
it is presented or delivered. Enforces the R3 decision-support guardrail: the skill produces
findings and a recommendation for a human adjudicator, and NEVER approves, accepts risk,
attests, or closes the review. Checks:
  1. Every fired finding has a control_id, >= 1 cited evidence row, and remediation guidance.
  2. recommended_rating equals the deterministic max-severity mapping from fired findings.
  3. recommended_disposition equals the deterministic mapping from the rating.
  4. No approval / risk-acceptance / attestation / review-closure language (an R3 skill
     recommends; it does not decide, approve, or close).
  5. The standing disclaimer is present.
  6. The human-adjudication note is present.

Usage:
  python validate_output.py review_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

SEV_RANK = {"Low": 1, "Moderate": 2, "High": 3, "Critical": 4}
RANK_SEV = {v: k for k, v in SEV_RANK.items()}
DISCLAIMER = ("Risk review evidence and recommendations only; not an approval, risk "
              "acceptance, or attestation. Deployment requires human adjudication by the "
              "accountable AI risk owner.")

# Positive approval / decision / closure assertions an R3 review must not make:
APPROVAL_PATTERNS = [
    r"\bapproved for (production|release|deployment|deploy|go-?live)\b",
    r"\bcleared to (deploy|release|go-?live|proceed)\b",
    r"\brisk (is |has been )?accepted\b",
    r"\brisk acceptance (is |has been )?granted\b",
    r"\bexception (is |has been )?granted\b",
    r"\bwaiv(e|ed|es|ing) the control\b",
    r"\bsign(ed|-| )?off\b",
    r"\bwe (hereby )?approve\b",
    r"\bwe attest\b", r"\bi attest\b", r"\battestation (is )?(complete|granted|signed)\b",
    r"\breview (is |has been )?closed\b", r"\bcase closed\b",
    r"\bgo-?live approved\b",
    r"\bauthori[sz](e|ed|es) (the )?(deployment|release|agent|go-?live)\b",
    r"\bfiled? (the )?(risk assessment|attestation|control)\b",
]


def _expected_rating(findings: list) -> str:
    fired = [f for f in findings if f.get("fired")]
    if not fired:
        return "Low"
    return RANK_SEV[max(SEV_RANK.get(f.get("severity"), 1) for f in fired)]


def _expected_disposition(rating: str) -> str:
    if rating in ("Critical", "High"):
        return "Remediate-before-deploy (recommended)"
    if rating == "Moderate":
        return "Conditional-remediation (recommended)"
    return "Proceed-with-standard-controls (recommended)"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    fired = [f for f in findings if f.get("fired")]

    for f in fired:
        cid = f.get("control_id")
        if not (cid or "").strip():
            errors.append("fired finding missing control_id")
            cid = "?"
        evs = f.get("evidence") or []
        if not evs:
            errors.append(f"fired finding {cid} has no evidence")
        for row in evs:
            if not (row.get("citation") or "").strip():
                errors.append(f"fired finding {cid} evidence row missing citation")
        if not (f.get("remediation") or "").strip():
            errors.append(f"fired finding {cid} missing remediation guidance")

    exp_rating = _expected_rating(findings)
    if pack.get("recommended_rating") != exp_rating:
        errors.append(f"recommended_rating {pack.get('recommended_rating')!r} != deterministic {exp_rating!r} for fired={[f.get('control_id') for f in fired]}")

    exp_disp = _expected_disposition(exp_rating)
    if pack.get("recommended_disposition") != exp_disp:
        errors.append(f"recommended_disposition {pack.get('recommended_disposition')!r} != deterministic {exp_disp!r} for rating {exp_rating!r}")

    # scan narrative + notes + finding rationales/remediation, but NOT the disclaimer/adjudication_note fields
    text = " ".join(
        [str(pack.get("narrative", "")), str(pack.get("notes", "")),
         str(pack.get("recommended_disposition", ""))]
        + [str(f.get("rationale", "")) for f in findings]
        + [str(f.get("remediation", "")) for f in findings]
    )
    for pat in APPROVAL_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"approval/closure/attestation language detected: {m.group(0)!r} (R3 recommends; it does not approve, accept risk, attest, or close)")

    disc_scan = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disc_scan:
        errors.append("missing standing disclaimer")

    adj = (str(pack.get("adjudication_note", "")) + " " + str(pack.get("narrative", ""))).lower()
    if "human adjudication" not in adj:
        errors.append("missing human-adjudication note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_pack_example.json"
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
