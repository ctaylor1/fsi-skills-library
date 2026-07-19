#!/usr/bin/env python3
"""Deterministic input validation for policy-procedure-gap-analyzer.

Validates a gap-analysis pack before mapping and finding computation. Fails closed on
structural problems; warns on data-quality gaps that limit which findings are evaluable.

Input schema (JSON): see references/source-map.md. Key fields:
  framework, jurisdiction, as_of (YYYY-MM-DD), config_version, config{review_max_days},
  requirements[{req_id, source, citation, obligation, criticality(mandatory|guidance),
                applicable, effective_date(YYYY-MM-DD), version, evidence_expected,
                parameter{kind,value}}],
  policy_controls[{control_id, doc, section, maps_to[req_ids], status(active|retired),
                   last_reviewed(YYYY-MM-DD), references_version, evidence_ref,
                   parameter{kind,value}}]

Usage:
  python validate_input.py analysis.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("framework", "as_of", "config_version", "requirements", "policy_controls")
REQUIRED_REQ = ("req_id", "citation", "obligation", "criticality", "effective_date")
REQUIRED_CTRL = ("control_id", "doc", "section", "maps_to", "status")
CRITICALITY = {"mandatory", "guidance"}
STATUS = {"active", "retired"}


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
        errors.append(f"as_of must be YYYY-MM-DD, got {doc['as_of']!r}")

    reqs = doc.get("requirements") or []
    ctrls = doc.get("policy_controls") or []
    if not isinstance(reqs, list) or not reqs:
        errors.append("requirements must be a non-empty list")
    if not isinstance(ctrls, list):
        errors.append("policy_controls must be a list")
    if errors:
        return errors, warnings

    req_ids = set()
    for i, r in enumerate(reqs):
        tag = f"requirements[{i}] ({r.get('req_id', '?')})"
        for k in REQUIRED_REQ:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if r.get("criticality") not in CRITICALITY:
            errors.append(f"{tag}: criticality must be one of {sorted(CRITICALITY)}")
        if r.get("effective_date") and not DATE_RE.match(str(r["effective_date"])):
            errors.append(f"{tag}: effective_date must be YYYY-MM-DD")
        rid = r.get("req_id")
        if rid in req_ids:
            errors.append(f"{tag}: duplicate req_id")
        req_ids.add(rid)
        p = r.get("parameter")
        if p is not None:
            if not isinstance(p, dict) or "kind" not in p or _num(p.get("value")) is None:
                errors.append(f"{tag}: parameter must be {{kind, numeric value}}")
        if r.get("evidence_expected") is None:
            warnings.append(f"{tag}: no evidence_expected flag — evidence_gap not evaluated for this requirement")

    ctrl_ids = set()
    for i, c in enumerate(ctrls):
        tag = f"policy_controls[{i}] ({c.get('control_id', '?')})"
        for k in REQUIRED_CTRL:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if c.get("status") not in STATUS:
            errors.append(f"{tag}: status must be one of {sorted(STATUS)}")
        if not isinstance(c.get("maps_to"), list) or not c.get("maps_to"):
            errors.append(f"{tag}: maps_to must be a non-empty list")
        else:
            for m in c["maps_to"]:
                if m not in req_ids:
                    warnings.append(f"{tag}: maps_to references unknown req_id {m!r} — mapping ignored")
        cid = c.get("control_id")
        if cid in ctrl_ids:
            errors.append(f"{tag}: duplicate control_id")
        ctrl_ids.add(cid)
        if c.get("last_reviewed") and not DATE_RE.match(str(c["last_reviewed"])):
            errors.append(f"{tag}: last_reviewed must be YYYY-MM-DD")
        if c.get("status") == "active" and not c.get("last_reviewed"):
            warnings.append(f"{tag}: active control without last_reviewed — stale_review not evaluable")
        p = c.get("parameter")
        if p is not None and (not isinstance(p, dict) or "kind" not in p or _num(p.get("value")) is None):
            errors.append(f"{tag}: parameter must be {{kind, numeric value}}")

    covered = set()
    for c in ctrls:
        if c.get("status") == "active":
            covered.update(c.get("maps_to") or [])
    uncovered = sorted(req_ids - covered)
    if uncovered:
        warnings.append(f"{len(uncovered)} requirement(s) have no active mapped control — "
                        f"coverage gaps expected: {', '.join(uncovered)}")
    if not doc.get("config"):
        warnings.append("no 'config' block — default review_max_days will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "analysis_example.json"
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
