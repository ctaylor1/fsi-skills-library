#!/usr/bin/env python3
"""Deterministic input validation for investment-banking-pitch-builder.

Validates a pitch build request before assembly. Fails closed on structural problems (a
draft cannot be assembled without a template contract and pages); warns on completeness,
source, and approval gaps that will force a `hold-for-approval` delivery status.

Input schema (JSON): see references/source-map.md. Key fields:
  engagement_id, template{template_id, version, required_sections[]},
  deal_context{client_name, mandate_type, ...}, required_approvals[],
  approvals[{role, status, approver, date}], pages[
    {page_id, section, title, source_component, takeaway, claims[{text, source_ref,
     approved}], sources[], approval{status, approver, date}}]

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("engagement_id", "template", "deal_context", "required_approvals", "pages")
REQUIRED_TEMPLATE = ("template_id", "version", "required_sections")
REQUIRED_PAGE = ("page_id", "section", "title", "takeaway")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    tmpl = doc.get("template") or {}
    for k in REQUIRED_TEMPLATE:
        if k not in tmpl or tmpl[k] in (None, "", []):
            errors.append(f"template: missing '{k}' (the approved template is a versioned contract)")
    required_sections = tmpl.get("required_sections") or []
    if not isinstance(required_sections, list) or not required_sections:
        errors.append("template.required_sections must be a non-empty list")

    dc = doc.get("deal_context") or {}
    for k in ("client_name", "mandate_type"):
        if not dc.get(k):
            errors.append(f"deal_context: missing '{k}'")

    pages = doc.get("pages") or []
    if not isinstance(pages, list) or not pages:
        errors.append("pages must be a non-empty list")
        return errors, warnings

    ids: set = set()
    covered: set = set()
    for i, p in enumerate(pages):
        tag = f"pages[{i}] ({p.get('page_id','?')})"
        for k in REQUIRED_PAGE:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        pid = p.get("page_id")
        if pid in ids:
            errors.append(f"{tag}: duplicate page_id")
        ids.add(pid)
        covered.add(p.get("section"))

        if not p.get("sources"):
            warnings.append(f"{tag}: no source citation -> page will be marked needs-source")
        for j, c in enumerate(p.get("claims") or []):
            if not c.get("source_ref"):
                warnings.append(f"{tag}: claim[{j}] has no source_ref -> unsupported assertion (hold-for-approval)")
            elif c.get("approved") is not True:
                warnings.append(f"{tag}: claim[{j}] source not approved -> unapproved assertion (hold-for-approval)")
        appr = p.get("approval") or {}
        if appr.get("status") != "approved":
            warnings.append(f"{tag}: content approval status is {appr.get('status')!r} -> needs-approval")

    for sec in required_sections:
        if sec not in covered:
            warnings.append(f"required section '{sec}' has no page -> completeness gap (hold-for-approval)")

    approvals = {a.get("role"): a.get("status") for a in (doc.get("approvals") or [])}
    for role in doc.get("required_approvals") or []:
        if role not in approvals:
            warnings.append(f"required approval '{role}' not recorded -> hold-for-approval")
        elif approvals[role] != "approved":
            warnings.append(f"required approval '{role}' status is {approvals[role]!r} -> hold-for-approval")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pitch_request_example.json"
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
