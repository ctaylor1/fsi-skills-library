#!/usr/bin/env python3
"""Deterministic input validation for enhanced-due-diligence-packager.

Validates an EDD case-intake file before a package is assembled. Fails closed on
structural problems; warns on evidence gaps that force a `needs-evidence` package (never a
guess). Stdlib-only, self-contained, operates on a documented JSON schema — no live calls.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, template_version, jurisdiction, case_id,
  customer{customer_id, type, risk_rating_of_record, edd_trigger[], customer_ref},
  required_approvals[], recorded_approvals[{role, approver, date}],
  risk_factors{pep_status, sanctions_true_match, high_risk_geography_nexus[],
    adverse_media_severity, ownership_opacity, cash_intensive, product_channel_risk,
    sof_sow_inconsistency},
  evidence{<section>: {present, items[], citations[], gaps[]}}

Usage: python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "case_id", "customer", "evidence", "required_approvals")
REQUIRED_CUSTOMER = ("customer_id", "type", "risk_rating_of_record", "edd_trigger")
# The nine evidence sections an EDD package must marshal. A missing/gap section does not
# fail validation; it forces a `needs-evidence` package downstream.
REQUIRED_EVIDENCE = (
    "customer_overview", "source_of_funds", "source_of_wealth", "ownership_control",
    "geography_exposure", "adverse_media", "pep_sanctions_screening", "expected_activity",
    "ongoing_monitoring_controls",
)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    cust = doc.get("customer") or {}
    if not isinstance(cust, dict):
        errors.append("customer must be an object")
    else:
        for k in REQUIRED_CUSTOMER:
            if k not in cust or cust[k] in (None, "", []):
                errors.append(f"customer: missing '{k}'")
        if cust.get("edd_trigger") and not isinstance(cust["edd_trigger"], list):
            errors.append("customer.edd_trigger must be a list")

    req_appr = doc.get("required_approvals")
    if not isinstance(req_appr, list) or not req_appr:
        errors.append("required_approvals must be a non-empty list of approver roles")

    ev = doc.get("evidence")
    if not isinstance(ev, dict):
        errors.append("evidence must be an object of sections")
        return errors, warnings

    for sec in REQUIRED_EVIDENCE:
        s = ev.get(sec)
        if s is None:
            warnings.append(f"evidence.{sec} absent -> package will mark this section a gap (needs-evidence)")
            continue
        if not isinstance(s, dict):
            errors.append(f"evidence.{sec} must be an object")
            continue
        present = bool(s.get("present"))
        has_items = bool(s.get("items"))
        has_cites = bool(s.get("citations"))
        if present and not has_items:
            warnings.append(f"evidence.{sec}: marked present but no items -> gap (needs-evidence)")
        if present and not has_cites:
            warnings.append(f"evidence.{sec}: present items without citations -> unsupported; will be a gap (needs-evidence)")
        if not present:
            warnings.append(f"evidence.{sec}: not present -> gap (needs-evidence)")

    rf = doc.get("risk_factors")
    if rf is None:
        warnings.append("no risk_factors provided -> residual-risk indicator defaults to 0 (Low); confirm before packaging")
    elif not isinstance(rf, dict):
        errors.append("risk_factors must be an object")
    else:
        if rf.get("sanctions_true_match") is True:
            warnings.append("risk_factors.sanctions_true_match is true -> HARD BOUNDARY: package will be blocked and routed to a specialist; no decision is made here")

    if doc.get("recorded_approvals") is None:
        warnings.append("no recorded_approvals -> approval ledger will list all required approvals as pending (expected for a draft)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "edd_case_example.json"
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
