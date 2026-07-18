#!/usr/bin/env python3
"""Deterministic input validation for pci-dss-evidence-assistant.

Validates a requirements/controls/evidence file before an evidence package is assembled.
Fails closed on structural problems; warns on data gaps that will force a `needs-data`,
`evidence-gap`, or `evidence-stale` outcome downstream.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, assessment{pci_dss_version, as_of_date, prepared_by, ...},
  freshness_windows{type:int}, remediation{req_id:{owner,target_date,severity}},
  controls[{control_id, evidence[{id, type, effective_date, source_ref, in_scope}]}],
  requirements[{req_id, title, control_ids[], not_applicable?, na_justification?}]

Usage: python validate_input.py requirements.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise. Final line ends "N error(s)".
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_TOP = ("config_version", "assessment", "controls", "requirements")
REQUIRED_ASSESSMENT = ("pci_dss_version", "as_of_date", "prepared_by")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    a = doc.get("assessment") or {}
    for k in REQUIRED_ASSESSMENT:
        if not str(a.get(k, "")).strip():
            errors.append(f"assessment: missing '{k}'")
    if a.get("as_of_date") and not DATE_RE.match(str(a.get("as_of_date"))):
        errors.append(f"assessment.as_of_date must be YYYY-MM-DD, got {a.get('as_of_date')!r}")

    fw = doc.get("freshness_windows")
    if fw is not None:
        if not isinstance(fw, dict):
            errors.append("freshness_windows must be an object of {type: int_days}")
        else:
            for t, v in fw.items():
                if not isinstance(v, int) or v <= 0:
                    errors.append(f"freshness_windows['{t}'] must be a positive integer, got {v!r}")

    # Controls + evidence
    controls = doc.get("controls")
    if not isinstance(controls, list) or not controls:
        errors.append("controls must be a non-empty list")
        return errors, warnings
    control_ids = set()
    for i, c in enumerate(controls):
        cid = c.get("control_id")
        tag = f"controls[{i}] ({cid or '?'})"
        if not cid:
            errors.append(f"{tag}: missing control_id")
        elif cid in control_ids:
            errors.append(f"{tag}: duplicate control_id")
        control_ids.add(cid)
        evs = c.get("evidence") or []
        if not evs:
            warnings.append(f"{tag}: no evidence -> mapped requirements will be evidence-gap")
        ev_ids = set()
        for j, ev in enumerate(evs):
            etag = f"{tag}.evidence[{j}] ({ev.get('id','?')})"
            for k in ("id", "type", "source_ref"):
                if not str(ev.get(k, "")).strip():
                    errors.append(f"{etag}: missing '{k}'")
            if ev.get("id") in ev_ids:
                errors.append(f"{etag}: duplicate evidence id within control")
            ev_ids.add(ev.get("id"))
            eff = ev.get("effective_date")
            if not eff:
                warnings.append(f"{etag}: no effective_date -> treated as STALE (cannot assess freshness)")
            elif not DATE_RE.match(str(eff)):
                errors.append(f"{etag}: effective_date must be YYYY-MM-DD, got {eff!r}")

    # Requirements
    reqs = doc.get("requirements")
    if not isinstance(reqs, list) or not reqs:
        errors.append("requirements must be a non-empty list")
        return errors, warnings
    seen = set()
    for i, r in enumerate(reqs):
        rid = r.get("req_id")
        tag = f"requirements[{i}] ({rid or '?'})"
        if not rid:
            errors.append(f"{tag}: missing req_id")
        elif rid in seen:
            errors.append(f"{tag}: duplicate req_id")
        seen.add(rid)
        if not str(r.get("title", "")).strip():
            warnings.append(f"{tag}: missing title")
        cids = r.get("control_ids") or []
        if r.get("not_applicable") and not str(r.get("na_justification", "")).strip():
            warnings.append(f"{tag}: marked N/A without na_justification -> will be needs-data")
        if not r.get("not_applicable") and not cids:
            warnings.append(f"{tag}: no control_ids -> needs-data")
        for cid in cids:
            if cid not in control_ids:
                errors.append(f"{tag}: references unknown control_id {cid!r}")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "requirements_example.json"
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
    print(f"input validation: {len(warnings)} warning(s), {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
