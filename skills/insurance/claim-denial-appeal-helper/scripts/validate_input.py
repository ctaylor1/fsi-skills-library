#!/usr/bin/env python3
"""Deterministic input validation for claim-denial-appeal-helper.

Validates a de-identified denial bundle before the appeal work-product is computed. Fails
closed on structural problems; warns on data-quality gaps that limit the package (missing
supporting documents, an already-closed appeal window, an unmasked member id, etc.).

Input schema (JSON): see references/source-map.md. Key fields:
  claim_id, member_id, plan_id, as_of (YYYY-MM-DD), denial_date (YYYY-MM-DD),
  appeal_window_days (int), appeal_level, denial_reasons[{code, description, source_ref}],
  documents_available[{doc_type, source_ref, date}], policy_refs[{provision, source_ref}],
  config{...overrides...}

Usage:
  python validate_input.py denial.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("claim_id", "as_of", "denial_date", "appeal_window_days",
                "denial_reasons", "documents_available")
KNOWN_REASONS = {
    "not_medically_necessary", "experimental_investigational", "out_of_network",
    "prior_authorization_missing", "coding_error", "benefit_exclusion",
    "not_covered_service", "timely_filing", "duplicate_claim",
    "coordination_of_benefits", "eligibility",
}


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    for field in ("as_of", "denial_date"):
        if not DATE_RE.match(str(doc[field])):
            errors.append(f"{field} must be YYYY-MM-DD, got {doc[field]!r}")

    window = _int(doc["appeal_window_days"])
    if window is None or window <= 0:
        errors.append(f"appeal_window_days must be a positive integer, got {doc['appeal_window_days']!r}")

    reasons = doc.get("denial_reasons") or []
    if not isinstance(reasons, list) or not reasons:
        errors.append("denial_reasons must be a non-empty list")
    else:
        for i, r in enumerate(reasons):
            tag = f"denial_reasons[{i}]"
            if not r.get("code"):
                errors.append(f"{tag}: missing 'code'")
            elif r["code"] not in KNOWN_REASONS:
                warnings.append(f"{tag}: unknown reason code {r['code']!r} — generic evidence checklist will be used")
            if not r.get("source_ref"):
                warnings.append(f"{tag}: no source_ref — cite the denial notice/EOB line for this reason")

    docs = doc.get("documents_available")
    if not isinstance(docs, list):
        errors.append("documents_available must be a list")
    else:
        for i, d in enumerate(docs):
            if not d.get("doc_type"):
                errors.append(f"documents_available[{i}]: missing 'doc_type'")
            if not d.get("source_ref"):
                warnings.append(f"documents_available[{i}]: no source_ref — evidence citation will be incomplete")
        if not docs:
            warnings.append("no documents_available — every supporting item will be reported as a gap")

    if errors:
        return errors, warnings

    # Data-quality / freshness warnings (do not block).
    if DATE_RE.match(str(doc["as_of"])) and DATE_RE.match(str(doc["denial_date"])):
        from datetime import datetime, timedelta
        as_of = datetime.strptime(doc["as_of"], "%Y-%m-%d")
        denial = datetime.strptime(doc["denial_date"], "%Y-%m-%d")
        if as_of < denial:
            warnings.append("as_of precedes denial_date — check the dates")
        if window:
            deadline = denial + timedelta(days=window)
            if as_of > deadline:
                warnings.append("appeal window appears to have closed — flag the deadline prominently and confirm any exception")
            elif (deadline - as_of).days <= 30:
                warnings.append("appeal deadline is within 30 days — treat as time-sensitive")

    mid = str(doc.get("member_id", ""))
    if mid and "*" not in mid and re.search(r"\d{5,}", mid):
        warnings.append("member_id may be unmasked — mask to the last 4 digits before drafting")
    if not doc.get("policy_refs"):
        warnings.append("no policy_refs — supporting policy provisions will be absent from the argument scaffold")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "denial_example.json"
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
