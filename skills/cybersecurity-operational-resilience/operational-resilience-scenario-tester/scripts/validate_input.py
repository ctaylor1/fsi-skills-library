#!/usr/bin/env python3
"""Deterministic input validation for operational-resilience-scenario-tester.

Validates a scenario-test package before the deterministic test engine runs. Fails closed
on structural problems; warns on data-quality gaps that limit which checks are evaluable or
that weaken a severe-but-plausible test.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  programme_id, as_of (YYYY-MM-DD), config_version,
  important_business_services[{service_id, name, impact_tolerance{max_downtime_hours,
    max_data_loss_hours}, dependencies{people[],process[],technology[],facilities[],
    third_parties[],data[]}}],
  scenarios[{scenario_id, service_id, title, threat_type, severity, plausibility,
    dimensions_exercised[], observed{time_to_recover_hours, data_loss_hours},
    decisions[{decision_id, description, owner_role, timestamp, evidence_ref}],
    recovery_evidence[{evidence_id, description, source_ref}],
    lessons[{lesson_id, description, severity, remediation_owner_role, evidence_ref}]}],
  config{severity_levels[], plausibility_levels[], min_severity_for_test,
    min_plausibility_for_test, margin_buffer_hours, dependency_dimensions[]}

Usage:
  python validate_input.py package.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("programme_id", "as_of", "config_version",
                "important_business_services", "scenarios")
REQUIRED_IBS = ("service_id", "name", "impact_tolerance")
REQUIRED_SC = ("scenario_id", "service_id", "title", "threat_type",
               "severity", "plausibility", "dimensions_exercised", "observed")


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

    services = doc.get("important_business_services") or []
    if not isinstance(services, list) or not services:
        errors.append("important_business_services must be a non-empty list")
        return errors, warnings

    svc_ids = set()
    for i, s in enumerate(services):
        tag = f"important_business_services[{i}] ({s.get('service_id','?')})"
        for k in REQUIRED_IBS:
            if k not in s or s[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        sid = s.get("service_id")
        if sid in svc_ids:
            errors.append(f"{tag}: duplicate service_id")
        svc_ids.add(sid)
        tol = s.get("impact_tolerance") or {}
        if _num(tol.get("max_downtime_hours")) is None:
            errors.append(f"{tag}: impact_tolerance.max_downtime_hours not numeric")
        deps = s.get("dependencies") or {}
        empty = [d for d in ("people", "process", "technology", "facilities", "third_parties", "data")
                 if not (deps.get(d))]
        if empty:
            warnings.append(f"{tag}: no mapped dependencies for {', '.join(empty)} — coverage of those dimensions is not evaluable")

    scenarios = doc.get("scenarios") or []
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios must be a non-empty list")
        return errors, warnings

    sc_ids = set()
    cfg = doc.get("config") or {}
    sev_levels = cfg.get("severity_levels") or ["moderate", "severe", "extreme"]
    plaus_levels = cfg.get("plausibility_levels") or ["implausible", "plausible", "highly_plausible"]

    for i, sc in enumerate(scenarios):
        tag = f"scenarios[{i}] ({sc.get('scenario_id','?')})"
        for k in REQUIRED_SC:
            if k not in sc or sc[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        scid = sc.get("scenario_id")
        if scid in sc_ids:
            errors.append(f"{tag}: duplicate scenario_id")
        sc_ids.add(scid)
        if sc.get("service_id") not in svc_ids:
            errors.append(f"{tag}: references unknown service_id {sc.get('service_id')!r}")
        if sc.get("severity") and sc["severity"] not in sev_levels:
            errors.append(f"{tag}: severity {sc['severity']!r} not in {sev_levels}")
        if sc.get("plausibility") and sc["plausibility"] not in plaus_levels:
            errors.append(f"{tag}: plausibility {sc['plausibility']!r} not in {plaus_levels}")
        obs = sc.get("observed") or {}
        if _num(obs.get("time_to_recover_hours")) is None:
            warnings.append(f"{tag}: observed.time_to_recover_hours missing — tolerance test is not evaluable for this scenario")
        if not (sc.get("dimensions_exercised")):
            warnings.append(f"{tag}: no dimensions_exercised recorded — coverage cannot be assessed")
        if not (sc.get("decisions")):
            warnings.append(f"{tag}: no response decisions recorded — decision evidence will be incomplete")
        if not (sc.get("recovery_evidence")):
            warnings.append(f"{tag}: no recovery_evidence recorded — recovery cannot be evidenced")

    if not doc.get("config"):
        warnings.append("no 'config' block — default rubric/thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "scenario_pack_example.json"
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
