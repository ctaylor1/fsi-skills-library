#!/usr/bin/env python3
"""Deterministic output validation for dispute-operations-assistant.

Enforces the R3 "draft & package" decision-support guardrails before any dispute case-work
is handed to a human adjudicator. Fails closed on any miss so an overreaching or
decision-making output cannot be presented as ready:

  1. Only decision-SUPPORT dispositions appear (no decide/accept/deny/close/file states).
  2. Role and transaction identity are recorded (issuer|acquirer; reason code present).
  3. A `draft-ready-for-review` case carries a complete draft package: all required template
     sections, an on-time (or at-risk) deadline, sufficient evidence, and a current rule
     version.
  4. No unsupported/unapproved claims: every draft package carries citations and contains no
     outcome-guarantee or asserted-fact-without-evidence language.
  5. Required human approvals are RECORDED and NOT self-granted: authorization stays
     `pending-human-authorization` and `authorized_submission` is false.
  6. No decision / closure / filing / credit language anywhere in the output.
  7. The standing note (draft-only; no decision, submission, or account movement) is present.

Usage: python validate_output.py response.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {
    "draft-ready-for-review", "evidence-insufficient", "needs-data",
    "out-of-time-review", "rule-version-stale", "route-specialist",
}
ALLOWED_ROLES = {"issuer", "acquirer"}
ALLOWED_ROUTES = {"payment-fraud-case-investigator", "chargeback-dispute-packager",
                  "payment-exception-investigator"}
REQUIRED_SECTIONS = ("case_identification", "reason_code_and_rule_basis", "deadline_and_timeline",
                     "evidence_inventory", "draft_response_narrative", "recommended_disposition",
                     "human_review_and_authorization")
STANDING_NOTE_KEY = "draft decision-support only"

# Completed regulated action / decision / closure / filing / account-movement language.
DECISION_PATTERNS = [
    r"\bchargeback (accepted|denied|upheld|reversed)\b",
    r"\bdispute (won|lost|denied|granted|upheld|resolved in)\b",
    r"\brepresent(ment)? (submitted|filed|sent) to\b",
    r"\bresponse (submitted|filed|sent) to (the )?(network|visa|mastercard|acquirer|issuer)\b",
    r"\bsubmitted to (the )?(network|visa|mastercard|acquirer)\b",
    r"\bwe have (filed|submitted|posted)\b",
    r"\bcase closed\b", r"\bclosed the case\b",
    r"\bprovisional credit (issued|granted|posted)\b", r"\bfinal credit (issued|granted|posted)\b",
    r"\bliability (accepted|assigned|assumed)\b", r"\bwe accept liability\b",
    r"\bcredited the (cardholder|customer|merchant)\b",
    r"\brefund (issued|processed|posted)\b", r"\bcharge(back)? reversed\b",
    r"\bwritten off\b", r"\bwrite-?off approved\b", r"\bno further action\b",
    r"\bposted to the (ledger|system of record)\b",
]
# Outcome guarantee / unsupported asserted-fact language.
UNSUPPORTED_PATTERNS = [
    r"\bguarantee(s|d)?\b[^.]{0,40}\b(win|reversal|refund|recover|prevail|outcome)\b",
    r"\bwe will (win|prevail|recover)\b", r"\bcertain to (win|prevail)\b",
    r"\b100% (win|success|guaranteed)\b", r"\bguaranteed (win|reversal|outcome)\b",
    r"\bcardholder is lying\b", r"\bdefinitely fraud\b",
]


def _validate_draft(pid, draft, errors):
    sections = (draft or {}).get("sections") or {}
    for s in REQUIRED_SECTIONS:
        if s not in sections:
            errors.append(f"{pid}: draft_response missing required template section {s!r}")
    if not (draft or {}).get("citations"):
        errors.append(f"{pid}: draft_response missing citations (unsupported package)")
    hra = sections.get("human_review_and_authorization") or {}
    status = hra.get("authorization_status")
    if status != "pending-human-authorization":
        errors.append(f"{pid}: authorization_status {status!r} must be 'pending-human-authorization' "
                      f"(this skill never self-authorizes)")
    if hra.get("authorized_submission"):
        errors.append(f"{pid}: authorized_submission is true (agent must not authorize submission)")
    if not hra.get("reviewer_role"):
        errors.append(f"{pid}: human approval not recorded (missing reviewer_role)")


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("cases") or []
    if not records:
        return ["case-work output has no cases"]

    for r in records:
        pid = r.get("case_id", "?")
        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{pid}: disallowed disposition {disp!r} "
                          f"(decide/accept/deny/close/file are not permitted in decision support)")
        if r.get("role") not in ALLOWED_ROLES:
            errors.append(f"{pid}: role {r.get('role')!r} not issuer/acquirer (identity)")
        if not r.get("reason_code"):
            errors.append(f"{pid}: missing reason_code (identity)")

        draft = r.get("draft_response")
        if draft is not None:
            _validate_draft(pid, draft, errors)

        if disp == "draft-ready-for-review":
            if draft is None:
                errors.append(f"{pid}: draft-ready-for-review but no draft_response")
            if (r.get("deadline") or {}).get("status") == "out-of-time":
                errors.append(f"{pid}: draft-ready-for-review but deadline is out-of-time")
            if not (r.get("evidence_check") or {}).get("complete"):
                errors.append(f"{pid}: draft-ready-for-review but evidence incomplete")
            if not (r.get("rule_currency") or {}).get("current_ok"):
                errors.append(f"{pid}: draft-ready-for-review but rule version not current")
        if disp == "route-specialist" and r.get("route_specialist") not in ALLOWED_ROUTES:
            errors.append(f"{pid}: route_specialist {r.get('route_specialist')!r} not an approved route")
        if disp == "rule-version-stale" and (r.get("rule_currency") or {}).get("current_ok"):
            errors.append(f"{pid}: rule-version-stale but rule_currency.current_ok is true")
        if disp == "out-of-time-review" and (r.get("deadline") or {}).get("status") != "out-of-time":
            errors.append(f"{pid}: out-of-time-review but deadline status is not out-of-time")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited decision/closure/filing language detected: {m.group(0)!r} "
                          f"(this skill never decides, files, closes, or moves funds)")
    for pat in UNSUPPORTED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"unsupported/guarantee language detected: {m.group(0)!r}")

    if STANDING_NOTE_KEY not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "response_example.json"
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
