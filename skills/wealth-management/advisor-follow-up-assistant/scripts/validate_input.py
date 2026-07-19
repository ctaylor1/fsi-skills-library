#!/usr/bin/env python3
"""Deterministic input validation for advisor-follow-up-assistant.

Validates a post-meeting follow-up request before the draft package is assembled. Fails closed
on structural problems (missing top-level fields, malformed meeting block). Warns on data gaps
that force a `needs-data` disposition (uncited material assertions, action items without an owner
or due date, a recommendation that requires a disclosure but has none) so the drafter surfaces
them instead of guessing.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, template_version, disclosures_version, followup_id, author_id,
  client{household_id,name_masked,senior_or_vulnerable},
  meeting{date,channel,attendees[],citation},
  discussion_points[{topic,summary,citation}],
  recommendations[{id,summary,requires_disclosure,requires_suitability_review,citation}],
  action_items[{id,owner,description,due_date,citation}],
  client_communication{channel,subject,key_points[],citation},
  disclosures[{id,covers_recommendation,ref,citation}],
  crm_update{fields[{field,proposed_value,citation}]},
  next_meeting{target_timeframe,purpose,citation},
  approvals[{role,name_masked,status}]

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "followup_id", "meeting")
APPROVAL_ROLES = ("Advisor", "Supervisory Principal")
ACTION_KEYS = ("owner", "due_date", "citation")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    # --- meeting block (structural = error) ---
    meeting = doc.get("meeting") or {}
    if not isinstance(meeting, dict):
        errors.append("meeting must be an object")
    else:
        if not meeting.get("date"):
            errors.append("meeting.date is required")
        if not meeting.get("citation"):
            warnings.append("meeting.citation missing -> meeting summary unsupported (needs-data)")

    # --- discussion points (uncited = needs-data warning) ---
    for i, dp in enumerate(doc.get("discussion_points") or []):
        if not dp.get("citation"):
            warnings.append(f"discussion_points[{i}] ({dp.get('topic','?')}) missing citation -> needs-data")

    # --- action items (missing owner/due/citation = needs-data warning) ---
    for i, ai in enumerate(doc.get("action_items") or []):
        tag = f"action_items[{i}] ({ai.get('id','?')})"
        for k in ACTION_KEYS:
            if not ai.get(k):
                warnings.append(f"{tag}: missing '{k}' -> needs-data")

    # --- recommendations: disclosure completeness + suitability routing ---
    disclosures = doc.get("disclosures") or []
    covered = {d.get("covers_recommendation") for d in disclosures}
    for rec in doc.get("recommendations") or []:
        rid = rec.get("id")
        if not rec.get("citation"):
            warnings.append(f"recommendation {rid!r} missing citation -> needs-data")
        if rec.get("requires_disclosure") and rid not in covered:
            warnings.append(f"recommendation {rid!r} requires a disclosure but none covers it -> needs-data")
        if rec.get("requires_suitability_review"):
            warnings.append(f"recommendation {rid!r} requires suitability review -> will route to "
                            f"suitability-reg-bi-reviewer (not approved here)")

    # --- client communication (uncited = needs-data warning) ---
    comm = doc.get("client_communication") or {}
    if comm and not comm.get("citation"):
        warnings.append("client_communication missing citation -> key points unsupported (needs-data)")

    # --- crm update fields (uncited = needs-data warning) ---
    for i, f in enumerate((doc.get("crm_update") or {}).get("fields") or []):
        if not f.get("citation"):
            warnings.append(f"crm_update.fields[{i}] ({f.get('field','?')}) missing citation -> needs-data")

    # --- next meeting (uncited = needs-data warning) ---
    nm = doc.get("next_meeting") or {}
    if nm and not nm.get("citation"):
        warnings.append("next_meeting missing citation -> needs-data")

    # --- senior / vulnerable indicator routes to the protection screener ---
    if (doc.get("client") or {}).get("senior_or_vulnerable"):
        warnings.append("client.senior_or_vulnerable set -> route to senior-investor-protection-screener")

    # --- versions present ---
    if not doc.get("template_version"):
        warnings.append("template_version missing -> record the versioned template contract")
    if not doc.get("disclosures_version"):
        warnings.append("disclosures_version missing -> record the versioned disclosures contract")

    # --- approvals must not be pre-granted in the request ---
    approvals = doc.get("approvals") or []
    seen = {a.get("role") for a in approvals}
    for role in APPROVAL_ROLES:
        if role not in seen:
            warnings.append(f"approvals: no '{role}' entry -> will be added as pending")
    for a in approvals:
        st = str(a.get("status", "")).lower()
        if st and st != "pending":
            errors.append(f"approvals: '{a.get('role')}' status {a.get('status')!r} is not 'pending' "
                          f"(this skill drafts; approvals are granted by humans out-of-band)")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "followup_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
