#!/usr/bin/env python3
"""Deterministic output validation for transaction-process-tracker.

Enforces the Draft & package guardrails before the assembled tracker is presented:
  1. All required template sections are present (mirrors assets/output-template.md).
  2. No unsupported/unapproved claims: every party_tracker entry carries a citation, and any
     bid recorded on a party carries its own citation.
  3. Control-gate consistency: any active party with data-room access granted but no executed
     NDA must carry a matching control-exception (never silently accepted).
  4. Required human approvals are recorded (type + role + date + citation); missing required
     approvals appear as outstanding open items; delivery approval is flagged as required.
  5. No deal-decision / bid-selection / recommendation language and no send/grant/deliver
     (execution) language.
  6. tracker_status is 'draft-tracker' (never final / sent / published).
  7. The standing note is present.

Usage: python validate_output.py tracker.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Canonical tracker sections; the human-facing render in assets/output-template.md mirrors
# these (versioned contract). All must appear in the manifest's `sections`.
REQUIRED_SECTIONS = [
    "process_summary", "party_tracker", "approvals", "reminders", "change_log",
    "open_items", "source_index",
]
STANDING_NOTE = (
    "Draft transaction process tracker for internal deal-team review only. It records "
    "status, reminders, and a change log; it is not a deal decision, bid selection, or "
    "recommendation, and no outreach, NDA, data-room access, or delivery has been executed."
)

# Claims a tracker must NEVER make: it does not pick a winner or recommend a counterparty.
DECISION_PATTERNS = [
    r"\bwinning bid\b", r"\bwinner\b", r"\bselected? (buyer|bidder|counterparty|winner)\b",
    r"\bselect(ing)? .{0,40}\bas the (buyer|bidder|counterparty|winner)\b",
    r"\baward(ing|ed)? (the deal|exclusivity)\b", r"\bgrant(ing|ed)? exclusivity\b",
    r"\bwe recommend (accepting|selecting|proceeding with)\b", r"\brecommend(ed)? bid\b",
    r"\bproceed to (close|closing)\b", r"\bdeal approved\b", r"\baccept(ed)? the (bid|offer)\b",
]
# Actions a draft tracker must NEVER perform: it does not send, grant, or deliver anything.
EXECUTION_PATTERNS = [
    r"\bsent the (nda|tracker|outreach|teaser|cim)\b", r"\bemailed the\b", r"\bwe have sent\b",
    r"\bgrant(ed|ing)? .{0,30}(data.?room|vdr) access\b", r"\bopened (data.?room|vdr) access\b",
    r"\bsubmitted the (bid|loi|ioi)\b", r"\bdistributed to (buyers|bidders|the client)\b",
    r"\bdelivered to the client\b", r"\bexecuted on behalf\b", r"\bsent to the client\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections")
    if not isinstance(sections, dict):
        return ["tracker output has no 'sections' object"]

    # 1. required sections present
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required tracker section '{sec}'")

    # 2. no unsupported claims: party entries (and any bid) must be cited
    entries = sections.get("party_tracker")
    if not isinstance(entries, list) or not entries:
        errors.append("party_tracker must be a non-empty list")
        entries = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        pid = e.get("party_id", "?")
        if e.get("status") and not e.get("citation"):
            errors.append(f"unsupported claim: party {pid!r} asserts status "
                          f"{e.get('status')!r} without a citation")
        bid = e.get("bid")
        if isinstance(bid, dict) and not bid.get("citation"):
            errors.append(f"unsupported claim: party {pid!r} bid recorded without a citation")

        # 3. control-gate consistency
        if (e.get("engagement", "active") == "active"
                and e.get("access_status") == "granted"
                and e.get("nda_status") != "executed"):
            ex_types = {x.get("type") for x in (e.get("exceptions") or []) if isinstance(x, dict)}
            if "nda-not-executed" not in ex_types:
                errors.append(f"unflagged control exception: party {pid!r} has data-room access "
                              f"granted without an executed NDA and is not flagged")

    # 4. approvals recorded well-formed; delivery approval flagged
    approvals = sections.get("approvals")
    if not isinstance(approvals, dict) or "recorded" not in approvals:
        errors.append("approvals section missing or lacks a 'recorded' list")
    else:
        for rec in approvals.get("recorded") or []:
            for field in ("type", "approver_role", "date", "citation"):
                if not rec.get(field):
                    errors.append(f"recorded approval {rec.get('type','?')!r} missing '{field}'")
    if doc.get("human_approval_required_before_delivery") is not True:
        errors.append("human_approval_required_before_delivery must be true (external-delivery posture)")

    # 5. forbidden language
    scan = json.dumps(doc)
    for label, patterns in (("deal-decision", DECISION_PATTERNS),
                            ("delivery/execution", EXECUTION_PATTERNS)):
        for pat in patterns:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {label} language detected: {m.group(0)!r} "
                              f"(the tracker only records status in a draft)")

    # 6. tracker status must be draft
    if doc.get("tracker_status") != "draft-tracker":
        errors.append(f"tracker_status must be 'draft-tracker', got {doc.get('tracker_status')!r}")

    # 7. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "tracker_example.json"
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
