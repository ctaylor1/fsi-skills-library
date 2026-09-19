#!/usr/bin/env python3
"""Validate a sourced follow-up request. Errors reject structure; warnings block readiness."""
from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

CAPACITIES = {"advisory", "brokerage", "private-bank", "trust"}
CHANNELS = {"email", "letter", "portal"}

def iso(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False

def text(value):
    return isinstance(value, str) and bool(value.strip())

def validate(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["request must be an object"], []
    for key in ("config_version", "template_version", "disclosures_version", "followup_id", "request_id", "author_id", "as_of_date"):
        if not text(doc.get(key)):
            errors.append(f"{key} is required")
    if not iso(doc.get("as_of_date")):
        errors.append("as_of_date must be an ISO date")
    for key in ("client", "meeting", "client_communication", "crm_update", "next_meeting", "engagement", "communication_policy"):
        if not isinstance(doc.get(key), dict):
            errors.append(f"{key} must be an object")
    for key in ("discussion_points", "recommendations", "action_items", "disclosures", "source_inventory", "approvals"):
        if not isinstance(doc.get(key), list) or any(not isinstance(x, dict) for x in doc[key]):
            errors.append(f"{key} must be a list of objects")
    if errors:
        return errors, warnings
    engagement = doc["engagement"]
    if not isinstance(engagement.get("capacity"), str) or engagement.get("capacity") not in CAPACITIES or engagement.get("jurisdiction") != "US":
        errors.append("engagement needs a supported capacity and US jurisdiction")
    policy = doc["communication_policy"]
    roles = policy.get("required_roles")
    if not isinstance(roles, list) or not roles or not all(text(x) for x in roles) or len(set(roles)) != len(roles) or "Advisor" not in roles:
        errors.append("communication_policy.required_roles must include Advisor and contain unique role names")
    if policy.get("version") != doc["config_version"] or policy.get("capacity") != engagement.get("capacity") or not text(policy.get("owner")) or not text(policy.get("approved_by")):
        errors.append("communication_policy must match capacity/config_version and record owner and approval")
    if policy.get("classification") not in {"correspondence", "retail", "institutional", "internal"}:
        errors.append("communication_policy needs an explicit communication classification")
    registry = {}
    for i, source in enumerate(doc["source_inventory"]):
        citation = source.get("citation")
        if not text(citation) or citation in registry or not text(source.get("owner")):
            errors.append(f"source_inventory[{i}] needs a unique citation and owner")
            continue
        registry[citation] = source
        if not iso(source.get("as_of")) or not iso(source.get("valid_until")):
            errors.append(f"source_inventory[{i}] needs as_of and valid_until dates")
        elif not source["as_of"] <= doc["as_of_date"] <= source["valid_until"]:
            errors.append(f"source_inventory[{i}] is future-dated or expired")
    for field in ("template_version", "disclosures_version"):
        if doc[field] not in registry:
            errors.append(f"{field} must resolve to the controlled source inventory")
    def cited(item, label):
        if not text(item.get("citation")) or item["citation"] not in registry:
            warnings.append(f"{label}: missing or unknown citation")
    def required(item, fields, label):
        for field in fields:
            if not text(item.get(field)):
                warnings.append(f"{label}: missing {field}")
        cited(item, label)
    cited(policy, "communication_policy")
    client = doc["client"]
    required(client, ("household_id", "name_masked"), "client")
    if not isinstance(client.get("senior_or_vulnerable"), bool):
        errors.append("client.senior_or_vulnerable must be boolean")
    meeting = doc["meeting"]
    required(meeting, ("meeting_id", "date", "channel"), "meeting")
    if not iso(meeting.get("date")) or meeting["date"] > doc["as_of_date"]:
        errors.append("meeting.date must be a supported date no later than as_of_date")
    if not isinstance(meeting.get("attendees"), list) or not meeting["attendees"] or not all(text(x) for x in meeting["attendees"]):
        warnings.append("meeting: attendee roster is required")
    if not doc["discussion_points"]:
        warnings.append("discussion_points: no documented discussion")
    for i, point in enumerate(doc["discussion_points"]):
        required(point, ("topic", "summary"), f"discussion_points[{i}]")
    for list_key in ("recommendations", "action_items", "disclosures"):
        ids = set()
        for i, item in enumerate(doc[list_key]):
            if not text(item.get("id")) or item["id"] in ids:
                errors.append(f"{list_key}[{i}]: id must be present and unique")
            else:
                ids.add(item["id"])
            cited(item, f"{list_key}[{i}]")
    covered = {d.get("covers_recommendation") for d in doc["disclosures"]}
    rec_ids = {r.get("id") for r in doc["recommendations"] if text(r.get("id"))}
    for recommendation in doc["recommendations"]:
        required(recommendation, ("summary",), f"recommendation {recommendation.get('id')}")
        for flag in ("requires_disclosure", "requires_suitability_review"):
            if not isinstance(recommendation.get(flag), bool):
                warnings.append(f"recommendation {recommendation.get('id')}: {flag} must be explicitly reviewed")
        if recommendation.get("requires_disclosure") and recommendation.get("id") not in covered:
            warnings.append(f"recommendation {recommendation.get('id')}: required disclosure missing")
    for disclosure in doc["disclosures"]:
        required(disclosure, ("ref",), f"disclosure {disclosure.get('id')}")
        if disclosure.get("covers_recommendation") not in rec_ids:
            warnings.append(f"disclosure {disclosure.get('id')}: unknown recommendation")
    not_applicable = doc.get("not_applicable", {})
    if not isinstance(not_applicable, dict):
        errors.append("not_applicable must be an object")
        not_applicable = {}
    def absent_mode(key):
        reason = not_applicable.get(key)
        if not isinstance(reason, dict):
            warnings.append(f"{key}: missing content or cited not-applicable reason")
        else:
            required(reason, ("reason",), f"not_applicable.{key}")
    if not doc["action_items"]:
        absent_mode("action-items")
    for action in doc["action_items"]:
        required(action, ("owner", "description", "due_date"), f"action {action.get('id')}")
        if not iso(action.get("due_date")):
            warnings.append(f"action {action.get('id')}: due_date must be an ISO date")
    communication = doc["client_communication"]
    required(communication, ("channel", "subject"), "client_communication")
    if communication.get("channel") not in CHANNELS:
        errors.append("client_communication.channel must be email, letter or portal")
    points = communication.get("key_points")
    if not isinstance(points, list) or not points or any(not isinstance(x, dict) for x in points):
        errors.append("client_communication.key_points must be a nonempty list of {text,citation} objects")
    else:
        for i, point in enumerate(points):
            required(point, ("text",), f"client_communication.key_points[{i}]")
    fields = doc["crm_update"].get("fields")
    if not isinstance(fields, list) or any(not isinstance(x, dict) for x in fields):
        errors.append("crm_update.fields must be a list of objects")
    elif not fields:
        absent_mode("crm-update")
    else:
        for i, item in enumerate(fields):
            required(item, ("field",), f"crm_update.fields[{i}]")
            if "proposed_value" not in item or item["proposed_value"] in (None, ""):
                warnings.append(f"crm_update.fields[{i}]: proposed_value is required")
    if not doc["next_meeting"]:
        absent_mode("next-meeting")
    else:
        required(doc["next_meeting"], ("target_timeframe", "purpose"), "next_meeting")
    for approval in doc["approvals"]:
        if approval.get("status") != "pending":
            errors.append("input approvals must remain pending; decisions are outside this draft")
    return errors, sorted(set(warnings))

def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/followup_request_example.json" if "--selftest" in argv else None
    doc = json.loads(path.read_text() if path else Path(argv[0]).read_text() if argv else sys.stdin.read())
    errors, warnings = validate(doc)
    for row in warnings:
        print("WARN", row)
    for row in errors:
        print("ERROR", row)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return bool(errors)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
