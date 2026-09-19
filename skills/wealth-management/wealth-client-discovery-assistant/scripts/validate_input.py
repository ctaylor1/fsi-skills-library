#!/usr/bin/env python3
"""Validate discovery structure; material gaps are findings in the assembled fact-find."""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path
from wealth_contract import validate_envelope, source_errors, nonempty, iso_date

AREAS = ("assets", "liabilities", "income", "expenses", "tax-context", "family", "estate", "protection")
ROLES = {"client", "spouse", "partner", "dependent", "trustee", "entity-representative", "other"}

def validate(doc):
    errors = validate_envelope(doc)
    if errors:
        return errors
    for key in ("household", "engagement_details"):
        if not isinstance(doc.get(key), dict):
            errors.append(f"{key} must be an object")
    for key in ("members", "facts", "goals", "coverage"):
        if not isinstance(doc.get(key), list) or any(not isinstance(x, dict) for x in doc[key]):
            errors.append(f"{key} must be a list of objects")
    return errors

def findings(doc):
    result = []
    def add(code, message, path):
        result.append({"code": code, "message": message, "path": path})
    def cited(item, path):
        for error in source_errors(item.get("source_ids"), doc):
            add("evidence-gap", error, path)
    def required(item, fields, path):
        for key in fields:
            if not nonempty(item.get(key)):
                add("missing-fact", f"{key} must be supplied from evidence", f"{path}.{key}")
        cited(item, path)
    required(doc["household"], ("display_name",), "household")
    required(doc["engagement_details"], ("service_scope", "relationship_status"), "engagement_details")
    if doc["engagement_details"].get("relationship_status") not in {"prospect", "existing-client"}:
        add("engagement-gap", "relationship_status must be prospect or existing-client", "engagement_details")
    # Capacity is a documented intake assertion, not a finding that a legal standard applies.
    for error in source_errors(doc["engagement"].get("source_ids"), doc):
        add("engagement-evidence-gap", error, "engagement")
    member_ids = set()
    if not doc["members"]:
        add("missing-members", "Household member or entity-representative details have not been collected", "members")
    for index, member in enumerate(doc["members"]):
        path = f"members[{index}]"
        required(member, ("member_id", "name_masked", "role"), path)
        mid = member.get("member_id")
        if nonempty(mid):
            if mid in member_ids:
                add("duplicate-member", f"Duplicate member_id {mid}", path)
            member_ids.add(mid)
        if not nonempty(member.get("role")) or member["role"] not in ROLES:
            add("member-role-gap", "Member role needs clarification", path)
    fact_ids, collected = set(), set()
    for index, fact in enumerate(doc["facts"]):
        path = f"facts[{index}]"
        required(fact, ("fact_id", "subject_id", "area", "label", "evidence_status"), path)
        fid = fact.get("fact_id")
        if nonempty(fid):
            if fid in fact_ids:
                add("duplicate-fact", f"Duplicate fact_id {fid}", path)
            fact_ids.add(fid)
        if not nonempty(fact.get("subject_id")) or fact["subject_id"] not in member_ids | {doc["household_id"]}:
            add("unknown-subject", "Fact references an unconfirmed household/member", path)
        if not nonempty(fact.get("area")) or fact["area"] not in AREAS:
            add("unsupported-area", "Fact area is outside the discovery contract", path)
        else:
            collected.add(fact["area"])
        value = fact.get("value")
        if value is None or (isinstance(value, str) and not value.strip()) or isinstance(value, (dict, list, bool)):
            add("missing-value", "Supply a substantive text or numeric value; unknown is not zero", path)
        elif isinstance(value, (int, float)) and (not math.isfinite(value) or value < 0):
            add("invalid-value", "Discovery amounts must be finite and nonnegative", path)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            currency = fact.get("currency")
            if not nonempty(currency) or len(currency) != 3 or not currency.isupper() or not currency.isalpha():
                add("currency-gap", "Numeric amounts require an explicit three-letter currency", path)
            if fact.get("area") in ("income", "expenses") and fact.get("period") not in ("monthly", "annual", "one-time"):
                add("period-gap", "Income and expense amounts require an explicit period", path)
        if not nonempty(fact.get("evidence_status")) or fact["evidence_status"] not in {"client-reported", "documented"}:
            add("evidence-status-gap", "Distinguish client-reported facts from documented facts", path)
    goal_ids = set()
    if not doc["goals"]:
        add("missing-goals", "No client goals have been documented", "goals")
    for index, goal in enumerate(doc["goals"]):
        path = f"goals[{index}]"
        required(goal, ("goal_id", "description", "subject_id"), path)
        gid = goal.get("goal_id")
        if nonempty(gid):
            if gid in goal_ids:
                add("duplicate-goal", f"Duplicate goal_id {gid}", path)
            goal_ids.add(gid)
        if not nonempty(goal.get("subject_id")) or goal["subject_id"] not in member_ids | {doc["household_id"]}:
            add("unknown-subject", "Goal references an unconfirmed household/member", path)
        if "priority" in goal and (not isinstance(goal["priority"], int) or isinstance(goal["priority"], bool) or not 1 <= goal["priority"] <= 5):
            add("priority-gap", "Supplied goal priority must be an integer from 1 through 5", path)
        if "target_date" in goal and iso_date(goal["target_date"]) is None:
            add("goal-date-gap", "Supplied target_date must be YYYY-MM-DD", path)
        if "target_amount" in goal:
            amount = goal["target_amount"]
            if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not math.isfinite(amount) or amount < 0:
                add("goal-amount-gap", "Supplied target_amount must be finite and nonnegative", path)
            currency = goal.get("currency")
            if not nonempty(currency) or len(currency) != 3 or not currency.isupper() or not currency.isalpha():
                add("currency-gap", "Goal amounts require an explicit three-letter currency", path)
    covered = set()
    for index, row in enumerate(doc["coverage"]):
        path = f"coverage[{index}]"
        required(row, ("area", "status", "note"), path)
        area, status = row.get("area"), row.get("status")
        if not nonempty(area) or area not in AREAS or area in covered:
            add("coverage-gap", "Coverage area must be supported and unique", path)
        if isinstance(area, str):
            covered.add(area)
        if not nonempty(status) or status not in {"provided", "none-reported", "not-collected"}:
            add("coverage-gap", "Coverage status needs clarification", path)
        elif status == "not-collected":
            add("not-collected", f"{area} evidence has not been collected", path)
        elif status == "provided" and area not in collected:
            add("coverage-gap", "Coverage says provided but no corresponding fact exists", path)
        elif status == "none-reported" and area in collected:
            add("coverage-conflict", "Coverage says none-reported but facts are present", path)
    for area in AREAS:
        if area not in covered:
            add("coverage-gap", f"Record whether {area} was collected; absence is not none", "coverage")
    return result

def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/discovery_request.json" if "--selftest" in argv else None
    doc = json.loads(path.read_text() if path else Path(argv[0]).read_text() if argv else sys.stdin.read())
    errors = validate(doc)
    for error in errors:
        print("ERROR", error)
    gaps = [] if errors else findings(doc)
    print(f"input validation: {len(errors)} error(s), {len(gaps)} material gap(s)")
    return bool(errors)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
