#!/usr/bin/env python3
"""Deterministic input validation for data-quality-issue-investigator.

Validates a data-quality issue file before investigation. Fails closed on structural
problems; warns on data gaps that force a `needs-data` disposition (the investigator must
not profile a defect by guessing missing counts or consumers).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, open_cases[], issues[
    {issue_id, dataset_id, field, rule_id, defect_type, period{from,to}, total_records,
     failing_records, data_classification, consumers{regulatory_reports[], internal_reports[],
     models[{id,materiality}], regulated_decisions[]}, prior_issues_90d, upstream_suspected,
     owners{data_owner,steward,upstream_owner}, monetary_exposure, events[{ts,type,ref}],
     record_keys[], source_ref}]

Usage: python validate_input.py dq_issues.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "issues")
REQUIRED_ISSUE = ("issue_id", "dataset_id", "rule_id", "period", "source_ref")
CLASSIFICATIONS = {"Restricted", "Confidential", "Internal", "Public"}
DEFECT_TYPES = {"completeness", "validity", "uniqueness", "consistency", "timeliness", "accuracy"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    issues = doc.get("issues") or []
    if not isinstance(issues, list) or not issues:
        errors.append("issues must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, it in enumerate(issues):
        tag = f"issues[{i}] ({it.get('issue_id','?')})"
        for k in REQUIRED_ISSUE:
            if k not in it or it[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        iid = it.get("issue_id")
        if iid in ids:
            errors.append(f"{tag}: duplicate issue_id")
        ids.add(iid)
        # period is a {from, to} object (the engine stores and compares it as a whole); a
        # scalar (or any non-object) must fail closed with a clean error, never crash on
        # attribute access.
        per = it.get("period")
        if not isinstance(per, dict):
            errors.append(f"{tag}: period must be an object with 'from' and 'to'")
        elif not (per.get("from") and per.get("to")):
            errors.append(f"{tag}: period requires 'from' and 'to'")
        # structural sanity: failing cannot exceed total when both present
        tot, fail = it.get("total_records"), it.get("failing_records")
        if isinstance(tot, (int, float)) and isinstance(fail, (int, float)) and fail > tot:
            errors.append(f"{tag}: failing_records ({fail}) exceeds total_records ({tot})")

        # data-gap warnings that force needs-data (never guess to profile a defect)
        if it.get("defect_type") not in DEFECT_TYPES:
            warnings.append(f"{tag}: defect_type missing/invalid -> needs-data")
        if not isinstance(tot, (int, float)) or not isinstance(fail, (int, float)):
            warnings.append(f"{tag}: total_records/failing_records missing -> cannot quantify impact (needs-data)")
        cls = it.get("data_classification")
        if cls is not None and cls not in CLASSIFICATIONS:
            warnings.append(f"{tag}: data_classification '{cls}' not recognized -> treated as Internal")
        if not it.get("consumers"):
            warnings.append(f"{tag}: no consumers listed -> downstream impact cannot be assessed")
        if not it.get("events"):
            warnings.append(f"{tag}: no events -> chronology will be empty")
    if doc.get("open_cases") is None:
        warnings.append("no open_cases provided -> duplicate detection limited")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "dq_issues_example.json"
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
