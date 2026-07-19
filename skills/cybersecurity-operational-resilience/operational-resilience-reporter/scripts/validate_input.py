#!/usr/bin/env python3
"""Deterministic input validation for operational-resilience-reporter.

Validates a resilience dataset before a report is drafted. Fails closed on structural
problems (missing request, unknown report_type/jurisdiction, malformed registers); warns on
data gaps (missing impact tolerances, unresolved service/third-party identity, incidents or
tests that reference an unknown service) that will surface as report `gap` sections or a
`needs-human-input` note rather than being silently drafted over.

Input schema (JSON): see references/source-map.md. Key fields:
  report_request{report_type, jurisdiction, template_version, as_of_date, reporting_period},
  ruleset_version, critical_services[], third_parties[], dependencies[], incidents[],
  tests[], approvals[]

Usage: python validate_input.py resilience_dataset.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("report_request", "ruleset_version", "critical_services")
REPORT_TYPES = {"incident", "impact-tolerance", "dependency", "testing", "self-assessment"}
JURISDICTIONS = {"UK-PRA-SS1-21", "EU-DORA", "US-INTERAGENCY"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    rr = doc.get("report_request") or {}
    if rr.get("report_type") not in REPORT_TYPES:
        errors.append(f"report_request.report_type must be one of {sorted(REPORT_TYPES)}")
    if rr.get("jurisdiction") not in JURISDICTIONS:
        errors.append(f"report_request.jurisdiction must be one of {sorted(JURISDICTIONS)}")
    if not rr.get("as_of_date"):
        errors.append("report_request.as_of_date is required")

    services = doc.get("critical_services")
    if not isinstance(services, list) or not services:
        errors.append("critical_services must be a non-empty list")
        return errors, warnings

    svc_ids = set()
    for i, s in enumerate(services):
        tag = f"critical_services[{i}] ({s.get('service_id', '?')})"
        if not s.get("service_id") or not s.get("name"):
            errors.append(f"{tag}: missing service_id/name")
        if s.get("service_id") in svc_ids:
            errors.append(f"{tag}: duplicate service_id")
        svc_ids.add(s.get("service_id"))
        if s.get("is_important_business_service") and not (s.get("impact_tolerance") or {}).get("threshold"):
            warnings.append(f"{tag}: important business service missing impact_tolerance.threshold -> gap")

    for i, t in enumerate(doc.get("third_parties") or []):
        tag = f"third_parties[{i}] ({t.get('tp_id', '?')})"
        if not t.get("tp_id") or not t.get("name"):
            errors.append(f"{tag}: missing tp_id/name")
        if t.get("is_critical") and not t.get("exit_plan_ref"):
            warnings.append(f"{tag}: critical third party missing exit_plan_ref -> gap")

    for i, d in enumerate(doc.get("dependencies") or []):
        if d.get("service_id") not in svc_ids:
            warnings.append(f"dependencies[{i}]: references unknown service_id {d.get('service_id')!r} -> needs-human-input")

    for i, inc in enumerate(doc.get("incidents") or []):
        if inc.get("service_id") not in svc_ids:
            warnings.append(f"incidents[{i}] ({inc.get('incident_id', '?')}): unknown service_id "
                            f"{inc.get('service_id')!r} -> identity unresolved")
    for i, t in enumerate(doc.get("tests") or []):
        if t.get("service_id") not in svc_ids:
            warnings.append(f"tests[{i}] ({t.get('test_id', '?')}): unknown service_id "
                            f"{t.get('service_id')!r} -> identity unresolved")

    roles = {a.get("role") for a in (doc.get("approvals") or [])}
    for role in ("accountable-executive", "second-line-review"):
        if role not in roles:
            warnings.append(f"no recorded approval for required role '{role}' -> output will fail closed until adjudicated")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "resilience_dataset.json"
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
