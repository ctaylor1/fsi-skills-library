#!/usr/bin/env python3
"""Deterministic input validation for buyer-investor-list-builder.

Validates a buyer-universe intake before list building. Fails closed on structural problems;
warns on data-quality gaps (missing scoring fields, unsupported rationale, restricted/conflict
flags, missing approvals) that will force a `needs-data`, `needs-source`, or
`hold-conflicts-review` disposition downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  mandate{mandate_id, project_codename, target_name_masked, process_type, as_of_date,
    deal_size_band}, freshness_window_days, restricted_list[], existing_list[{entity_id,
    prior_ref}], sources[{doc_id, title, type, date, version, owner, index_ref}],
  candidates[{candidate_id, entity_id, name_masked, buyer_type, sector_fit, size_fit, geo_fit,
    mandate_fit, precedent_activity, relationship, conflict_flag, restricted,
    rationale[{claim, source_doc, page}], source_ref}],
  approvals[{role, name_masked, status, date}]

Usage: python validate_input.py buyer_universe.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("mandate", "sources", "candidates")
REQUIRED_MANDATE = ("mandate_id", "as_of_date")
REQUIRED_SOURCE = ("doc_id", "title", "type", "index_ref")
REQUIRED_CANDIDATE = ("candidate_id", "name_masked")
BUYER_TYPES = {"strategic", "sponsor", "lender", "investor"}
SECTOR = {"strong", "moderate", "weak"}
SIZE = {"high", "medium", "low"}
REL = {"strong", "some", "none"}
REQUIRED_APPROVAL_ROLES = {"deal_lead", "conflicts_reviewer"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    mandate = doc.get("mandate") or {}
    if not isinstance(mandate, dict):
        errors.append("mandate must be an object")
    else:
        for k in REQUIRED_MANDATE:
            if not mandate.get(k):
                errors.append(f"mandate: missing '{k}'")

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

    candidates = doc.get("candidates") or []
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidates must be a non-empty list")
        return errors, warnings

    restricted_ids = set(doc.get("restricted_list") or [])
    seen: set[str] = set()
    for i, c in enumerate(candidates):
        tag = f"candidates[{i}] ({c.get('candidate_id','?')})"
        for k in REQUIRED_CANDIDATE:
            if c.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("candidate_id")
        if cid in seen:
            errors.append(f"{tag}: duplicate candidate_id")
        seen.add(cid)

        # scoring-field data quality -> needs-data downstream (warn, do not guess)
        if c.get("buyer_type") not in BUYER_TYPES:
            warnings.append(f"{tag}: buyer_type missing/invalid -> needs-data")
        if c.get("sector_fit") not in SECTOR:
            warnings.append(f"{tag}: sector_fit missing/invalid -> needs-data")
        if c.get("size_fit") not in SIZE:
            warnings.append(f"{tag}: size_fit missing/invalid -> needs-data")
        if c.get("relationship") is not None and c.get("relationship") not in REL:
            warnings.append(f"{tag}: relationship {c.get('relationship')!r} not in {sorted(REL)} -> treated as 'none'")

        # rationale sourcing -> unsupported claims are excluded downstream
        rationale = c.get("rationale") or []
        if not rationale:
            warnings.append(f"{tag}: no rationale -> will be flagged needs-source (excluded from waves)")
        supported = 0
        for r in rationale:
            sd = r.get("source_doc")
            if sd and sd not in doc_ids:
                warnings.append(f"{tag}: rationale source_doc '{sd}' not in source index -> UNSUPPORTED CLAIM (excluded)")
            elif sd:
                supported += 1
        if rationale and supported == 0:
            warnings.append(f"{tag}: no rationale claim resolves to an indexed source -> needs-source")

        # restricted / conflict screen -> hold-conflicts-review downstream
        if bool(c.get("restricted")) or c.get("entity_id") in restricted_ids:
            warnings.append(f"{tag}: on the restricted list -> hold-conflicts-review (excluded from active waves)")
        if bool(c.get("conflict_flag")):
            warnings.append(f"{tag}: unresolved conflict flag -> hold-conflicts-review (excluded from active waves)")

    if doc.get("existing_list") is None:
        warnings.append("no existing_list provided -> duplicate detection against prior outreach is limited")

    approvals = doc.get("approvals") or []
    roles = {a.get("role") for a in approvals if isinstance(a, dict)}
    missing_roles = REQUIRED_APPROVAL_ROLES - roles
    if missing_roles:
        warnings.append(f"approvals ledger missing required role(s): {', '.join(sorted(missing_roles))} -> record before external delivery")

    return errors, warnings


def main(argv) -> int:
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "buyer_universe_example.json"
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
