#!/usr/bin/env python3
"""Deterministic input validation for contract-obligation-extractor.

Validates a contract intake bundle before the obligation register is built. Fails closed on
structural problems; warns on data gaps that will surface as open items (extractions with no
resolvable source clause, taxonomy categories with no extraction, missing required reviews).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, register_id, as_of_date, template_version,
  contract{contract_id, title, counterparty, contract_type, effective_date, term_end,
           governing_law, source_ref},
  taxonomy[],                       # required obligation categories to cover (versioned)
  clauses[{clause_id, heading, text, source_ref}],
  extractions[{extraction_id, category, clause_ref, summary, responsible_party, due,
               terms{}}],
  required_reviews[], reviews[{review_id, type, reviewer_role, reviewer, status, date,
                               source_ref}]

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "register_id", "contract", "clauses", "taxonomy", "as_of_date")
REQUIRED_CLAUSE = ("clause_id", "source_ref")
REQUIRED_EXTRACTION = ("extraction_id", "category", "summary")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    contract = doc.get("contract") or {}
    if not contract.get("contract_id") or not contract.get("title"):
        errors.append("contract requires 'contract_id' and 'title'")
    if not contract.get("source_ref"):
        warnings.append("contract has no source_ref -> profile citation limited")

    taxonomy = doc.get("taxonomy")
    if not isinstance(taxonomy, list) or not taxonomy:
        errors.append("taxonomy must be a non-empty list of obligation categories")
        return errors, warnings

    clauses = doc.get("clauses")
    if not isinstance(clauses, list) or not clauses:
        errors.append("clauses must be a non-empty list")
        return errors, warnings

    clause_ids = set()
    for i, c in enumerate(clauses):
        tag = f"clauses[{i}] ({c.get('clause_id','?')})"
        for k in REQUIRED_CLAUSE:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cid = c.get("clause_id")
        if cid in clause_ids:
            errors.append(f"{tag}: duplicate clause_id")
        clause_ids.add(cid)
        if not c.get("text"):
            warnings.append(f"{tag}: no clause text -> extractions from this clause cannot be re-verified")

    extractions = doc.get("extractions")
    if extractions is None:
        warnings.append("no extractions provided -> register will be all coverage gaps")
        extractions = []
    elif not isinstance(extractions, list):
        errors.append("extractions must be a list")
        return errors, warnings

    ex_ids = set()
    covered = set()
    for i, e in enumerate(extractions):
        tag = f"extractions[{i}] ({e.get('extraction_id','?')})"
        for k in REQUIRED_EXTRACTION:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        eid = e.get("extraction_id")
        if eid in ex_ids:
            errors.append(f"{tag}: duplicate extraction_id")
        ex_ids.add(eid)
        cat = e.get("category")
        if cat and cat not in taxonomy:
            warnings.append(f"{tag}: category '{cat}' is not in the taxonomy -> will not map to a register section")
        covered.add(cat)
        ref = e.get("clause_ref")
        if not ref and not e.get("citation"):
            warnings.append(f"{tag}: no clause_ref/citation -> will be flagged unsourced (needs-source), never asserted")
        elif ref and ref not in clause_ids:
            warnings.append(f"{tag}: clause_ref '{ref}' does not resolve to a supplied clause -> unsourced (needs-source)")

    for cat in taxonomy:
        if cat not in covered:
            warnings.append(f"taxonomy category '{cat}' has no extraction -> coverage-gap open item (confirm, do not assume silence)")

    for i, r in enumerate(doc.get("reviews") or []):
        if not r.get("type") or not r.get("status"):
            errors.append(f"reviews[{i}]: requires 'type' and 'status'")
        if r.get("status") == "recorded" and not r.get("source_ref"):
            errors.append(f"reviews[{i}] ({r.get('type','?')}): recorded review missing 'source_ref'")

    if not doc.get("required_reviews"):
        warnings.append("no required_reviews configured -> human review capture limited")
    if doc.get("reviews") is None:
        warnings.append("no reviews provided -> all required reviews will be outstanding")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "register_intake_example.json"
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
