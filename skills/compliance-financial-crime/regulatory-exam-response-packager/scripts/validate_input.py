#!/usr/bin/env python3
"""Deterministic input validation for regulatory-exam-response-packager.

Validates an exam/inquiry request set before a response package is assembled. Fails closed on
structural problems; warns on data gaps that will surface as `gap`, `needs-evidence`, or
`unsupported-assertion` items in the draft package (surfaced, never hidden).

Input schema (JSON): see references/source-map.md. Key fields:
  package_version, exam{exam_id, regulator, scope, period{from,to}},
  required_approver_roles[], requests[
    {request_id, prompt, category, evidence_required, due_date}],
  responses[
    {request_id, narrative, assertions[{assertion_id, text, source_ref}],
     evidence[{evidence_id, description, source_ref, classification}],
     issue_status, approvals[{role, approver_id, status, date}]}]

Usage: python validate_input.py exam_requests.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("package_version", "exam", "requests")
REQUIRED_EXAM = ("exam_id", "regulator", "period")
REQUIRED_REQUEST = ("request_id", "prompt", "category")
CATEGORIES = {"document", "information", "question", "finding-response"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    exam = doc.get("exam") or {}
    for k in REQUIRED_EXAM:
        if not exam.get(k):
            errors.append(f"exam: missing '{k}'")
    per = exam.get("period") or {}
    if not (per.get("from") and per.get("to")):
        errors.append("exam.period requires 'from' and 'to'")

    requests = doc.get("requests") or []
    if not isinstance(requests, list) or not requests:
        errors.append("requests must be a non-empty list")
        return errors, warnings

    req_ids = set()
    for i, r in enumerate(requests):
        tag = f"requests[{i}] ({r.get('request_id', '?')})"
        for k in REQUIRED_REQUEST:
            if not r.get(k):
                errors.append(f"{tag}: missing '{k}'")
        rid = r.get("request_id")
        if rid in req_ids:
            errors.append(f"{tag}: duplicate request_id")
        req_ids.add(rid)
        if r.get("category") not in CATEGORIES:
            errors.append(f"{tag}: category {r.get('category')!r} not in {sorted(CATEGORIES)}")
        if "evidence_required" not in r:
            warnings.append(f"{tag}: evidence_required not set -> defaulting to true")

    if not doc.get("required_approver_roles"):
        warnings.append("required_approver_roles empty -> no approval gate can be enforced")

    responses = doc.get("responses") or []
    resp_ids = set()
    for i, resp in enumerate(responses):
        rid = resp.get("request_id")
        tag = f"responses[{i}] ({rid or '?'})"
        if not rid:
            errors.append(f"{tag}: missing request_id")
            continue
        if rid not in req_ids:
            errors.append(f"{tag}: response for unknown request_id {rid!r} (orphan)")
        if rid in resp_ids:
            errors.append(f"{tag}: duplicate response for request_id {rid!r}")
        resp_ids.add(rid)
        for j, a in enumerate(resp.get("assertions") or []):
            if not a.get("assertion_id") or not a.get("text"):
                errors.append(f"{tag}: assertions[{j}] missing assertion_id/text")
            if not a.get("source_ref"):
                warnings.append(f"{tag}: assertion {a.get('assertion_id', '?')} has no source_ref -> unsupported-assertion")
        for j, e in enumerate(resp.get("evidence") or []):
            if not e.get("evidence_id") or not e.get("description"):
                errors.append(f"{tag}: evidence[{j}] missing evidence_id/description")
            if not e.get("source_ref"):
                errors.append(f"{tag}: evidence {e.get('evidence_id', '?')} missing source_ref (provenance required)")

    for rid in req_ids - resp_ids:
        warnings.append(f"request {rid} has no response -> will be a gap in the package")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exam_requests_example.json"
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
