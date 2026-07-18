#!/usr/bin/env python3
"""Deterministic output validation for claims-fraud-referral-assistant.

Enforces the R3 decision-support + Draft & package guardrails before a referral pack is
presented:
  1. Only allowed recommendations are used (no fraud finding / denial / closure states).
  2. Every triggered indicator uses an APPROVED indicator id and carries evidence + citation.
  3. score_band is consistent with indicator_score (+ prior-SIU override).
  4. Each `refer-to-siu` referral carries a complete, cited referral_package AND a drafted
     referral_document containing all required template sections.
  5. Required human approvals are recorded as pending/required (never auto-approved).
  6. No unsupported/unapproved-claim language: fraud finding, adverse decision, denial,
     closure, or accusatory customer-facing text (defamation risk).
  7. The standing note is present.

Usage: python validate_output.py referral.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_RECS = {"refer-to-siu", "monitor", "insufficient-indicators", "needs-data"}
APPROVED_INDICATORS = {
    "FR-LATE-REPORT", "FR-EARLY-LOSS", "FR-POST-INCREASE", "FR-CLAIM-FREQ", "FR-NO-REPORT",
    "FR-DOC-GAP", "FR-INCONSISTENT", "FR-LAPSE-REINSTATE", "FR-PRIOR-SIU",
}
REQUIRED_SECTIONS = ["Claim Summary", "Fraud Indicators Observed", "Chronology",
                     "Supporting Evidence", "Recommendation", "Required Human Approvals",
                     "Limitations"]
APPROVAL_KEYS = ("adjuster_attestation", "siu_intake_ack")
PENDING_STATES = {"pending", "required", "not recorded", "to be recorded"}
STANDING_NOTE = ("Draft fraud referral only; no fraud finding has been made, no claim has "
                 "been denied or closed, and no adverse customer decision has been taken.")
# Unsupported-claim / adverse-decision / closure language (fail closed).
PROHIBITED_PATTERNS = [
    # affirmative fraud assertions only; the mandatory disclaimer language ("no fraud
    # finding has been made", "not a determination of fraud") must be allowed to appear.
    r"\bconfirmed fraud\b", r"\bfraud confirmed\b", r"\bis fraudulent\b",
    r"\bproven fraud\b", r"\bfound to have committed fraud\b", r"\bcommitted fraud\b",
    r"\bdeny (the )?claim\b", r"\bdenied the claim\b", r"\bclaim denied\b",
    r"\bclose (the )?claim\b", r"\bclaim closed\b", r"\bvoid the policy\b", r"\brescind\b",
    r"\bsiu accepted\b", r"\breferral accepted\b", r"\bno further action\b",
]
# Accusatory customer-facing text (defamation risk).
CUSTOMER_PATTERNS = [
    r"\btell the (insured|customer|claimant) (they|you) committed fraud\b",
    r"\baccuse the (insured|customer|claimant)\b",
    r"\bnotify the (insured|customer|claimant) of (the )?fraud\b",
]


def _expected_band(score, prior_siu, cfg):
    if score >= cfg["refer_min"] or prior_siu:
        return "Refer"
    return "Monitor" if score >= cfg["monitor_min"] else "Insufficient"


def validate(doc: dict, cfg=None) -> list[str]:
    cfg = cfg or {"refer_min": 6, "monitor_min": 3}
    errors: list[str] = []
    records = doc.get("referrals") or []
    if not records:
        return ["referral output has no records"]

    for r in records:
        cid = r.get("claim_id", "?")
        rec = r.get("recommendation")
        if rec not in ALLOWED_RECS:
            errors.append(f"{cid}: disallowed recommendation {rec!r} "
                          f"(fraud finding / denial / closure not permitted)")
        # indicators must be from the approved catalogue and carry evidence + citation
        for ind in r.get("indicators_triggered") or []:
            iid = ind.get("id")
            if iid not in APPROVED_INDICATORS:
                errors.append(f"{cid}: unapproved indicator {iid!r} (not in approved red-flag catalogue)")
            if not ind.get("evidence") or not ind.get("citation"):
                errors.append(f"{cid}: indicator {iid!r} missing evidence or citation")
        # band tie-out (skip pure needs-data records)
        if rec != "needs-data":
            prior_siu = any(i.get("id") == "FR-PRIOR-SIU" for i in (r.get("indicators_triggered") or []))
            exp = _expected_band(r.get("indicator_score", 0), prior_siu, cfg)
            if r.get("score_band") != exp:
                errors.append(f"{cid}: score_band {r.get('score_band')!r} != expected {exp!r} "
                              f"for score {r.get('indicator_score')}")
        # referral completeness + template fidelity + approvals
        if rec == "refer-to-siu":
            pkg = r.get("referral_package") or {}
            if not pkg:
                errors.append(f"{cid}: referred but no referral_package")
            elif not pkg.get("citations"):
                errors.append(f"{cid}: referral_package missing citations")
            appr = pkg.get("required_approvals") or {}
            for k in APPROVAL_KEYS:
                if k not in appr:
                    errors.append(f"{cid}: required approval {k!r} not recorded")
                elif str(appr.get(k)).strip().lower() not in PENDING_STATES:
                    errors.append(f"{cid}: approval {k!r} must be pending/required, got {appr.get(k)!r} "
                                  f"(this skill never records human approval as granted)")
            docmd = r.get("referral_document") or ""
            missing = [s for s in REQUIRED_SECTIONS if s not in docmd]
            if missing:
                errors.append(f"{cid}: referral_document missing required template section(s): {missing}")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"unsupported/adverse-decision language detected: {m.group(0)!r} "
                          f"(draft referral never makes a fraud finding, denies, or closes)")
    for pat in CUSTOMER_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"accusatory customer-facing language detected: {m.group(0)!r} (defamation risk)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "referral_example.json"
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
