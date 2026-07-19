#!/usr/bin/env python3
"""Deterministic input validation for operational-risk-event-analyzer.

Validates an operational-risk event record before analysis. Fails closed on structural
problems; warns on data-quality gaps that limit which parts of the analysis are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  event_id, as_of (YYYY-MM-DD), config_version, currency, event_source_ref,
  is_near_miss, reported_event_type, reported_business_line, occurrence_date,
  discovery_date, description, customer_harm, affected_customers, third_party_involved,
  financials{gross_loss, recoveries[{amount,type,source_ref}], indirect_costs, potential_loss},
  causes[{cause_code, description, source_ref}], config{...thresholds...}

Usage:
  python validate_input.py event.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("event_id", "as_of", "config_version", "currency", "event_source_ref",
                "reported_event_type", "financials", "causes")
BASEL_L1 = {
    "Internal Fraud", "External Fraud", "Employment Practices and Workplace Safety",
    "Clients, Products & Business Practices", "Damage to Physical Assets",
    "Business Disruption and System Failures", "Execution, Delivery & Process Management",
}
BASEL_BUSINESS_LINES = {
    "Corporate Finance", "Trading & Sales", "Retail Banking", "Commercial Banking",
    "Payment & Settlement", "Agency Services", "Asset Management", "Retail Brokerage",
}
KNOWN_CAUSE_CODES = {
    "PEOPLE-ERR", "PEOPLE-SKILL", "PEOPLE-CONDUCT", "PROC-DESIGN", "PROC-BREAK",
    "PROC-DOC", "SYS-FAIL", "SYS-CONFIG", "SYS-CAPACITY", "EXT-VENDOR", "EXT-FRAUD",
    "EXT-EVENT",
}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if not str(doc.get("event_source_ref", "")).strip():
        errors.append("event_source_ref must be a non-empty citation to the loss-event record")

    if str(doc.get("reported_event_type", "")).strip() not in BASEL_L1:
        warnings.append(f"reported_event_type {doc.get('reported_event_type')!r} is not a Basel L1 type — classification not evaluable")
    bl = str(doc.get("reported_business_line", "")).strip()
    if bl and bl not in BASEL_BUSINESS_LINES:
        warnings.append(f"reported_business_line {bl!r} is not a Basel business line — business-line mapping not evaluable")

    fin = doc.get("financials")
    if not isinstance(fin, dict):
        errors.append("financials must be an object")
        return errors, warnings

    is_near_miss = bool(doc.get("is_near_miss"))
    if not is_near_miss:
        if _num(fin.get("gross_loss")) is None:
            errors.append("financials.gross_loss must be numeric for a realized loss event")
    else:
        if _num(fin.get("gross_loss")) not in (None, 0.0):
            warnings.append("event marked near-miss but gross_loss is non-zero — gross_loss will be ignored for banding")
        if fin.get("potential_loss") is None:
            warnings.append("near-miss without financials.potential_loss — severity will rest on escalators only")

    recoveries = fin.get("recoveries") or []
    if not isinstance(recoveries, list):
        errors.append("financials.recoveries must be a list")
    else:
        for i, r in enumerate(recoveries):
            if _num(r.get("amount")) is None:
                errors.append(f"financials.recoveries[{i}]: amount not numeric")
            if not str(r.get("source_ref", "")).strip():
                warnings.append(f"financials.recoveries[{i}]: no source_ref — recovery not independently citable")
    if fin.get("indirect_costs") is not None and _num(fin.get("indirect_costs")) is None:
        errors.append("financials.indirect_costs, if present, must be numeric")

    causes = doc.get("causes")
    if not isinstance(causes, list) or not causes:
        errors.append("causes must be a non-empty list")
        return errors, warnings
    for i, c in enumerate(causes):
        tag = f"causes[{i}] ({c.get('cause_code','?')})"
        if not str(c.get("cause_code", "")).strip():
            errors.append(f"{tag}: missing cause_code")
        elif str(c.get("cause_code")).strip() not in KNOWN_CAUSE_CODES:
            warnings.append(f"{tag}: unknown cause_code — will be reported not_evaluable")
        if not str(c.get("source_ref", "")).strip():
            warnings.append(f"{tag}: no source_ref — its control finding will be uncitable and fail output validation")
        if not str(c.get("description", "")).strip():
            warnings.append(f"{tag}: no description")

    if doc.get("customer_harm") and doc.get("affected_customers") is None:
        warnings.append("customer_harm is true but affected_customers is missing — board-notify escalator may under-flag")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "event_example.json"
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
