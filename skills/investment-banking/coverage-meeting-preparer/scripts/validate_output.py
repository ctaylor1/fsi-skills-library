#!/usr/bin/env python3
"""Deterministic output validation for coverage-meeting-preparer.

Enforces the R2 "Draft & package" guardrails before a coverage-meeting brief is handed to a
human for review and (optionally) approved external delivery:
  1. Template fidelity: a packageable brief has the required sections and no unfilled
     `{{placeholder}}` tokens.
  2. No unsupported / unapproved claims: every claim carries a non-empty citation whose source
     system is on the approved list; the content-integrity flag agrees.
  3. Freshness: no blocking (unacknowledged) stale sources.
  4. MNPI handling: every MNPI claim is internal-only (never placed in a shareable field); if
     any MNPI is present, control-room clearance is recorded as approved.
  5. Approvals recorded: supervisory review is approved and an external-delivery approval slot
     is recorded (this skill never marks it delivered/sent); reviewer sign-off is required.
  6. Draft-only: no send/distribute/file/execute language; no investment recommendation,
     price-target-as-advice, valuation-opinion, or investment/legal/tax-advice language.
  7. The standing note is present.

Fails closed on any miss so a defective or overreaching brief cannot be presented as
ready-to-deliver.

Usage: python validate_output.py brief.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

STANDING_NOTE = (
    "Draft coverage-meeting brief for internal preparation only; this skill does not send, "
    "distribute, file, or execute anything, makes no investment recommendation, price target, "
    "or valuation opinion, and states nothing not backed by a cited approved source. Any "
    "material non-public information is tagged private-side and internal-only; external "
    "delivery requires the recorded control-room and delivery approvals."
)
DEFAULT_APPROVED_SOURCES = {"crm", "filings", "transcript", "research", "marketdata",
                            "news", "dataroom", "comps"}
REQUIRED_BRIEF_SECTIONS = ("engagement_id", "client_name", "meeting_snapshot",
                           "relationship_history", "developments", "strategic_issues",
                           "client_objectives", "discussion_questions", "follow_ups",
                           "citations", "approvals", "reviewer_signoff_required")
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")

DELIVERY_PATTERNS = [
    r"\b(brief|pack|deck) (has been |was )?(sent|distributed|emailed|delivered|shared)\b",
    r"\bi (have |'ve )?(sent|distributed|emailed|delivered|shared|filed|submitted)\b",
    r"\bsent to the (client|prospect|company)\b",
    r"\bdistributed to (the )?(client|attendees|prospect)\b",
    r"\bposted to (the )?crm\b",
    r"\bfiled with\b",
]
ADVICE_PATTERNS = [
    r"\bwe recommend (the client |you )?(buy|sell|invest|acquire|divest)\b",
    r"\byou should (buy|sell|invest|acquire|divest|sign)\b",
    r"\bprice target of\b",
    r"\bfair value (is|of)\b",
    r"\b(guaranteed|guarantee[sd]?) (a )?return\b",
    r"\bstrong buy\b",
    r"\b(investment|legal|tax) advice\b",
    r"\bour valuation (opinion|is)\b",
]


def _claim_system(citation):
    if not citation or ":" not in str(citation):
        return None
    return str(citation).split(":", 1)[0]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    approved = set(doc.get("approved_sources") or DEFAULT_APPROVED_SOURCES)
    briefs = doc.get("briefs") or []
    if not briefs:
        return ["brief output has no records"]

    for b in briefs:
        eid = b.get("engagement_id", "?")
        if not b.get("packageable"):
            continue

        if b.get("status") != "draft-brief":
            errors.append(f"{eid}: packageable but status is {b.get('status')!r} (only draft-brief is packageable)")
        ci = b.get("content_integrity") or {}
        if not ci.get("all_supported"):
            errors.append(f"{eid}: packageable but content not fully supported (unsupported: {ci.get('unsupported')})")
        sc = b.get("stale_check") or {}
        if sc.get("stale_unacknowledged"):
            errors.append(f"{eid}: packageable but has blocking stale sources {sc.get('stale_unacknowledged')}")
        if not b.get("citations"):
            errors.append(f"{eid}: packageable but citations list is empty")

        brief = b.get("brief") or {}
        if not brief:
            errors.append(f"{eid}: packageable but no brief object")
            continue

        # template fidelity
        for sec in REQUIRED_BRIEF_SECTIONS:
            if sec not in brief or brief.get(sec) in (None, "", [], {}):
                errors.append(f"{eid}: brief missing required section {sec!r} (template fidelity)")
        if not brief.get("reviewer_signoff_required"):
            errors.append(f"{eid}: brief missing reviewer_signoff_required=true")
        if not brief.get("handling"):
            errors.append(f"{eid}: brief missing handling label")
        if PLACEHOLDER_RE.search(json.dumps(brief)):
            errors.append(f"{eid}: brief contains unfilled '{{{{placeholder}}}}' tokens (template fidelity)")

        # no unsupported / unapproved claims (independent re-derivation)
        for c in brief.get("claims") or []:
            cite = c.get("citation")
            sysname = _claim_system(cite)
            if not cite:
                errors.append(f"{eid}: claim {c.get('id')!r} ({c.get('section')}) has no citation (unsupported assertion)")
            elif sysname not in approved:
                errors.append(f"{eid}: claim {c.get('id')!r} cites unapproved source system {sysname!r}")
            # MNPI must never be placed in a shareable field
            if c.get("mnpi") and not c.get("internal_only"):
                errors.append(f"{eid}: MNPI claim {c.get('id')!r} is not marked internal-only (barrier breach)")

        # MNPI => control-room clearance recorded as approved
        approvals = brief.get("approvals") or {}
        if brief.get("mnpi_present"):
            clr = (approvals.get("control_room_clearance") or {}).get("status")
            if clr != "approved":
                errors.append(f"{eid}: MNPI present but control_room_clearance not approved (got {clr!r})")

        # approvals recorded
        if (approvals.get("supervisory_review") or {}).get("status") != "approved":
            errors.append(f"{eid}: supervisory_review not recorded as approved")
        ext = approvals.get("external_delivery_approval") or {}
        if "status" not in ext:
            errors.append(f"{eid}: external_delivery_approval not recorded (no status)")
        elif ext.get("status") in ("delivered", "sent", "distributed"):
            errors.append(f"{eid}: external_delivery_approval status {ext.get('status')!r} implies delivery (this skill never delivers)")

    scan = json.dumps(briefs) + " " + str(doc.get("narrative", ""))
    for pat in DELIVERY_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited delivery/execution language detected: {m.group(0)!r} "
                          "(this skill drafts only; a human delivers)")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited advice/recommendation language detected: {m.group(0)!r} "
                          "(no investment recommendation, price target, or valuation opinion)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "brief_example.json"
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
