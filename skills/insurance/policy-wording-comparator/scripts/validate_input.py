#!/usr/bin/env python3
"""Deterministic input validation for policy-wording-comparator.

Validates a comparison request (subject form vs baseline form) before clause alignment. Fails
closed on structural problems; warns on data-quality gaps that limit which checks are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  as_of (YYYY-MM-DD), config_version, required_clause_types[] (optional),
  config{material_text_change, material_types[], escalation_types[]} (optional),
  subject_form / baseline_form each:
    {form_id, form_name, filing_status, edition_date?, clauses[
       {clause_id, clause_type, text, source_ref, heading?, section?, defines[]?, references[]?}]}

Usage:
  python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "config_version", "subject_form", "baseline_form")
REQUIRED_FORM = ("form_id", "form_name", "filing_status", "clauses")
REQUIRED_CLAUSE = ("clause_id", "clause_type", "text", "source_ref")
FILING_STATUS = {"filed", "approved", "draft", "manuscript", "proposed"}
OF_RECORD = {"filed", "approved"}


def _validate_form(doc: dict, side: str, errors: list, warnings: list) -> None:
    form = doc.get(side)
    if not isinstance(form, dict):
        errors.append(f"{side}: must be an object")
        return
    for k in REQUIRED_FORM:
        if k not in form or form[k] in (None, ""):
            errors.append(f"{side}: missing '{k}'")
    if form.get("filing_status") and form["filing_status"] not in FILING_STATUS:
        errors.append(f"{side}: filing_status {form['filing_status']!r} not in {sorted(FILING_STATUS)}")
    clauses = form.get("clauses")
    if not isinstance(clauses, list) or not clauses:
        errors.append(f"{side}: clauses must be a non-empty list")
        return
    ids, no_heading, no_refs_meta = set(), 0, 0
    for i, c in enumerate(clauses):
        tag = f"{side}.clauses[{i}] ({c.get('clause_id','?')})"
        for k in REQUIRED_CLAUSE:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("clause_id")
        if cid in ids:
            errors.append(f"{tag}: duplicate clause_id within {side}")
        ids.add(cid)
        if not c.get("heading"):
            no_heading += 1
        if "references" not in c and "defines" not in c:
            no_refs_meta += 1
    if no_heading:
        warnings.append(f"{side}: {no_heading} clause(s) without a heading — alignment falls back to clause_id only")
    if no_refs_meta == len(clauses):
        warnings.append(f"{side}: no clause carries 'references'/'defines' — dangling-reference (conflict) check is not evaluable")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    _validate_form(doc, "subject_form", errors, warnings)
    _validate_form(doc, "baseline_form", errors, warnings)

    base = doc.get("baseline_form") or {}
    if base.get("filing_status") and base["filing_status"] not in OF_RECORD:
        warnings.append(
            f"baseline_form.filing_status is {base['filing_status']!r} (not filed/approved) — "
            "this is NOT a filed-form deviation check; label the comparison accordingly")

    if not doc.get("required_clause_types"):
        warnings.append("no 'required_clause_types' — missing-required-clause (gap) check will be skipped")
    if not doc.get("config"):
        warnings.append("no 'config' block — default materiality thresholds used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "comparison_example.json"
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
