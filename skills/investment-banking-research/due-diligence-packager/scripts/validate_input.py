#!/usr/bin/env python3
"""Deterministic input validation for due-diligence-packager.

Validates a data-room extraction manifest before packaging. Fails closed on structural
problems; warns on data-quality gaps (unsupported claims, missing confidence, missing
approvals) that will force exclusions or a `needs-source` disposition downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  deal{deal_id, project_codename, target_name_masked, as_of_date}, freshness_window_days,
  sources[{doc_id, title, type, date, version, owner, index_ref}],
  extractions[{field, value, unit, workstream, source_doc, page, confidence}],
  issues[{issue_id, category, severity, description, source_doc, status}],
  open_questions[{q_id, topic, question, owner, priority}], model_targets[],
  approvals[{role, name_masked, status, date}]

Usage: python validate_input.py dataroom.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("deal", "sources", "extractions")
REQUIRED_DEAL = ("deal_id", "as_of_date")
REQUIRED_SOURCE = ("doc_id", "title", "type", "index_ref")
REQUIRED_EXTRACTION = ("field", "source_doc")
REQUIRED_ISSUE = ("issue_id", "severity", "source_doc")
SEVERITY = {"high", "medium", "low"}
CONFIDENCE = {"high", "medium", "low"}
KNOWN_MODEL_TARGETS = {
    "three-statement-model-builder", "dcf-modeler", "lbo-model-builder",
    "merger-model-builder", "comps-analysis-builder", "scenario-sensitivity-generator",
}
REQUIRED_APPROVAL_ROLES = {"diligence_lead", "quality_reviewer"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    deal = doc.get("deal") or {}
    if not isinstance(deal, dict):
        errors.append("deal must be an object")
    else:
        for k in REQUIRED_DEAL:
            if not deal.get(k):
                errors.append(f"deal: missing '{k}'")

    sources = doc.get("sources") or []
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        return errors, warnings

    doc_ids: set[str] = set()
    for i, s in enumerate(sources):
        tag = f"sources[{i}] ({s.get('doc_id','?')})"
        for k in REQUIRED_SOURCE:
            if not s.get(k):
                errors.append(f"{tag}: missing '{k}'")
        did = s.get("doc_id")
        if did in doc_ids:
            errors.append(f"{tag}: duplicate doc_id")
        doc_ids.add(did)

    extractions = doc.get("extractions") or []
    if not isinstance(extractions, list) or not extractions:
        errors.append("extractions must be a non-empty list")
        return errors, warnings

    for i, e in enumerate(extractions):
        tag = f"extractions[{i}] ({e.get('field','?')})"
        for k in REQUIRED_EXTRACTION:
            if e.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if e.get("value") in (None, ""):
            warnings.append(f"{tag}: no value -> will be flagged low-signal")
        if e.get("source_doc") and e.get("source_doc") not in doc_ids:
            warnings.append(f"{tag}: source_doc '{e.get('source_doc')}' not in source index -> UNSUPPORTED CLAIM (will be excluded, needs-source)")
        if not e.get("page"):
            warnings.append(f"{tag}: missing page -> citation will be weak")
        if e.get("confidence") not in CONFIDENCE:
            warnings.append(f"{tag}: confidence missing/invalid -> defaults to 'low'")

    seen_iss: set[str] = set()
    for i, iss in enumerate(doc.get("issues") or []):
        tag = f"issues[{i}] ({iss.get('issue_id','?')})"
        for k in REQUIRED_ISSUE:
            if iss.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        iid = iss.get("issue_id")
        if iid in seen_iss:
            errors.append(f"{tag}: duplicate issue_id")
        seen_iss.add(iid)
        if iss.get("severity") and iss.get("severity") not in SEVERITY:
            errors.append(f"{tag}: invalid severity {iss.get('severity')!r}")
        if iss.get("source_doc") and iss.get("source_doc") not in doc_ids:
            warnings.append(f"{tag}: source_doc '{iss.get('source_doc')}' not in source index -> UNSUPPORTED CLAIM (will be excluded)")

    if doc.get("open_questions") is None:
        warnings.append("no open_questions provided -> pack will have an empty open-items list")

    targets = doc.get("model_targets") or []
    for t in targets:
        if t not in KNOWN_MODEL_TARGETS:
            errors.append(f"model_targets: '{t}' is not a known modeling skill (invalid handoff)")

    approvals = doc.get("approvals") or []
    roles = {a.get("role") for a in approvals if isinstance(a, dict)}
    missing_roles = REQUIRED_APPROVAL_ROLES - roles
    if missing_roles:
        warnings.append(f"approvals ledger missing required role(s): {', '.join(sorted(missing_roles))} -> record before external delivery")

    return errors, warnings


def main(argv) -> int:
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "dataroom_example.json"
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
