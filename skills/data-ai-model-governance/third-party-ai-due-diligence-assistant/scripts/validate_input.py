#!/usr/bin/env python3
"""Deterministic input validation for third-party-ai-due-diligence-assistant.

Validates a third-party AI due-diligence intake file before a package is drafted. Fails
closed on structural problems (so a package is never assembled from an ill-formed record);
warns on data gaps that force a `needs-data`, `insufficient-evidence`, `stale-evidence`, or
`unsupported-finding` disposition downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  rubric_version, as_of_date, domain_rubric{} (optional override), assessments[
    {engagement_id, provider{name, criticality, use_case, deployment},
     evidence[{item_id, domain, type, ref, as_of}],
     findings[{finding_id, domain, statement, evidence_id, severity}],
     risk_flags[]?}]

Usage: python validate_input.py assessments.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("rubric_version", "assessments")
REQUIRED_ASSESSMENT = ("engagement_id", "provider", "evidence", "findings")
KNOWN_CRITICALITY = {"High", "Medium", "Low"}
KNOWN_DOMAINS = {
    "provider_profile", "model_transparency", "data_governance", "subcontractors_fourth_party",
    "concentration_risk", "security_controls", "testing_evaluation", "contractual_rights",
    "resilience_continuity", "exit_strategy",
}
SEVERITIES = {"low", "medium", "high", "critical"}


def _is_iso_date(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except Exception:
        return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if doc.get("as_of_date") and not _is_iso_date(doc.get("as_of_date")):
        errors.append("as_of_date is not an ISO date (YYYY-MM-DD)")
    if not doc.get("as_of_date"):
        warnings.append("no as_of_date -> freshness computed against the system date")

    assessments = doc.get("assessments") or []
    if not isinstance(assessments, list) or not assessments:
        errors.append("assessments must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, a in enumerate(assessments):
        tag = f"assessments[{i}] ({a.get('engagement_id','?')})"
        for k in REQUIRED_ASSESSMENT:
            if k not in a or a[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        eid = a.get("engagement_id")
        if eid in ids:
            errors.append(f"{tag}: duplicate engagement_id")
        ids.add(eid)

        prov = a.get("provider")
        if not isinstance(prov, dict):
            errors.append(f"{tag}: provider must be an object")
            prov = {}
        for k in ("name", "criticality", "use_case", "deployment"):
            if prov.get(k) in (None, ""):
                errors.append(f"{tag}: provider missing '{k}'")
        if prov.get("criticality") and prov.get("criticality") not in KNOWN_CRITICALITY:
            warnings.append(f"{tag}: criticality {prov.get('criticality')!r} not classified -> needs-data")

        ev = a.get("evidence")
        if not isinstance(ev, list) or not ev:
            errors.append(f"{tag}: evidence must be a non-empty list")
            ev = []
        item_ids = set()
        for j, e in enumerate(ev):
            if not e.get("item_id") or not e.get("type") or not e.get("domain"):
                errors.append(f"{tag}: evidence[{j}] needs item_id, domain, and type")
            if e.get("domain") and e.get("domain") not in KNOWN_DOMAINS:
                warnings.append(f"{tag}: evidence[{j}] domain {e.get('domain')!r} is not a known due-diligence domain")
            if e.get("as_of") and not _is_iso_date(e.get("as_of")):
                errors.append(f"{tag}: evidence[{j}] as_of is not an ISO date")
            item_ids.add(e.get("item_id"))

        findings = a.get("findings")
        if not isinstance(findings, list):
            errors.append(f"{tag}: findings must be a list")
            findings = []
        for j, f in enumerate(findings):
            if not f.get("finding_id") or not f.get("statement"):
                errors.append(f"{tag}: findings[{j}] needs finding_id and statement")
            if f.get("severity") not in SEVERITIES:
                errors.append(f"{tag}: findings[{j}] severity {f.get('severity')!r} not in {sorted(SEVERITIES)}")
            if f.get("evidence_id") not in item_ids:
                warnings.append(f"{tag}: finding {f.get('finding_id')!r} cites evidence "
                                f"{f.get('evidence_id')!r} not in bundle -> unsupported-finding")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessments_example.json"
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
