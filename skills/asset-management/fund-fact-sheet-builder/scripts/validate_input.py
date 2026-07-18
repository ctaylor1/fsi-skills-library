#!/usr/bin/env python3
"""Deterministic input validation for fund-fact-sheet-builder.

Validates a fund fact-sheet intake bundle before assembly. Fails closed on structural
problems; warns on data gaps that will surface as open items (unsourced figures, undated
figures, figures that cannot be reconciled to source, MNPI/embargoed facts in an external
fact sheet, required sections with no fact, uncited or missing required disclosures).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, factsheet_id, as_of_date, intended_distribution ('internal'|'external'),
  template_version, required_sections[], required_approvals[], required_disclosures[],
  fund{fund_id, legal_name, share_class, isin, ticker, currency, inception_date,
       benchmark_name, objective},
  facts[{section, fact_id, label, value, value_numeric, source_value_numeric,
         reconcile_tolerance, source_ref, effective_date, expires, mnpi, basis, fund_id}],
  disclosures[{disclosure_id, text, source_ref}],
  approvals[{approval_id, type, approver_role, approver, status, date, source_ref}]

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "factsheet_id", "fund", "as_of_date",
                "required_sections", "facts")
REQUIRED_FACT = ("section", "fact_id")
CONTENT_SECTIONS = {"performance", "holdings", "risk", "fees", "esg"}
DISTRIBUTION = {"internal", "external"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    fund = doc.get("fund") or {}
    if not fund.get("fund_id") or not fund.get("legal_name"):
        errors.append("fund requires 'fund_id' and 'legal_name'")

    dist = doc.get("intended_distribution")
    if dist is None:
        warnings.append("no intended_distribution -> defaults to 'internal' (MNPI screen relaxed)")
    elif dist not in DISTRIBUTION:
        errors.append(f"intended_distribution must be one of {sorted(DISTRIBUTION)}, got {dist!r}")
    external = dist == "external"

    req = doc.get("required_sections")
    if not isinstance(req, list) or not req:
        errors.append("required_sections must be a non-empty list")
        return errors, warnings
    for s in req:
        if s not in CONTENT_SECTIONS:
            warnings.append(f"required section '{s}' is not a known content section {sorted(CONTENT_SECTIONS)}")

    facts = doc.get("facts")
    if not isinstance(facts, list):
        errors.append("facts must be a list")
        return errors, warnings

    fact_ids = set()
    provided_sections = set()
    for i, f in enumerate(facts):
        tag = f"facts[{i}] ({f.get('fact_id','?')})"
        for k in REQUIRED_FACT:
            if k not in f or f[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        fid = f.get("fact_id")
        if fid in fact_ids:
            errors.append(f"{tag}: duplicate fact_id")
        fact_ids.add(fid)
        sec = f.get("section")
        if sec and sec not in CONTENT_SECTIONS:
            errors.append(f"{tag}: unknown section {sec!r} (allowed: {sorted(CONTENT_SECTIONS)})")
        provided_sections.add(sec)
        if not f.get("source_ref"):
            warnings.append(f"{tag}: no source_ref -> unsupported open item (not asserted)")
        if not f.get("effective_date"):
            warnings.append(f"{tag}: no effective_date -> freshness cannot be evaluated (review)")
        has_v = f.get("value_numeric") is not None
        has_sv = f.get("source_value_numeric") is not None
        if has_v != has_sv:
            warnings.append(f"{tag}: value_numeric/source_value_numeric not both present -> "
                            f"figure cannot be reconciled to source (review)")
        if f.get("mnpi") and external:
            warnings.append(f"{tag}: MNPI/embargoed fact will be EXCLUDED from an external fact sheet (needs clearance)")

    for s in req:
        if s not in provided_sections:
            warnings.append(f"required section '{s}' has no fact -> section-incomplete open item")

    provided_disclosures = {d.get("disclosure_id") for d in (doc.get("disclosures") or [])}
    for i, d in enumerate(doc.get("disclosures") or []):
        if not d.get("disclosure_id"):
            errors.append(f"disclosures[{i}]: missing 'disclosure_id'")
        if not d.get("source_ref"):
            warnings.append(f"disclosures[{i}] ({d.get('disclosure_id','?')}): no source_ref -> "
                            f"uncited disclosure (unsupported, not rendered as satisfied)")
    for did in doc.get("required_disclosures") or []:
        if did not in provided_disclosures:
            warnings.append(f"required disclosure '{did}' not provided -> disclosure-outstanding open item")

    for i, a in enumerate(doc.get("approvals") or []):
        if not a.get("type") or not a.get("status"):
            errors.append(f"approvals[{i}]: requires 'type' and 'status'")
        if a.get("status") == "recorded" and not a.get("source_ref"):
            errors.append(f"approvals[{i}] ({a.get('type','?')}): recorded approval missing 'source_ref'")

    if not doc.get("required_approvals"):
        warnings.append("no required_approvals configured -> approval capture limited")
    if doc.get("approvals") is None:
        warnings.append("no approvals provided -> all required approvals will be outstanding")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "factsheet_intake_example.json"
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
