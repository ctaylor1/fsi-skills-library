#!/usr/bin/env python3
"""Deterministic input validation for ai-incident-investigator.

Validates an AI-incident bundle before investigation. Fails closed on structural problems;
warns on evidence gaps that force a `needs-evidence` disposition (never guess to fill them).

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, incidents[
    {incident_id, detected_at, incident_class, root_cause_hypothesis_category,
     model_or_agent{ref, name, version, owner}, related_incidents[],
     affected{population, financial_exposure, customer_facing, regulated_decision_affected,
              data_classification, reversible, detection_latency_days},
     events[{ts, description, source_ref}], source_ref}]

Usage: python validate_input.py incidents.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "incidents")
REQUIRED_INCIDENT = ("incident_id", "detected_at", "incident_class", "source_ref")
KNOWN_CLASSES = {"harmful", "incorrect", "unauthorized", "biased", "privacy", "security", "resilience"}
KNOWN_DATA_CLASS = {"Restricted", "Highly Confidential", "Confidential", "Internal", "Public"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    incidents = doc.get("incidents") or []
    if not isinstance(incidents, list) or not incidents:
        errors.append("incidents must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, a in enumerate(incidents):
        tag = f"incidents[{i}] ({a.get('incident_id','?')})"
        for k in REQUIRED_INCIDENT:
            if k not in a or a[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        iid = a.get("incident_id")
        if iid in ids:
            errors.append(f"{tag}: duplicate incident_id")
        ids.add(iid)

        mdl = a.get("model_or_agent") or {}
        if not mdl.get("ref"):
            errors.append(f"{tag}: model_or_agent.ref is required (which model/agent is implicated)")

        cls = a.get("incident_class")
        if cls and cls not in KNOWN_CLASSES:
            warnings.append(f"{tag}: unknown incident_class {cls!r} -> scored at base 0; confirm taxonomy")

        events = a.get("events")
        if not events:
            warnings.append(f"{tag}: no events -> chronology incomplete (needs-evidence)")
        else:
            for j, e in enumerate(events):
                if not e.get("source_ref"):
                    warnings.append(f"{tag}: events[{j}] missing source_ref -> chronology entry will be uncited")
                if not e.get("ts"):
                    warnings.append(f"{tag}: events[{j}] missing ts -> cannot order chronology")

        aff = a.get("affected")
        if aff is None:
            warnings.append(f"{tag}: no affected block -> impact unknown (needs-evidence)")
        else:
            dc = aff.get("data_classification")
            if dc and dc not in KNOWN_DATA_CLASS:
                warnings.append(f"{tag}: unknown data_classification {dc!r}")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "incidents_example.json"
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
