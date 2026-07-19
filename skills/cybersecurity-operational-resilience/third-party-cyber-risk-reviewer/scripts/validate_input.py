#!/usr/bin/env python3
"""Deterministic input validation for third-party-cyber-risk-reviewer.

Validates a supplier assessment intake before findings computation. Fails closed on
structural problems; warns on data-quality gaps that limit which findings are evaluable or
that keep a residual-tier suggestion low-confidence.

Input schema (JSON): see references/source-map.md. Key fields:
  assessment_id, supplier_ref, as_of (YYYY-MM-DD), config_version,
  engagement{data_classification, criticality, hosts_regulated_data, ...},
  controls[{control_id, domain, status, evidence_ref, evidence_date}],
  certifications[{type, valid_until, scope_covers_service, evidence_ref}],
  incidents[{incident_id, severity, occurred, disclosed, resolved, affected_our_data}],
  vulnerabilities{critical_open, high_open, sla_breaches, oldest_open_days},
  subcontractors[{name, processes_our_data, region, evidence_ref}],
  contract{...}, resilience{...}, remediation[{...}], config{...thresholds...}

Usage:
  python validate_input.py assessment.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("assessment_id", "supplier_ref", "as_of", "config_version", "engagement")
CONTROL_STATUS = {"implemented", "partial", "missing", "not_applicable", "unknown"}
CRITICALITY = {"critical", "important", "standard"}
SEVERITY = {"low", "medium", "high", "critical"}
CLASSIFICATION = {"Public", "Confidential", "Highly Confidential", "Restricted"}


def _isdate(v) -> bool:
    return bool(DATE_RE.match(str(v)))


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _isdate(doc["as_of"]):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    eng = doc.get("engagement")
    if not isinstance(eng, dict):
        errors.append("engagement must be an object")
    else:
        if eng.get("criticality") not in CRITICALITY:
            errors.append(f"engagement.criticality must be one of {sorted(CRITICALITY)}")
        dc = eng.get("data_classification")
        if not dc:
            errors.append("engagement.data_classification is required")
        elif dc not in CLASSIFICATION:
            warnings.append(f"engagement.data_classification {dc!r} not a standard value — mapping may be off")

    # at least one evidence section must be present to review anything
    sections = ("controls", "certifications", "incidents", "vulnerabilities",
                "subcontractors", "contract", "resilience", "remediation")
    if not any(doc.get(s) for s in sections):
        errors.append("no evidence sections supplied — nothing to review")

    controls = doc.get("controls") or []
    if controls and not isinstance(controls, list):
        errors.append("controls must be a list")
    else:
        ids = set()
        for i, c in enumerate(controls):
            tag = f"controls[{i}] ({c.get('control_id', '?')})"
            for k in ("control_id", "domain", "status"):
                if not c.get(k):
                    errors.append(f"{tag}: missing '{k}'")
            if c.get("status") and c["status"] not in CONTROL_STATUS:
                errors.append(f"{tag}: status must be one of {sorted(CONTROL_STATUS)}")
            if c.get("status") == "unknown":
                warnings.append(f"{tag}: status unknown — not evaluable, will be flagged as an evidence gap")
            cid = c.get("control_id")
            if cid in ids:
                errors.append(f"{tag}: duplicate control_id")
            ids.add(cid)

    for i, c in enumerate(doc.get("certifications") or []):
        tag = f"certifications[{i}] ({c.get('type', '?')})"
        if not c.get("type"):
            errors.append(f"{tag}: missing 'type'")
        if c.get("valid_until") and not _isdate(c["valid_until"]):
            errors.append(f"{tag}: valid_until must be YYYY-MM-DD")
    if not (doc.get("certifications")):
        warnings.append("no certifications supplied — attestation coverage will read as missing")

    for i, inc in enumerate(doc.get("incidents") or []):
        tag = f"incidents[{i}] ({inc.get('incident_id', '?')})"
        if inc.get("severity") and inc["severity"] not in SEVERITY:
            errors.append(f"{tag}: severity must be one of {sorted(SEVERITY)}")
        if "affected_our_data" in inc and not isinstance(inc["affected_our_data"], bool):
            errors.append(f"{tag}: affected_our_data must be boolean")
        for d in ("occurred", "disclosed"):
            if inc.get(d) and not _isdate(inc[d]):
                errors.append(f"{tag}: {d} must be YYYY-MM-DD")

    v = doc.get("vulnerabilities")
    if v is not None:
        if not isinstance(v, dict):
            errors.append("vulnerabilities must be an object of counts")
        else:
            for k in ("critical_open", "high_open", "sla_breaches", "oldest_open_days"):
                if k in v and not isinstance(v[k], (int, float)):
                    errors.append(f"vulnerabilities.{k} must be numeric")

    for i, s in enumerate(doc.get("subcontractors") or []):
        tag = f"subcontractors[{i}] ({s.get('name', '?')})"
        if s.get("processes_our_data") and not s.get("evidence_ref"):
            warnings.append(f"{tag}: processes our data but no evidence_ref — will read as exposure")

    if "contract" not in doc:
        warnings.append("no contract block — contractual_gap not evaluable")
    if "resilience" not in doc:
        warnings.append("no resilience block — resilience_gap not evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_example.json"
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
