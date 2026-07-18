#!/usr/bin/env python3
"""Deterministic input validation for policy-document-assistant.

Validates a policy build request before a controlled policy/procedure is drafted. Fails
closed on structural problems; warns on data gaps that would produce an unsupported clause
or a limited change summary.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, approvals_required[], prior_version_ref,
  requirements_register[{req_id, text, source, owner, status}],
  policy{policy_id, title, policy_type, tier, current_version, change_type, owner,
         classification, last_review_date, proposed_effective_date,
         clauses[{clause_id, heading, section_id, text, normative, req_ids[]}],
         prior_clauses[{clause_id, text}]}

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "requirements_register", "policy")
REQUIRED_POLICY = ("policy_id", "title", "policy_type", "current_version", "change_type",
                   "owner", "clauses")
POLICY_TYPES = {"policy", "procedure", "standard"}
CHANGE_TYPES = {"major", "minor", "editorial"}
TIERS = {"tier-1", "tier-2", "tier-3"}
REQ_STATUS_OK = {"approved"}
VERSION_RE = re.compile(r"^\d+\.\d+$")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    reg = doc.get("requirements_register") or []
    if not isinstance(reg, list) or not reg:
        errors.append("requirements_register must be a non-empty list")
    reg_by_id: dict[str, dict] = {}
    for i, r in enumerate(reg if isinstance(reg, list) else []):
        rid = r.get("req_id")
        if not rid:
            errors.append(f"requirements_register[{i}]: missing 'req_id'")
            continue
        if rid in reg_by_id:
            errors.append(f"requirements_register[{i}]: duplicate req_id {rid!r}")
        reg_by_id[rid] = r
        if not r.get("source"):
            warnings.append(f"req {rid}: missing 'source' -> clauses citing it will be unsupported")
        if r.get("status") not in REQ_STATUS_OK:
            warnings.append(f"req {rid}: status {r.get('status')!r} not 'approved' -> not citable")

    pol = doc.get("policy") or {}
    if not isinstance(pol, dict):
        errors.append("'policy' must be a mapping")
        return errors, warnings
    for k in REQUIRED_POLICY:
        if k not in pol or pol[k] in (None, "", []):
            errors.append(f"policy: missing '{k}'")

    if pol.get("policy_type") and pol["policy_type"] not in POLICY_TYPES:
        errors.append(f"policy.policy_type {pol.get('policy_type')!r} not in {sorted(POLICY_TYPES)}")
    if pol.get("change_type") and pol["change_type"] not in CHANGE_TYPES:
        errors.append(f"policy.change_type {pol.get('change_type')!r} not in {sorted(CHANGE_TYPES)}")
    if pol.get("current_version") and not VERSION_RE.match(str(pol["current_version"])):
        errors.append(f"policy.current_version {pol.get('current_version')!r} must match 'X.Y'")
    if pol.get("tier") and pol["tier"] not in TIERS:
        warnings.append(f"policy.tier {pol.get('tier')!r} unknown -> conservative 12-month review interval applied")
    if not pol.get("proposed_effective_date"):
        warnings.append("policy.proposed_effective_date missing -> next-review date cannot be computed")
    if not pol.get("last_review_date"):
        warnings.append("policy.last_review_date missing -> review-history section will be incomplete")

    clauses = pol.get("clauses") or []
    if not isinstance(clauses, list) or not clauses:
        errors.append("policy.clauses must be a non-empty list")
        return errors, warnings

    seen = set()
    for i, c in enumerate(clauses):
        tag = f"clauses[{i}] ({c.get('clause_id','?')})"
        for k in ("clause_id", "heading", "section_id", "text"):
            if not c.get(k):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("clause_id")
        if cid in seen:
            errors.append(f"{tag}: duplicate clause_id")
        seen.add(cid)
        if c.get("normative"):
            req_ids = c.get("req_ids") or []
            if not req_ids:
                warnings.append(f"{tag}: normative clause with no req_ids -> unsupported assertion")
            for rid in req_ids:
                if rid not in reg_by_id:
                    warnings.append(f"{tag}: cites req {rid!r} not in register -> unsupported assertion")
                elif reg_by_id[rid].get("status") not in REQ_STATUS_OK:
                    warnings.append(f"{tag}: cites req {rid!r} whose status is not 'approved' -> unsupported")

    if pol.get("change_type") in {"minor", "major"} and not (pol.get("prior_clauses") or doc.get("prior_version_ref")):
        warnings.append("no prior_clauses/prior_version_ref -> change summary (diff) will be limited")
    if not doc.get("approvals_required"):
        warnings.append("no approvals_required -> approval slots default to owner/legal/compliance")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "policy_request_example.json"
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
